"use client";

import { io, type Socket } from "socket.io-client";

import { getAccessToken } from "@/lib/api";
import {
  WS_EVENTS,
  WS_SUBTYPES,
  type SocketUpdateData,
} from "@/lib/collab/constants";

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type OrderedElement = {
  id: string;
  version?: number;
  isDeleted?: boolean;
  updated?: number;
  [key: string]: unknown;
};

type CollabLike = {
  getSceneElementsIncludingDeleted: () => OrderedElement[];
  setCollaborators: (socketIds: string[]) => void;
  onClientBroadcast: (data: SocketUpdateData) => void;
  onFirstInRoom: () => void;
  onPresence?: (users: Record<string, unknown>[]) => void;
};

function isSyncableElement(element: OrderedElement) {
  if (element.isDeleted) {
    const updated = typeof element.updated === "number" ? element.updated : Date.now();
    return Date.now() - updated < 24 * 60 * 60 * 1000;
  }
  return true;
}

/**
 * Port of excalidraw-app/collab/Portal.tsx
 * Encryption omitted — rooms are JWT-authenticated.
 */
export class Portal {
  collab: CollabLike;
  socket: Socket | null = null;
  socketInitialized = false;
  roomId: string | null = null;
  broadcastedElementVersions = new Map<string, number>();

  constructor(collab: CollabLike) {
    this.collab = collab;
  }

  isOpen() {
    return Boolean(this.socketInitialized && this.socket && this.roomId);
  }

  open(roomId: string, token: string) {
    this.close();
    this.roomId = roomId;

    const socket = io(SOCKET_URL, {
      // Polling first: raw websocket to this host has been unreliable in Docker.
      transports: ["polling", "websocket"],
      auth: { token },
      query: { token },
      withCredentials: false,
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 500,
      reconnectionDelayMax: 4000,
    });
    this.socket = socket;

    socket.on("init-room", () => {
      socket.emit("join-room", this.roomId);
    });

    socket.on("new-user", () => {
      void this.broadcastScene(WS_SUBTYPES.INIT, this.collab.getSceneElementsIncludingDeleted(), true);
    });

    socket.on("room-user-change", (clients: string[]) => {
      this.collab.setCollaborators(clients);
    });

    socket.on("first-in-room", () => {
      this.collab.onFirstInRoom();
    });

    socket.on("client-broadcast", (data: unknown) => {
      try {
        const parsed = (typeof data === "string" ? JSON.parse(data) : data) as SocketUpdateData;
        if (parsed?.type) this.collab.onClientBroadcast(parsed);
      } catch {
        /* ignore */
      }
    });

    socket.on("presence", (users: Record<string, unknown>[]) => {
      this.collab.onPresence?.(users);
    });

    return socket;
  }

  close() {
    this.socket?.removeAllListeners();
    this.socket?.disconnect();
    this.socket = null;
    this.roomId = null;
    this.socketInitialized = false;
    this.broadcastedElementVersions = new Map();
  }

  private emit(data: SocketUpdateData, volatile = false) {
    if (!this.isOpen() || !this.socket || !this.roomId) return;
    this.socket.emit(volatile ? WS_EVENTS.SERVER_VOLATILE : WS_EVENTS.SERVER, this.roomId, JSON.stringify(data));
  }

  async broadcastScene(
    updateType: WS_SUBTYPES.INIT | WS_SUBTYPES.UPDATE,
    elements: readonly OrderedElement[],
    syncAll: boolean,
  ) {
    if (updateType === WS_SUBTYPES.INIT && !syncAll) {
      throw new Error("syncAll must be true when sending SCENE.INIT");
    }

    const syncableElements: OrderedElement[] = [];
    for (const element of elements) {
      const last = this.broadcastedElementVersions.get(element.id);
      if (
        (syncAll || last === undefined || (element.version ?? 0) > last) &&
        isSyncableElement(element)
      ) {
        syncableElements.push(element);
      }
    }

    for (const el of syncableElements) {
      this.broadcastedElementVersions.set(el.id, el.version ?? 0);
    }

    this.emit({
      type: updateType,
      payload: { elements: syncableElements },
    });
  }

  broadcastMouseLocation(payload: {
    pointer: { x: number; y: number; tool: string };
    button: "up" | "down";
    selectedElementIds: Record<string, boolean>;
    username: string;
  }) {
    if (!this.socket?.id) return;
    this.emit(
      {
        type: WS_SUBTYPES.MOUSE_LOCATION,
        payload: {
          socketId: this.socket.id,
          pointer: payload.pointer,
          button: payload.button,
          selectedElementIds: payload.selectedElementIds,
          username: payload.username,
        },
      },
      true,
    );
  }
}

export function waitForAccessToken(timeoutMs = 8000): Promise<string | null> {
  const existing = getAccessToken();
  if (existing) return Promise.resolve(existing);
  return new Promise((resolve) => {
    const started = Date.now();
    const timer = window.setInterval(() => {
      const token = getAccessToken();
      if (token) {
        window.clearInterval(timer);
        resolve(token);
        return;
      }
      if (Date.now() - started > timeoutMs) {
        window.clearInterval(timer);
        resolve(null);
      }
    }, 200);
  });
}
