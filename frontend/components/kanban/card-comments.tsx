"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Comment } from "@/types";

export function CardComments({ cardId }: { cardId: string }) {
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");

  const comments = useQuery({
    queryKey: ["comments", cardId],
    queryFn: () => api<Comment[]>(`/api/v1/cards/${cardId}/comments`),
  });

  const create = useMutation({
    mutationFn: () =>
      api<Comment>(`/api/v1/cards/${cardId}/comments`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    onSuccess: () => {
      setBody("");
      queryClient.invalidateQueries({ queryKey: ["comments", cardId] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-3 border-t pt-4">
      <h3 className="text-sm font-semibold">Comments</h3>
      <div className="max-h-48 space-y-3 overflow-y-auto">
        {(comments.data ?? []).map((comment) => (
          <div key={comment.id} className="rounded-lg bg-muted/50 p-2">
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-xs font-medium">{comment.author.name}</span>
              <span className="text-[10px] text-muted-foreground">
                {new Date(comment.created_at).toLocaleString()}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-sm">{comment.body}</p>
          </div>
        ))}
      </div>
      <form
        className="space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (body.trim()) create.mutate();
        }}
      >
        <Textarea
          placeholder="Write a comment… use @name to mention"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          rows={3}
        />
        <Button type="submit" size="sm" disabled={create.isPending || !body.trim()}>
          Comment
        </Button>
      </form>
    </div>
  );
}
