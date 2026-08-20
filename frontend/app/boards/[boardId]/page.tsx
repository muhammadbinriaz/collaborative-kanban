"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { AppHeader } from "@/components/app-header";
import { BoardView } from "@/components/kanban/board-view";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { BoardDetail } from "@/types";

export default function BoardPage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ boardId: string }>();
  const boardId = params.boardId;

  const board = useQuery({
    queryKey: ["board", boardId],
    queryFn: () => api<BoardDetail>(`/api/v1/boards/${boardId}`),
    enabled: Boolean(user && boardId),
  });

  if (!ready || !user || board.isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading board…</div>;
  }

  if (!board.data) {
    return <div className="p-8 text-sm text-muted-foreground">Board not found.</div>;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader
        title={board.data.name}
        backHref={`/workspaces/${board.data.workspace_id}`}
        backLabel="Boards"
      />
      <BoardView board={board.data} />
    </div>
  );
}
