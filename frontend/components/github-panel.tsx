"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Github } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type GithubStatus = {
  oauth_configured: boolean;
  connection: {
    id: string;
    installation_login: string;
    repo_full_name: string | null;
  } | null;
};

export function GithubPanel({ workspaceId, canManage }: { workspaceId: string; canManage: boolean }) {
  const queryClient = useQueryClient();
  const [repo, setRepo] = useState("");

  const status = useQuery({
    queryKey: ["github", workspaceId],
    queryFn: () => api<GithubStatus>(`/api/v1/github/workspaces/${workspaceId}/status`),
  });

  useEffect(() => {
    setRepo(status.data?.connection?.repo_full_name ?? "");
  }, [status.data?.connection?.repo_full_name]);

  const connect = useMutation({
    mutationFn: () => api<{ authorize_url: string }>(`/api/v1/github/workspaces/${workspaceId}/authorize`),
    onSuccess: (data) => {
      window.location.href = data.authorize_url;
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const saveRepo = useMutation({
    mutationFn: () =>
      api(`/api/v1/github/workspaces/${workspaceId}/repo`, {
        method: "PUT",
        body: JSON.stringify({ repo_full_name: repo }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github", workspaceId] });
      toast.success("Repository linked");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const disconnect = useMutation({
    mutationFn: () => api(`/api/v1/github/workspaces/${workspaceId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github", workspaceId] });
      toast.success("GitHub disconnected");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!canManage) return null;

  return (
    <div className="rounded-xl border p-4">
      <div className="mb-3 flex items-center gap-2">
        <Github className="h-4 w-4" />
        <h3 className="text-sm font-semibold">GitHub</h3>
      </div>
      {!status.data?.oauth_configured ? (
        <p className="text-xs text-muted-foreground">
          Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in root `.env` to enable OAuth.
        </p>
      ) : !status.data.connection ? (
        <Button size="sm" onClick={() => connect.mutate()} disabled={connect.isPending}>
          Connect GitHub
        </Button>
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Connected as <strong>{status.data.connection.installation_login}</strong>
          </p>
          <div className="flex gap-2">
            <Input
              placeholder="owner/repo"
              value={repo}
              onChange={(event) => setRepo(event.target.value)}
            />
            <Button size="sm" onClick={() => saveRepo.mutate()} disabled={saveRepo.isPending || !repo.trim()}>
              Save
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Webhook URL: <code className="text-[11px]">/api/v1/github/webhook</code>
          </p>
          <Button size="sm" variant="outline" onClick={() => disconnect.mutate()} disabled={disconnect.isPending}>
            Disconnect
          </Button>
        </div>
      )}
    </div>
  );
}
