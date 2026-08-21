"use client";

import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Paperclip, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Attachment } from "@/types";

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function CardAttachments({ cardId }: { cardId: string }) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);

  const attachments = useQuery({
    queryKey: ["attachments", cardId],
    queryFn: () => api<Attachment[]>(`/api/v1/cards/${cardId}/attachments`),
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData();
      body.append("file", file);
      return api<Attachment>(`/api/v1/cards/${cardId}/attachments`, { method: "POST", body });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attachments", cardId] });
      toast.success("File uploaded");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api<void>(`/api/v1/attachments/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["attachments", cardId] }),
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-3 border-t pt-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Attachments</h3>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={upload.isPending}
          onClick={() => inputRef.current?.click()}
        >
          <Paperclip className="h-3.5 w-3.5" />
          Upload
        </Button>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) upload.mutate(file);
            event.target.value = "";
          }}
        />
      </div>
      <ul className="space-y-2">
        {(attachments.data ?? []).map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm">
            <a
              href={item.download_url ?? "#"}
              target="_blank"
              rel="noreferrer"
              className="min-w-0 truncate text-primary hover:underline"
            >
              {item.filename}
            </a>
            <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(item.size_bytes)}</span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => remove.mutate(item.id)}
              disabled={remove.isPending}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </li>
        ))}
        {!attachments.isLoading && (attachments.data ?? []).length === 0 ? (
          <li className="text-xs text-muted-foreground">No files yet.</li>
        ) : null}
      </ul>
    </div>
  );
}
