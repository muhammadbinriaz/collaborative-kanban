"use client";

import { useEffect, useRef, useState } from "react";

import { Collab } from "@/lib/collab/Collab";
import type { PresenceUser } from "@/types";

export function useExcalidrawCollab(
  whiteboardId: string | undefined,
  currentUser: { id: string; name: string } | null,
) {
  const collabRef = useRef<Collab | null>(null);
  if (!collabRef.current) collabRef.current = new Collab();
  const [connected, setConnected] = useState(false);
  const [presence, setPresence] = useState<PresenceUser[]>([]);

  useEffect(() => {
    const collab = collabRef.current!;
    collab.setUsername(currentUser?.name || "");
    collab.on({
      onStatus: setConnected,
      onPresence: (users) => setPresence(users as PresenceUser[]),
    });
    if (whiteboardId && currentUser) {
      void collab.start(whiteboardId);
    }
    return () => collab.stop();
  }, [whiteboardId, currentUser?.id, currentUser?.name]);

  return {
    connected,
    presence,
    setApi: (api: unknown) => collabRef.current?.setApi(api as never),
    syncElements: (elements: readonly unknown[]) =>
      collabRef.current?.syncElements(elements as never),
    onPointerUpdate: (payload: {
      pointer: { x: number; y: number; tool: string };
      button: "up" | "down";
    }) => collabRef.current?.onPointerUpdate(payload),
  };
}
