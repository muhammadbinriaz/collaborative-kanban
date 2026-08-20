"use client";

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { InvitePreview } from "@/types";

export default function InvitePage() {
  const { user, ready } = useAuth({ requireAuth: true });
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const token = params.token;

  const preview = useQuery({
    queryKey: ["invite", token],
    queryFn: () => api<InvitePreview>(`/api/v1/invites/${token}`),
    enabled: Boolean(token && user),
  });

  const accept = useMutation({
    mutationFn: () =>
      api<{ workspace_id: string }>(`/api/v1/invites/${token}/accept`, { method: "POST" }),
    onSuccess: (data) => {
      toast.success("Joined workspace");
      router.replace(`/workspaces/${data.workspace_id}`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!ready || !user) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <div className="min-h-screen">
      <AppHeader title="Invite" />
      <main className="mx-auto flex max-w-md flex-col gap-4 px-4 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Join workspace</CardTitle>
            <CardDescription>
              {preview.isError
                ? "This invite is invalid or expired."
                : preview.data
                  ? `You are invited to ${preview.data.workspace_name} as ${preview.data.role}.`
                  : "Loading invite…"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              className="w-full"
              disabled={!preview.data || accept.isPending}
              onClick={() => accept.mutate()}
            >
              Accept invite
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
