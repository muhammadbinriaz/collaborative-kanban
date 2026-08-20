"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

import { AppHeader } from "@/components/app-header";
import { InvitePanel } from "@/components/invite-panel";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { Board, WorkspaceDetail } from "@/types";

export default function WorkspacePage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params.workspaceId;
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const workspace = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => api<WorkspaceDetail>(`/api/v1/workspaces/${workspaceId}`),
    enabled: Boolean(user && workspaceId),
  });

  const boards = useQuery({
    queryKey: ["boards", workspaceId],
    queryFn: () => api<Board[]>(`/api/v1/workspaces/${workspaceId}/boards`),
    enabled: Boolean(user && workspaceId),
  });

  const create = useMutation({
    mutationFn: () =>
      api<Board>(`/api/v1/workspaces/${workspaceId}/boards`, {
        method: "POST",
        body: JSON.stringify({ name, description: description || null }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["boards", workspaceId] });
      setName("");
      setDescription("");
      setOpen(false);
      toast.success("Board created");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!ready || !user || workspace.isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="min-h-screen">
      <AppHeader title={workspace.data?.name} backHref="/workspaces" backLabel="Workspaces" />
      <main className="mx-auto max-w-[1400px] px-4 py-8">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-muted-foreground">Boards</p>
            <h2 className="font-serif text-3xl">{workspace.data?.name}</h2>
          </div>
          <div className="flex items-center gap-2">
            {workspace.data ? <InvitePanel workspace={workspace.data} /> : null}
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4" />
                  New board
                </Button>
              </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create board</DialogTitle>
              </DialogHeader>
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  create.mutate();
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="board-name">Name</Label>
                  <Input id="board-name" value={name} onChange={(event) => setName(event.target.value)} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="board-description">Description</Label>
                  <Textarea id="board-description" value={description} onChange={(event) => setDescription(event.target.value)} />
                </div>
                <Button type="submit" disabled={create.isPending || !name.trim()}>
                  Create
                </Button>
              </form>
            </DialogContent>
          </Dialog>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {boards.data?.map((board) => (
            <Link key={board.id} href={`/boards/${board.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <CardTitle>{board.name}</CardTitle>
                  <CardDescription>{board.description || "No description"}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
