"use client";

import { useMemo, useState } from "react";
import { DragDropContext, type DropResult } from "@hello-pangea/dnd";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

import { ListColumn } from "@/components/kanban/list-column";
import { CardModal } from "@/components/kanban/card-modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { newCardPosition } from "@/lib/utils";
import type { BoardDetail, BoardList, Card } from "@/types";

export function BoardView({ board }: { board: BoardDetail }) {
  const queryClient = useQueryClient();
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [listName, setListName] = useState("");
  const lists = useMemo(() => [...board.lists].sort((a, b) => a.position - b.position), [board.lists]);

  function setBoard(next: BoardDetail) {
    queryClient.setQueryData(["board", board.id], next);
  }

  const move = useMutation({
    mutationFn: ({ cardId, listId, position }: { cardId: string; listId: string; position: number }) =>
      api<Card>(`/api/v1/cards/${cardId}/move`, {
        method: "POST",
        body: JSON.stringify({ list_id: listId, position }),
      }),
    onError: (error: Error) => {
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      toast.error(error.message);
    },
  });

  const createList = useMutation({
    mutationFn: () =>
      api<BoardList>(`/api/v1/boards/${board.id}/lists`, {
        method: "POST",
        body: JSON.stringify({ name: listName }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", board.id] });
      setListName("");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function onDragEnd(result: DropResult) {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const sourceList = lists.find((list) => list.id === source.droppableId);
    const destList = lists.find((list) => list.id === destination.droppableId);
    if (!sourceList || !destList) return;

    const moving = sourceList.cards.find((card) => card.id === draggableId);
    if (!moving) return;

    const destCards =
      source.droppableId === destination.droppableId
        ? destList.cards
        : destList.cards;
    const position = newCardPosition(destCards, destination.index, draggableId);

    const nextLists = lists.map((list) => {
      if (list.id === source.droppableId) {
        return { ...list, cards: list.cards.filter((card) => card.id !== draggableId) };
      }
      return list;
    });
    const updatedLists = nextLists.map((list) => {
      if (list.id !== destination.droppableId) return list;
      const cards = [...list.cards];
      const nextCard = { ...moving, list_id: destination.droppableId, position };
      cards.splice(destination.index, 0, nextCard);
      return { ...list, cards };
    });

    setBoard({ ...board, lists: updatedLists });
    move.mutate({ cardId: draggableId, listId: destination.droppableId, position });
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="board-scroll flex flex-1 items-start gap-4 overflow-x-auto p-4">
          {lists.map((list) => (
            <ListColumn
              key={list.id}
              boardId={board.id}
              list={list}
              onOpenCard={setSelectedCard}
            />
          ))}
          <form
            className="w-72 shrink-0 rounded-xl border bg-card/70 p-3"
            onSubmit={(event) => {
              event.preventDefault();
              if (listName.trim()) createList.mutate();
            }}
          >
            <Input
              placeholder="Add another list"
              value={listName}
              onChange={(event) => setListName(event.target.value)}
            />
            <Button className="mt-2 w-full" type="submit" variant="secondary" disabled={createList.isPending}>
              <Plus className="h-4 w-4" />
              Add list
            </Button>
          </form>
        </div>
      </DragDropContext>
      <CardModal
        card={selectedCard}
        board={board}
        open={Boolean(selectedCard)}
        onOpenChange={(open) => {
          if (!open) setSelectedCard(null);
        }}
      />
    </div>
  );
}
