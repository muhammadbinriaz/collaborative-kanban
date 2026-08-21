"use client";

import {
  CaptureUpdateAction,
  getSceneVersion,
  reconcileElements,
  restoreElements,
} from "@excalidraw/excalidraw";

import {
  INITIAL_SCENE_UPDATE_TIMEOUT,
  SYNC_FULL_SCENE_INTERVAL_MS,
  WS_SUBTYPES,
  type SocketUpdateData,
} from "@/lib/collab/constants";
import { Portal, waitForAccessToken } from "@/lib/collab/portal";

const NEVER = (CaptureUpdateAction?.NEVER ?? "NEVER") as "NEVER";

type OrderedElement = {
  id: string;
  version?: number;
  versionNonce?: number;
  isDeleted?: boolean;
  [key: string]: unknown;
};

type Collaborator = {
  socketId?: string;
  username?: string;
  pointer?: { x: number; y: number; tool: "pointer" | "laser" };
  button?: "up" | "down";
  selectedElementIds?: Record<string, boolean>;
  color?: { background: string; stroke: string };
};

type ExcalidrawApi = {
  getSceneElementsIncludingDeleted: () => OrderedElement[];
  getSceneElements: () => OrderedElement[];
  getAppState: () => Record<string, unknown>;
  updateScene: (scene: {
    elements?: OrderedElement[];
    collaborators?: Map<string, Collaborator>;
    captureUpdate?: "NEVER";
  }) => void;
};

type CollabListeners = {
  onStatus?: (connected: boolean) => void;
  onPresence?: (users: { id: string; name: string; email: string; color?: string }[]) => void;
};

/**
 * Port of excalidraw-app/collab/Collab.tsx (scene sync + cursors only).
 */
export class Collab {
  portal: Portal;
  api: ExcalidrawApi | null = null;
  username = "";
  private lastBroadcastedOrReceivedSceneVersion = -1;
  private collaborators = new Map<string, Collaborator>();
  private listeners: CollabListeners = {};
  private fullSyncTimer: ReturnType<typeof setTimeout> | null = null;
  private initTimer: ReturnType<typeof setTimeout> | null = null;
  private startedFor: string | null = null;

  constructor() {
    this.portal = new Portal({
      getSceneElementsIncludingDeleted: () =>
        this.api?.getSceneElementsIncludingDeleted?.() ?? this.api?.getSceneElements() ?? [],
      setCollaborators: (ids) => this.setCollaborators(ids),
      onClientBroadcast: (data) => this.onClientBroadcast(data),
      onFirstInRoom: () => this.initializeRoom(),
      onPresence: (users) => {
        this.listeners.onPresence?.(
          users.map((row) => ({
            id: String(row.id || row.socket_id || ""),
            name: String(row.name || "User"),
            email: String(row.email || ""),
            color: typeof row.color === "string" ? row.color : undefined,
          })),
        );
      },
    });
  }

  setApi(api: ExcalidrawApi) {
    this.api = api;
  }

  setUsername(name: string) {
    this.username = name;
  }

  on(listeners: CollabListeners) {
    this.listeners = listeners;
  }

  async start(roomId: string) {
    if (this.startedFor === roomId && this.portal.socket) return;
    this.stop();
    this.startedFor = roomId;

    const token = await waitForAccessToken();
    if (!token) {
      this.listeners.onStatus?.(false);
      return;
    }

    const socket = this.portal.open(roomId, token);
    socket.on("connect", () => this.listeners.onStatus?.(true));
    socket.on("disconnect", () => this.listeners.onStatus?.(false));
    socket.on("connect_error", () => this.listeners.onStatus?.(false));

    this.initTimer = setTimeout(() => {
      this.initializeRoom();
    }, INITIAL_SCENE_UPDATE_TIMEOUT);
  }

  stop() {
    if (this.initTimer) window.clearTimeout(this.initTimer);
    if (this.fullSyncTimer) window.clearTimeout(this.fullSyncTimer);
    this.portal.close();
    this.lastBroadcastedOrReceivedSceneVersion = -1;
    this.collaborators = new Map();
    this.startedFor = null;
    this.listeners.onStatus?.(false);
  }

  /** Official initializeRoom — marks socket ready to broadcast. */
  initializeRoom() {
    if (this.initTimer) {
      window.clearTimeout(this.initTimer);
      this.initTimer = null;
    }
    this.portal.socketInitialized = true;
    if (this.api) {
      const elements = this.api.getSceneElementsIncludingDeleted?.() ?? this.api.getSceneElements();
      this.lastBroadcastedOrReceivedSceneVersion = getSceneVersion(elements as never);
      void this.portal.broadcastScene(WS_SUBTYPES.UPDATE, elements, true);
    }
  }

  private _reconcileElements(remoteElements: OrderedElement[]) {
    if (!this.api) return remoteElements;
    const appState = this.api.getAppState();
    const existing = this.api.getSceneElementsIncludingDeleted?.() ?? this.api.getSceneElements();
    const restored = restoreElements(remoteElements as never, existing as never);
    const reconciled = reconcileElements(existing as never, restored as never, appState as never) as OrderedElement[];
    // Must run before updateScene — onChange is sync and would echo otherwise.
    this.lastBroadcastedOrReceivedSceneVersion = getSceneVersion(reconciled as never);
    return reconciled;
  }

  private handleRemoteSceneUpdate(elements: OrderedElement[]) {
    this.api?.updateScene({
      elements,
      captureUpdate: NEVER,
    });
  }

  onClientBroadcast(data: SocketUpdateData) {
    switch (data.type) {
      case WS_SUBTYPES.INIT: {
        this.initializeRoom();
        const remote = (data.payload.elements as OrderedElement[]) || [];
        this.handleRemoteSceneUpdate(this._reconcileElements(remote));
        break;
      }
      case WS_SUBTYPES.UPDATE: {
        const remote = (data.payload.elements as OrderedElement[]) || [];
        this.handleRemoteSceneUpdate(this._reconcileElements(remote));
        break;
      }
      case WS_SUBTYPES.MOUSE_LOCATION: {
        const socketId = String(data.payload.socketId || "");
        if (!socketId || !this.api) return;
        const next = new Map(this.collaborators);
        next.set(socketId, {
          socketId,
          username: String(data.payload.username || "Collaborator"),
          pointer: data.payload.pointer as Collaborator["pointer"],
          button: data.payload.button as Collaborator["button"],
          selectedElementIds: data.payload.selectedElementIds as Record<string, boolean>,
          color: { background: "#2563eb", stroke: "#2563eb" },
        });
        this.collaborators = next;
        this.api.updateScene({ collaborators: next, captureUpdate: NEVER });
        break;
      }
      default:
        break;
    }
  }

  setCollaborators(socketIds: string[]) {
    const next = new Map<string, Collaborator>();
    for (const id of socketIds) {
      if (id === this.portal.socket?.id) continue;
      next.set(id, this.collaborators.get(id) || { socketId: id });
    }
    this.collaborators = next;
    this.api?.updateScene({ collaborators: next, captureUpdate: NEVER });
  }

  broadcastElements(elements: readonly OrderedElement[]) {
    if (getSceneVersion(elements as never) > this.lastBroadcastedOrReceivedSceneVersion) {
      void this.portal.broadcastScene(WS_SUBTYPES.UPDATE, elements, false);
      this.lastBroadcastedOrReceivedSceneVersion = getSceneVersion(elements as never);
      this.queueBroadcastAllElements();
    }
  }

  syncElements(elements: readonly OrderedElement[]) {
    this.broadcastElements(elements);
  }

  private queueBroadcastAllElements() {
    if (this.fullSyncTimer) return;
    this.fullSyncTimer = setTimeout(() => {
      this.fullSyncTimer = null;
      if (!this.api) return;
      const all = this.api.getSceneElementsIncludingDeleted?.() ?? this.api.getSceneElements();
      void this.portal.broadcastScene(WS_SUBTYPES.UPDATE, all, true);
      this.lastBroadcastedOrReceivedSceneVersion = Math.max(
        this.lastBroadcastedOrReceivedSceneVersion,
        getSceneVersion(all as never),
      );
    }, SYNC_FULL_SCENE_INTERVAL_MS);
  }

  onPointerUpdate(payload: {
    pointer: { x: number; y: number; tool: string };
    button: "up" | "down";
  }) {
    this.portal.broadcastMouseLocation({
      pointer: payload.pointer,
      button: payload.button,
      selectedElementIds: (this.api?.getAppState()?.selectedElementIds || {}) as Record<string, boolean>,
      username: this.username,
    });
  }
}
