"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LayoutGrid, LogOut } from "lucide-react";

import { NotificationBell } from "@/components/notifications-bell";
import { Button } from "@/components/ui/button";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function AppHeader({ title, backHref, backLabel }: { title?: string; backHref?: string; backLabel?: string }) {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);

  async function logout() {
    try {
      await authApi.logout();
    } catch {
      /* cookie may already be gone */
    }
    clearSession();
    router.replace("/login");
  }

  return (
    <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <Link href="/workspaces" className="flex items-center gap-2 font-semibold">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <LayoutGrid className="h-4 w-4" />
            </span>
            <span className="hidden sm:inline">Kanban</span>
          </Link>
          {title ? (
            <>
              <span className="text-muted-foreground">/</span>
              {backHref ? (
                <Link href={backHref} className="text-sm text-muted-foreground hover:text-foreground">
                  {backLabel ?? "Back"}
                </Link>
              ) : null}
              {backHref ? <span className="text-muted-foreground">/</span> : null}
              <h1 className="text-sm font-medium">{title}</h1>
            </>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          {user ? <NotificationBell /> : null}
          {user ? <span className="hidden text-sm text-muted-foreground sm:inline">{user.name}</span> : null}
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </div>
      </div>
    </header>
  );
}
