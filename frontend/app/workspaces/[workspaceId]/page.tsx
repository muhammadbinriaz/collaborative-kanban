"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { PencilRuler, Plus } from "lucide-react";

import { AppHeader } from "@/components/app-header";
import { GithubPanel } from "@/components/github-panel";
import { InvitePanel } from "@/components/invite-panel";
import { WorkspaceDetailSkeleton } from "@/components/skeletons";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/use-auth";
import { useAppRouter } from "@/hooks/use-app-router";
import { api } from "@/lib/api";
import type { Board, Whiteboard, WhiteboardSummary, WorkspaceDetail } from "@/types";

export default function WorkspacePage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params.workspaceId;
  const queryClient = useQueryClient();
  const router = useAppRouter();
  const [open, setOpen] = useState(false);
  const [wbOpen, setWbOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [wbName, setWbName] = useState("");

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

  const whiteboards = useQuery({
    queryKey: ["whiteboards", workspaceId],
    queryFn: () => api<WhiteboardSummary[]>(`/api/v1/workspaces/${workspaceId}/whiteboards`),
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

  const createWhiteboard = useMutation({
    mutationFn: () =>
      api<Whiteboard>(`/api/v1/workspaces/${workspaceId}/whiteboards`, {
        method: "POST",
        body: JSON.stringify({ name: wbName }),
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["whiteboards", workspaceId] });
      setWbName("");
      setWbOpen(false);
      toast.success("Whiteboard created");
      router.push(`/whiteboards/${created.id}`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!ready || !user || workspace.isLoading) {
    return <WorkspaceDetailSkeleton />;
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
            <Dialog open={wbOpen} onOpenChange={setWbOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <PencilRuler className="h-4 w-4" />
                  New whiteboard
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create whiteboard</DialogTitle>
                </DialogHeader>
                <form
                  className="space-y-4"
                  onSubmit={(event) => {
                    event.preventDefault();
                    createWhiteboard.mutate();
                  }}
                >
                  <div className="space-y-2">
                    <Label htmlFor="wb-name">Name</Label>
                    <Input
                      id="wb-name"
                      value={wbName}
                      onChange={(event) => setWbName(event.target.value)}
                      placeholder="Sprint planning sketch"
                      required
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Uses the open-source{" "}
                    <a className="underline" href="https://github.com/excalidraw/excalidraw" target="_blank" rel="noreferrer">
                      Excalidraw
                    </a>{" "}
                    editor for shapes and freehand drawing.
                  </p>
                  <Button type="submit" disabled={createWhiteboard.isPending || !wbName.trim()}>
                    Create
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
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
                    <Textarea
                      id="board-description"
                      value={description}
                      onChange={(event) => setDescription(event.target.value)}
                    />
                  </div>
                  <Button type="submit" disabled={create.isPending || !name.trim()}>
                    Create
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {workspace.data ? (
          <div className="mb-8 max-w-lg">
            <GithubPanel
              workspaceId={workspace.data.id}
              canManage={workspace.data.role === "owner" || workspace.data.role === "admin"}
            />
          </div>
        ) : null}

        {(whiteboards.isLoading || boards.isLoading) && (whiteboards.data ?? []).length === 0 && (boards.data ?? []).length === 0 ? (
          <>
            <Skeleton className="mb-3 h-3 w-28" />
            <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="space-y-3 rounded-xl border bg-card p-6">
                  <Skeleton className="h-5 w-1/2" />
                  <Skeleton className="h-4 w-2/3" />
                </div>
              ))}
            </div>
            <Skeleton className="mb-3 h-3 w-32" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="space-y-3 rounded-xl border bg-card p-6">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-4 w-full" />
                </div>
              ))}
            </div>
          </>
        ) : null}

        {(whiteboards.data ?? []).length > 0 ? (
          <section className="mb-10">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Whiteboards</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {whiteboards.data?.map((board) => (
                <Link key={board.id} href={`/whiteboards/${board.id}`}>
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <PencilRuler className="h-4 w-4" />
                        {board.name}
                      </CardTitle>
                      <CardDescription>Updated {new Date(board.updated_at).toLocaleString()}</CardDescription>
                    </CardHeader>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        ) : null}

        <section>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Kanban boards</h3>
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
        </section>
      </main>
    </div>
  );
}
