"use client";

import dynamic from "next/dynamic";
import { useCallback, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { PresenceAvatars } from "@/components/presence-avatars";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { PresenceUser, Whiteboard } from "@/types";

const ExcalidrawCanvas = dynamic(() => import("@/components/whiteboard/excalidraw-canvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Loading Excalidraw…</div>
  ),
});

export default function WhiteboardPage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ whiteboardId: string }>();
  const whiteboardId = params.whiteboardId;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [presence, setPresence] = useState<PresenceUser[]>([]);
  const [connected, setConnected] = useState(false);

  const board = useQuery({
    queryKey: ["whiteboard", whiteboardId],
    queryFn: () => api<Whiteboard>(`/api/v1/whiteboards/${whiteboardId}`),
    enabled: Boolean(user && whiteboardId),
  });

  const save = useMutation({
    mutationFn: (scene: Record<string, unknown>) =>
      api<Whiteboard>(`/api/v1/whiteboards/${whiteboardId}`, {
        method: "PUT",
        body: JSON.stringify({ scene }),
      }),
    onMutate: () => setSaving(true),
    onSuccess: (data) => {
      queryClient.setQueryData(["whiteboard", whiteboardId], data);
      setSaving(false);
    },
    onError: (error: Error) => {
      setSaving(false);
      toast.error(error.message);
    },
  });

  const remove = useMutation({
    mutationFn: () => api<void>(`/api/v1/whiteboards/${whiteboardId}`, { method: "DELETE" }),
    onSuccess: () => {
      if (board.data) {
        router.push(`/workspaces/${board.data.workspace_id}`);
      }
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const onSave = useCallback(
    (scene: Record<string, unknown>) => {
      save.mutate(scene);
    },
    [save],
  );

  if (!ready || !user || board.isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }

  if (!board.data) {
    return <div className="p-8 text-sm text-muted-foreground">Whiteboard not found.</div>;
  }

  return (
    <div className="relative flex h-screen flex-col overflow-hidden">
      <div className="pointer-events-none fixed left-3 top-3 z-[200]">
        <span
          className={`pointer-events-auto inline-block rounded-full px-4 py-2 text-sm font-bold shadow-lg ${
            connected ? "bg-emerald-500 text-white" : "bg-amber-500 text-black"
          }`}
        >
          {connected ? "LIVE — auto-sync on" : "CONNECTING… live sync is off"}
        </span>
      </div>
      <AppHeader
        title={board.data.name}
        backHref={`/workspaces/${board.data.workspace_id}`}
        backLabel="Workspace"
      />
      <div className="flex items-center justify-between border-b px-4 py-2">
        <span className="text-xs text-muted-foreground">
          {connected ? "LIVE" : "CONNECTING"} · {saving ? "Saving…" : "Saved"}
        </span>
        <div className="flex items-center gap-3">
          <PresenceAvatars users={presence} connected={connected} />
          <Button size="sm" variant="destructive" onClick={() => remove.mutate()} disabled={remove.isPending}>
            Delete
          </Button>
        </div>
      </div>
      <div className="relative min-h-0 flex-1">
        <ExcalidrawCanvas
          whiteboardId={board.data.id}
          initialScene={board.data.scene}
          currentUser={{ id: user.id, name: user.name }}
          saving={saving}
          onSave={onSave}
          onPresence={setPresence}
          onConnection={setConnected}
        />
      </div>
    </div>
  );
}
