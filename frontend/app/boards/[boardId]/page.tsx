"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { AiPanel } from "@/components/ai/ai-panel";
import { AnalyticsPanel } from "@/components/analytics/analytics-panel";
import { AppHeader } from "@/components/app-header";
import { BoardView } from "@/components/kanban/board-view";
import { SprintPanel } from "@/components/kanban/sprint-panel";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { BoardDetail } from "@/types";

type Tab = "board" | "sprints" | "analytics" | "ai";

export default function BoardPage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ boardId: string }>();
  const boardId = params.boardId;
  const [tab, setTab] = useState<Tab>("board");
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);

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
    <div className="flex h-screen flex-col overflow-hidden">
      <AppHeader
        title={board.data.name}
        backHref={`/workspaces/${board.data.workspace_id}`}
        backLabel="Boards"
      />
      <div className="flex shrink-0 items-center gap-2 border-b bg-background px-4 py-2">
        {(
          [
            ["board", "Board"],
            ["sprints", "Sprints"],
            ["analytics", "Analytics"],
            ["ai", "AI"],
          ] as const
        ).map(([key, label]) => (
          <Button
            key={key}
            size="sm"
            variant={tab === key ? "default" : "ghost"}
            onClick={() => setTab(key)}
          >
            {key === "ai" ? <Sparkles className="mr-1 h-3.5 w-3.5" /> : null}
            {label}
          </Button>
        ))}
      </div>
      {tab === "board" ? (
        <BoardView board={board.data} onCardSelect={(cardId) => setSelectedCardId(cardId)} />
      ) : null}
      {tab === "sprints" ? (
        <div className="mx-auto w-full max-w-3xl flex-1 overflow-y-auto">
          <SprintPanel board={board.data} />
        </div>
      ) : null}
      {tab === "analytics" ? (
        <div className="mx-auto w-full max-w-5xl flex-1 overflow-y-auto">
          <AnalyticsPanel boardId={board.data.id} />
        </div>
      ) : null}
      {tab === "ai" ? (
        <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto">
          <AiPanel boardId={board.data.id} selectedCardId={selectedCardId} />
        </div>
      ) : null}
    </div>
  );
}
