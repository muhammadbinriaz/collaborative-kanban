"use client";

import { Calendar } from "lucide-react";

import { formatDate } from "@/lib/utils";
import type { Card } from "@/types";

export function CardItem({ card, onClick }: { card: Card; onClick: () => void }) {
  const due = formatDate(card.due_date);

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-lg border bg-card p-3 text-left shadow-sm transition hover:border-primary/40 hover:shadow"
    >
      {card.labels.length > 0 ? (
        <div className="mb-2 flex flex-wrap gap-1">
          {card.labels.map((label) => (
            <span
              key={label.id}
              className="h-1.5 w-10 rounded-full"
              style={{ backgroundColor: label.color }}
              title={label.name}
            />
          ))}
        </div>
      ) : null}
      <p className="text-sm font-medium leading-snug">{card.title}</p>
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          {due ? (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {due}
            </span>
          ) : null}
          {card.estimate_points != null ? <span>{card.estimate_points} pts</span> : null}
        </span>
        {card.assignee ? <span>{card.assignee.name.split(" ")[0]}</span> : null}
      </div>
    </button>
  );
}
