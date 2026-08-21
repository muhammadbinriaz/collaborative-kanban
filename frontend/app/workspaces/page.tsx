"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

import { AppHeader } from "@/components/app-header";
import { WorkspacesPageSkeleton } from "@/components/skeletons";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { Workspace } from "@/types";

export default function WorkspacesPage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");

  const workspaces = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => api<Workspace[]>("/api/v1/workspaces"),
    enabled: Boolean(user),
  });

  const create = useMutation({
    mutationFn: () => api<Workspace>("/api/v1/workspaces", { method: "POST", body: JSON.stringify({ name }) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setName("");
      setOpen(false);
      toast.success("Workspace created");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!ready || !user) {
    return <WorkspacesPageSkeleton />;
  }

  return (
    <div className="min-h-screen">
      <AppHeader title="Workspaces" />
      <main className="mx-auto max-w-[1400px] px-4 py-8">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-muted-foreground">Your teams</p>
            <h2 className="font-serif text-3xl">Workspaces</h2>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" />
                New workspace
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create workspace</DialogTitle>
              </DialogHeader>
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  create.mutate();
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="workspace-name">Name</Label>
                  <Input id="workspace-name" value={name} onChange={(event) => setName(event.target.value)} required />
                </div>
                <Button type="submit" disabled={create.isPending || !name.trim()}>
                  Create
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        {workspaces.isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-3 rounded-xl border bg-card p-6">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="mt-4 h-4 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {workspaces.data?.map((workspace) => (
                <Link key={workspace.id} href={`/workspaces/${workspace.id}`}>
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardHeader>
                      <CardTitle>{workspace.name}</CardTitle>
                      <CardDescription>
                        {workspace.role ?? "member"} · {workspace.slug}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">Open boards</CardContent>
                  </Card>
                </Link>
              ))}
            </div>
            {workspaces.data?.length === 0 ? (
              <p className="mt-10 text-center text-muted-foreground">Create a workspace to start a board.</p>
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}
