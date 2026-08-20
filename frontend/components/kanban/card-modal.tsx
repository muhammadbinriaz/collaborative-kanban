"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { CardComments } from "@/components/kanban/card-comments";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { BoardDetail, Card, Sprint, WorkspaceDetail } from "@/types";

export function CardModal({
  card,
  board,
  open,
  onOpenChange,
}: {
  card: Card | null;
  board: BoardDetail;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [estimate, setEstimate] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [sprintId, setSprintId] = useState("");
  const [labelIds, setLabelIds] = useState<string[]>([]);

  const workspace = useQuery({
    queryKey: ["workspace", board.workspace_id],
    queryFn: () => api<WorkspaceDetail>(`/api/v1/workspaces/${board.workspace_id}`),
    enabled: open,
  });

  const sprints = useQuery({
    queryKey: ["sprints", board.id],
    queryFn: () => api<Sprint[]>(`/api/v1/boards/${board.id}/sprints`),
    enabled: open,
  });

  useEffect(() => {
    if (!card) return;
    setTitle(card.title);
    setDescription(card.description ?? "");
    setDueDate(card.due_date ? card.due_date.slice(0, 10) : "");
    setEstimate(card.estimate_points != null ? String(card.estimate_points) : "");
    setAssigneeId(card.assignee_id ?? "");
    setSprintId(card.sprint_id ?? "");
    setLabelIds(card.labels.map((label) => label.id));
  }, [card]);

  const save = useMutation({
    mutationFn: () =>
      api<Card>(`/api/v1/cards/${card?.id}`, {
        method: "PUT",
        body: JSON.stringify({
          title,
          description,
          due_date: dueDate ? new Date(`${dueDate}T12:00:00`).toISOString() : null,
          estimate_points: estimate === "" ? null : Number(estimate),
          assignee_id: assigneeId || null,
          sprint_id: sprintId || null,
          label_ids: labelIds,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      queryClient.invalidateQueries({ queryKey: ["activity", board.id] });
      queryClient.invalidateQueries({ queryKey: ["analytics", board.id] });
      queryClient.invalidateQueries({ queryKey: ["sprints", board.id] });
      toast.success("Card updated");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const remove = useMutation({
    mutationFn: () => api<void>(`/api/v1/cards/${card?.id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      queryClient.invalidateQueries({ queryKey: ["activity", board.id] });
      onOpenChange(false);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!card) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Card details</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="card-title">Title</Label>
            <Input id="card-title" value={title} onChange={(event) => setTitle(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="card-description">Description</Label>
            <Textarea
              id="card-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={4}
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="card-due">Due date</Label>
              <Input id="card-due" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="card-estimate">Estimate (points)</Label>
              <Input
                id="card-estimate"
                type="number"
                min={0}
                step={0.5}
                value={estimate}
                onChange={(event) => setEstimate(event.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="card-assignee">Assignee</Label>
              <select
                id="card-assignee"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={assigneeId}
                onChange={(event) => setAssigneeId(event.target.value)}
              >
                <option value="">Unassigned</option>
                {(workspace.data?.members ?? []).map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="card-sprint">Sprint</Label>
              <select
                id="card-sprint"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={sprintId}
                onChange={(event) => setSprintId(event.target.value)}
              >
                <option value="">None</option>
                {(sprints.data ?? [])
                  .filter((sprint) => sprint.status !== "completed")
                  .map((sprint) => (
                    <option key={sprint.id} value={sprint.id}>
                      {sprint.name}
                    </option>
                  ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Labels</Label>
            <div className="flex flex-wrap gap-2">
              {board.labels.map((label) => {
                const active = labelIds.includes(label.id);
                return (
                  <button
                    key={label.id}
                    type="button"
                    onClick={() =>
                      setLabelIds((current) =>
                        current.includes(label.id) ? current.filter((id) => id !== label.id) : [...current, label.id],
                      )
                    }
                    className={`rounded-full px-3 py-1 text-xs font-medium text-white ${active ? "ring-2 ring-offset-2 ring-ring" : "opacity-70"}`}
                    style={{ backgroundColor: label.color }}
                  >
                    {label.name}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <Button type="button" variant="destructive" onClick={() => remove.mutate()} disabled={remove.isPending}>
              Delete
            </Button>
            <Button type="submit" disabled={save.isPending}>
              Save
            </Button>
          </div>
        </form>
        <CardComments cardId={card.id} />
      </DialogContent>
    </Dialog>
  );
}
