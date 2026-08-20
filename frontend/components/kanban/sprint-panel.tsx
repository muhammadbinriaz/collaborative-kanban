"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Play, CheckCircle2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { BoardDetail, Sprint } from "@/types";

export function SprintPanel({ board }: { board: BoardDetail }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");

  const sprints = useQuery({
    queryKey: ["sprints", board.id],
    queryFn: () => api<Sprint[]>(`/api/v1/boards/${board.id}/sprints`),
  });

  const create = useMutation({
    mutationFn: () =>
      api<Sprint>(`/api/v1/boards/${board.id}/sprints`, {
        method: "POST",
        body: JSON.stringify({ name, goal: goal || null }),
      }),
    onSuccess: () => {
      setName("");
      setGoal("");
      queryClient.invalidateQueries({ queryKey: ["sprints", board.id] });
      toast.success("Sprint created");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const start = useMutation({
    mutationFn: (id: string) => api<Sprint>(`/api/v1/sprints/${id}/start`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sprints", board.id] });
      queryClient.invalidateQueries({ queryKey: ["analytics", board.id] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const complete = useMutation({
    mutationFn: (id: string) => api<Sprint>(`/api/v1/sprints/${id}/complete`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sprints", board.id] });
      queryClient.invalidateQueries({ queryKey: ["analytics", board.id] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const assignAll = useMutation({
    mutationFn: (sprintId: string) => {
      const cardIds = board.lists.flatMap((list) => list.cards.map((card) => card.id));
      return api<Sprint>(`/api/v1/sprints/${sprintId}/cards`, {
        method: "POST",
        body: JSON.stringify({ card_ids: cardIds }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sprints", board.id] });
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      queryClient.invalidateQueries({ queryKey: ["analytics", board.id] });
      toast.success("Board cards added to sprint");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-4 p-4">
      <div>
        <h2 className="font-serif text-2xl">Sprints</h2>
        <p className="text-sm text-muted-foreground">Plan, start, and complete sprint cycles.</p>
      </div>

      <form
        className="space-y-2 rounded-xl border bg-card p-3"
        onSubmit={(event) => {
          event.preventDefault();
          if (name.trim()) create.mutate();
        }}
      >
        <Input placeholder="Sprint name" value={name} onChange={(event) => setName(event.target.value)} required />
        <Input placeholder="Goal (optional)" value={goal} onChange={(event) => setGoal(event.target.value)} />
        <Button type="submit" size="sm" disabled={create.isPending}>
          <Plus className="h-4 w-4" />
          Create sprint
        </Button>
      </form>

      <div className="space-y-3">
        {(sprints.data ?? []).map((sprint) => (
          <div key={sprint.id} className="rounded-xl border bg-card p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">{sprint.name}</p>
                <p className="text-xs text-muted-foreground">
                  {sprint.status} · {sprint.completed_points}/{sprint.total_points} pts · {sprint.card_count} cards
                </p>
                {sprint.goal ? <p className="mt-1 text-sm text-muted-foreground">{sprint.goal}</p> : null}
              </div>
              <div className="flex flex-col gap-1">
                {sprint.status === "planned" ? (
                  <Button size="sm" variant="secondary" onClick={() => start.mutate(sprint.id)}>
                    <Play className="h-3 w-3" />
                    Start
                  </Button>
                ) : null}
                {sprint.status === "active" ? (
                  <Button size="sm" variant="secondary" onClick={() => complete.mutate(sprint.id)}>
                    <CheckCircle2 className="h-3 w-3" />
                    Complete
                  </Button>
                ) : null}
                {sprint.status !== "completed" ? (
                  <Button size="sm" variant="outline" onClick={() => assignAll.mutate(sprint.id)}>
                    Add all cards
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
