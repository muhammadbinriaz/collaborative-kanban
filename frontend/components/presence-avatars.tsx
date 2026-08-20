"use client";

import type { PresenceUser } from "@/types";

export function PresenceAvatars({ users, connected }: { users: PresenceUser[]; connected: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-500" : "bg-muted-foreground/40"}`}
        title={connected ? "Live" : "Reconnecting…"}
      />
      <div className="flex -space-x-2">
        {users.slice(0, 5).map((user) => (
          <span
            key={user.id}
            title={user.name}
            className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-background bg-primary text-[10px] font-semibold text-primary-foreground"
          >
            {user.name
              .split(" ")
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </span>
        ))}
      </div>
      {users.length > 5 ? (
        <span className="text-xs text-muted-foreground">+{users.length - 5}</span>
      ) : null}
    </div>
  );
}
