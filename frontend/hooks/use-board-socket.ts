"use client";

import { useEffect, useRef, useState } from "react";

import { getAccessToken } from "@/lib/api";
import type { PresenceUser } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

type BoardEvent = {
  type: string;
  payload?: unknown;
  users?: PresenceUser[];
  at?: string;
};

export function useBoardSocket(
  boardId: string | undefined,
  onEvent: (event: BoardEvent) => void,
) {
  const [presence, setPresence] = useState<PresenceUser[]>([]);
  const [connected, setConnected] = useState(false);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    if (!boardId) return;
    const token = getAccessToken();
    if (!token) return;

    let closed = false;
    let socket: WebSocket | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let attempt = 0;

    function connect() {
      if (closed) return;
      socket = new WebSocket(`${WS_URL}/ws/boards/${boardId}?token=${encodeURIComponent(token!)}`);

      socket.onopen = () => {
        attempt = 0;
        setConnected(true);
        pingTimer = setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "ping" }));
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as BoardEvent;
          if (data.type === "presence.updated" && data.users) {
            setPresence(data.users);
          }
          handlerRef.current(data);
        } catch {
          /* ignore malformed frames */
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (pingTimer) clearInterval(pingTimer);
        if (closed) return;
        attempt += 1;
        const delay = Math.min(10000, 1000 * 2 ** Math.min(attempt, 4));
        retryTimer = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      closed = true;
      if (pingTimer) clearInterval(pingTimer);
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
    };
  }, [boardId]);

  return { presence, connected };
}
