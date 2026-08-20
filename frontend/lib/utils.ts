import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value?: string | null) {
  if (!value) return null;
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function newCardPosition(cards: { id: string; position: number }[], destIndex: number, movedId: string) {
  const without = cards.filter((card) => card.id !== movedId);
  const prev = without[destIndex - 1];
  const next = without[destIndex];
  if (!prev && !next) return 65535;
  if (!prev) return next.position / 2;
  if (!next) return prev.position + 65535;
  return (prev.position + next.position) / 2;
}
