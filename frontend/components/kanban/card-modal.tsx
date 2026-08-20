"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { CardComments } from "@/components/kanban/card-comments";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { BoardDetail, Card } from "@/types";

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
  const [labelIds, setLabelIds] = useState<string[]>([]);

  useEffect(() => {
    if (!card) return;
    setTitle(card.title);
    setDescription(card.description ?? "");
    setDueDate(card.due_date ? card.due_date.slice(0, 10) : "");
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
          label_ids: labelIds,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      queryClient.invalidateQueries({ queryKey: ["activity", board.id] });
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
          <div className="space-y-2">
            <Label htmlFor="card-due">Due date</Label>
            <Input id="card-due" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
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
