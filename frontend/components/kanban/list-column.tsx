"use client";

import { useState } from "react";
import { Draggable, Droppable } from "@hello-pangea/dnd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

import { CardItem } from "@/components/kanban/card-item";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { BoardList, Card } from "@/types";

export function ListColumn({
  boardId,
  list,
  onOpenCard,
}: {
  boardId: string;
  list: BoardList;
  onOpenCard: (card: Card) => void;
}) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const cards = [...list.cards].sort((a, b) => a.position - b.position);

  const createCard = useMutation({
    mutationFn: () =>
      api<Card>(`/api/v1/lists/${list.id}/cards`, {
        method: "POST",
        body: JSON.stringify({ title }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", boardId] });
      setTitle("");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <section className="flex w-72 shrink-0 flex-col rounded-xl bg-secondary/80 p-2">
      <header className="flex items-center justify-between px-2 py-2">
        <h3 className="text-sm font-semibold">{list.name}</h3>
        <span className="text-xs text-muted-foreground">{cards.length}</span>
      </header>
      <Droppable droppableId={list.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`min-h-24 flex-1 space-y-2 rounded-lg p-1 ${snapshot.isDraggingOver ? "bg-accent/60" : ""}`}
          >
            {cards.map((card, index) => (
              <Draggable key={card.id} draggableId={card.id} index={index}>
                {(drag) => (
                  <div ref={drag.innerRef} {...drag.draggableProps} {...drag.dragHandleProps}>
                    <CardItem card={card} onClick={() => onOpenCard(card)} />
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
      <form
        className="mt-2 space-y-2 p-1"
        onSubmit={(event) => {
          event.preventDefault();
          if (title.trim()) createCard.mutate();
        }}
      >
        <Input
          placeholder="Add a card"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <Button type="submit" size="sm" variant="ghost" className="w-full" disabled={createCard.isPending}>
          <Plus className="h-4 w-4" />
          Add card
        </Button>
      </form>
    </section>
  );
}
