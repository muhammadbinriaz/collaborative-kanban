export const WS_EVENTS = {
  SERVER: "server-broadcast",
  SERVER_VOLATILE: "server-volatile-broadcast",
} as const;

/** Copied from excalidraw-app/app_constants.ts */
export enum WS_SUBTYPES {
  INVALID_RESPONSE = "INVALID_RESPONSE",
  INIT = "SCENE_INIT",
  UPDATE = "SCENE_UPDATE",
  MOUSE_LOCATION = "MOUSE_LOCATION",
  IDLE_STATUS = "IDLE_STATUS",
}

export const INITIAL_SCENE_UPDATE_TIMEOUT = 5000;
export const SYNC_FULL_SCENE_INTERVAL_MS = 20000;
export const CURSOR_SYNC_TIMEOUT = 33;

export type SocketUpdateData = {
  type: WS_SUBTYPES;
  payload: Record<string, unknown>;
};
