"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { Excalidraw, Footer } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";

import { useExcalidrawCollab } from "@/hooks/use-excalidraw-collab";

type Scene = {
  elements?: unknown[];
  appState?: Record<string, unknown>;
  files?: Record<string, unknown>;
};

type ExcalidrawElement = {
  id: string;
  isDeleted?: boolean;
  [key: string]: unknown;
};

function activeCount(elements: ExcalidrawElement[]) {
  return elements.filter((el) => !el.isDeleted).length;
}

export default function ExcalidrawCanvas({
  whiteboardId,
  initialScene,
  currentUser,
  saving,
  onSave,
  onPresence,
  onConnection,
}: {
  whiteboardId: string;
  initialScene: Scene | null;
  currentUser: { id: string; name: string };
  saving?: boolean;
  onSave: (scene: Scene) => void;
  onPresence?: (users: { id: string; name: string; email: string }[]) => void;
  onConnection?: (connected: boolean) => void;
}) {
  const { connected, presence, setApi, syncElements, onPointerUpdate } = useExcalidrawCollab(
    whiteboardId,
    currentUser,
  );
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const canSave = useRef(false);
  const knownActive = useRef(activeCount((initialScene?.elements as ExcalidrawElement[]) || []));
  const onSaveRef = useRef(onSave);
  onSaveRef.current = onSave;

  useEffect(() => {
    onPresence?.(presence);
  }, [presence, onPresence]);

  useEffect(() => {
    onConnection?.(connected);
  }, [connected, onConnection]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      canSave.current = true;
    }, 800);
    return () => window.clearTimeout(timer);
  }, [whiteboardId]);

  const initialData = useMemo(
    () => ({
      elements: (initialScene?.elements ?? []) as never[],
      appState: (initialScene?.appState ?? {}) as never,
      files: (initialScene?.files ?? {}) as never,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [whiteboardId],
  );

  const persist = useCallback((elements: ExcalidrawElement[], appState: Record<string, unknown>, files: Record<string, unknown>) => {
    if (!canSave.current) return;
    const live = activeCount(elements);
    if (live === 0 && knownActive.current > 0 && elements.length === 0) return;
    if (live > 0) knownActive.current = live;
    onSaveRef.current({
      elements,
      appState: {
        viewBackgroundColor: appState.viewBackgroundColor,
        gridSize: appState.gridSize,
        currentItemFontFamily: appState.currentItemFontFamily,
      },
      files,
    });
  }, []);

  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, []);

  const statusLabel = connected ? "LIVE" : "CONNECTING";
  const saveLabel = saving ? "Saving…" : "Saved";

  return (
    <div className="h-full w-full">
      <Excalidraw
        isCollaborating={connected}
        excalidrawAPI={setApi}
        initialData={initialData}
        renderTopRightUI={() => (
          <div
            style={{
              background: connected ? "#059669" : "#d97706",
              color: "#fff",
              fontWeight: 700,
              fontSize: 13,
              padding: "6px 12px",
              borderRadius: 999,
              marginRight: 8,
            }}
          >
            {statusLabel}
          </div>
        )}
        onChange={(elements, appState, files) => {
          const typed = elements as unknown as ExcalidrawElement[];
          syncElements(typed);
          if (!canSave.current) return;
          if (saveTimer.current) clearTimeout(saveTimer.current);
          saveTimer.current = setTimeout(() => {
            persist(typed, appState as unknown as Record<string, unknown>, files as unknown as Record<string, unknown>);
          }, 700);
        }}
        onPointerUpdate={onPointerUpdate}
        UIOptions={{
          canvasActions: {
            loadScene: true,
            export: { saveFileToDisk: true },
          },
        }}
      >
        <Footer>
          <span style={{ fontWeight: 700, color: connected ? "#047857" : "#b45309", marginRight: 8 }}>
            {statusLabel} · {saveLabel}
          </span>
        </Footer>
      </Excalidraw>
    </div>
  );
}
