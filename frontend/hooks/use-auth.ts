"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { authApi, getAccessToken, setAccessToken } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function useAuth({ requireAuth = false, guestOnly = false } = {}) {
  const router = useRouter();
  const { user, ready, setSession, clearSession } = useAuthStore();

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      try {
        const token = getAccessToken();
        if (!token) {
          const refreshed = await authApi.refresh();
          if (cancelled) return;
          setSession(refreshed.user, refreshed.access_token);
        } else {
          const me = await authApi.me();
          if (cancelled) return;
          setSession(me, token);
        }
      } catch {
        if (cancelled) return;
        clearSession();
        if (requireAuth) router.replace("/login");
      }
    }

    hydrate();
    return () => {
      cancelled = true;
    };
  }, [clearSession, requireAuth, router, setSession]);

  useEffect(() => {
    if (ready && user && guestOnly) router.replace("/workspaces");
  }, [guestOnly, ready, router, user]);

  return { user, ready };
}

export function persistAuth(accessToken: string) {
  setAccessToken(accessToken);
}
