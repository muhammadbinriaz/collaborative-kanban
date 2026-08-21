"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { User } from "@/types";

export default function VerifyEmailPage() {
  const params = useSearchParams();
  const token = params.get("token");
  const [done, setDone] = useState(false);

  const verify = useMutation({
    mutationFn: () =>
      api<User>(`/api/v1/auth/verify-email?token=${encodeURIComponent(token || "")}`, { method: "POST" }),
    onSuccess: () => {
      setDone(true);
      toast.success("Email verified");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  useEffect(() => {
    if (token) verify.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="font-serif text-3xl">Email verification</h1>
      {!token ? <p className="text-sm text-muted-foreground">Missing token.</p> : null}
      {verify.isPending ? <p className="text-sm text-muted-foreground">Verifying…</p> : null}
      {done ? (
        <>
          <p className="text-sm">Your email is verified.</p>
          <Button asChild>
            <Link href="/workspaces">Continue</Link>
          </Button>
        </>
      ) : null}
    </div>
  );
}
