"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Activity } from "@/types";

export function ActivityFeed({ boardId }: { boardId: string }) {
  const activity = useQuery({
    queryKey: ["activity", boardId],
    queryFn: () => api<Activity[]>(`/api/v1/boards/${boardId}/activity`),
    refetchInterval: 20000,
  });

  return (
    <aside className="hidden w-72 shrink-0 border-l bg-card/40 xl:flex xl:flex-col">
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold">Activity</h2>
        <p className="text-xs text-muted-foreground">Recent board changes</p>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {(activity.data ?? []).map((item) => (
          <div key={item.id} className="space-y-1">
            <p className="text-sm leading-snug">{item.summary}</p>
            <p className="text-[11px] text-muted-foreground">
              {new Date(item.created_at).toLocaleString()}
            </p>
          </div>
        ))}
        {(activity.data ?? []).length === 0 ? (
          <p className="text-xs text-muted-foreground">Moves, comments, and edits show up here.</p>
        ) : null}
      </div>
    </aside>
  );
}
