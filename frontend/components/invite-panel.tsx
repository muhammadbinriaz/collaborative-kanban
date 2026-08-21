"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Copy, Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Invite, WorkspaceDetail, WorkspaceRole } from "@/types";

export function InvitePanel({ workspace }: { workspace: WorkspaceDetail }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [role, setRole] = useState<WorkspaceRole>("member");
  const [email, setEmail] = useState("");
  const canInvite = workspace.role === "owner" || workspace.role === "admin";

  const invites = useQuery({
    queryKey: ["invites", workspace.id],
    queryFn: () => api<Invite[]>(`/api/v1/workspaces/${workspace.id}/invites`),
    enabled: canInvite && open,
  });

  const create = useMutation({
    mutationFn: () =>
      api<Invite>(`/api/v1/workspaces/${workspace.id}/invites`, {
        method: "POST",
        body: JSON.stringify({
          role,
          expires_in_hours: 168,
          email: email.trim() || null,
        }),
      }),
    onSuccess: async (invite) => {
      queryClient.invalidateQueries({ queryKey: ["invites", workspace.id] });
      const url = invite.invite_url ?? `${window.location.origin}/invite/${invite.token}`;
      await navigator.clipboard.writeText(url);
      setEmail("");
      toast.success(invite.email ? "Invite emailed and link copied" : "Invite link copied");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!canInvite) return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Link2 className="h-4 w-4" />
          Invite
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite teammates</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="invite-email">
              Email (optional)
            </label>
            <Input
              id="invite-email"
              type="email"
              placeholder="teammate@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="invite-role">
              Role
            </label>
            <select
              id="invite-role"
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
              value={role}
              onChange={(event) => setRole(event.target.value as WorkspaceRole)}
            >
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <Button onClick={() => create.mutate()} disabled={create.isPending}>
            Create & copy link
          </Button>
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Active links</p>
            {(invites.data ?? []).map((invite) => (
              <div key={invite.id} className="flex items-center justify-between gap-2 rounded-md border p-2 text-xs">
                <span>
                  {invite.role} · expires {new Date(invite.expires_at).toLocaleDateString()}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={async () => {
                    const url = invite.invite_url ?? `${window.location.origin}/invite/${invite.token}`;
                    await navigator.clipboard.writeText(url);
                    toast.success("Copied");
                  }}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
          <div className="space-y-1 border-t pt-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Members</p>
            {workspace.members.map((member) => (
              <div key={member.id} className="flex justify-between text-sm">
                <span>{member.name}</span>
                <span className="text-muted-foreground">{member.role}</span>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
