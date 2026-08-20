"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api } from "@/lib/api";
import type { AppNotification } from "@/types";

export function NotificationBell() {
  const queryClient = useQueryClient();
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api<AppNotification[]>("/api/v1/notifications"),
    refetchInterval: 30000,
  });

  const unread = notifications.data?.filter((n) => !n.read_at).length ?? 0;

  const markRead = useMutation({
    mutationFn: (id: string) => api(`/api/v1/notifications/${id}/read`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => api("/api/v1/notifications/read-all", { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          {unread > 0 ? (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] text-destructive-foreground">
              {unread}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-2 py-1.5">
          <p className="text-sm font-medium">Notifications</p>
          {unread > 0 ? (
            <button
              type="button"
              className="text-xs text-primary hover:underline"
              onClick={() => markAll.mutate()}
            >
              Mark all read
            </button>
          ) : null}
        </div>
        {(notifications.data ?? []).slice(0, 8).map((note) => (
          <DropdownMenuItem
            key={note.id}
            className="flex flex-col items-start gap-1 whitespace-normal"
            onSelect={() => {
              if (!note.read_at) markRead.mutate(note.id);
            }}
            asChild={Boolean(note.link)}
          >
            {note.link ? (
              <Link href={note.link}>
                <span className={`text-sm ${note.read_at ? "text-muted-foreground" : "font-medium"}`}>
                  {note.title}
                </span>
                <span className="text-xs text-muted-foreground">{note.body}</span>
              </Link>
            ) : (
              <>
                <span className={`text-sm ${note.read_at ? "text-muted-foreground" : "font-medium"}`}>
                  {note.title}
                </span>
                <span className="text-xs text-muted-foreground">{note.body}</span>
              </>
            )}
          </DropdownMenuItem>
        ))}
        {(notifications.data ?? []).length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">No notifications yet</p>
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
