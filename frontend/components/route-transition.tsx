"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";

import {
  BoardPageSkeleton,
  HomeRedirectSkeleton,
  InvitePageSkeleton,
  WhiteboardPageSkeleton,
  WorkspaceDetailSkeleton,
  WorkspacesPageSkeleton,
} from "@/components/skeletons";

type RouteTransitionContextValue = {
  pendingHref: string | null;
  start: (href: string) => void;
  clear: () => void;
};

const RouteTransitionContext = createContext<RouteTransitionContextValue | null>(null);

function normalizePath(href: string) {
  try {
    if (href.startsWith("http://") || href.startsWith("https://")) {
      const url = new URL(href);
      return url.pathname;
    }
  } catch {
    /* ignore */
  }
  const path = href.split("?")[0]?.split("#")[0] || href;
  return path.endsWith("/") && path.length > 1 ? path.slice(0, -1) : path;
}

export function skeletonForHref(href: string) {
  const path = normalizePath(href);
  if (path === "/login" || path === "/register" || path.startsWith("/verify-email")) return null;
  if (path.startsWith("/boards/")) return <BoardPageSkeleton />;
  if (path.startsWith("/whiteboards/")) return <WhiteboardPageSkeleton />;
  if (path.startsWith("/invite/")) return <InvitePageSkeleton />;
  if (/^\/workspaces\/[^/]+$/.test(path)) return <WorkspaceDetailSkeleton />;
  if (path === "/workspaces") return <WorkspacesPageSkeleton />;
  if (path === "/" || path === "") return <HomeRedirectSkeleton />;
  return <WorkspacesPageSkeleton />;
}

function isInternalAppHref(href: string) {
  if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return false;
  if (href.startsWith("http://") || href.startsWith("https://")) {
    try {
      return new URL(href).origin === window.location.origin;
    } catch {
      return false;
    }
  }
  return href.startsWith("/");
}

export function RouteTransitionProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [pendingHref, setPendingHref] = useState<string | null>(null);

  const clear = useCallback(() => setPendingHref(null), []);
  const start = useCallback(
    (href: string) => {
      const next = normalizePath(href);
      const current = normalizePath(pathname);
      if (!next || next === current) return;
      setPendingHref(next);
    },
    [pathname],
  );

  useEffect(() => {
    clear();
  }, [pathname, clear]);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented) return;
      if (event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const target = event.target as Element | null;
      const anchor = target?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor) return;
      if (anchor.target && anchor.target !== "_self") return;
      if (anchor.hasAttribute("download")) return;

      const href = anchor.getAttribute("href");
      if (!href || !isInternalAppHref(href)) return;

      const next = normalizePath(href);
      const current = normalizePath(pathname);
      if (next === current) return;

      setPendingHref(next);
    };

    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [pathname]);

  const value = useMemo(
    () => ({ pendingHref, start, clear }),
    [pendingHref, start, clear],
  );

  const showOverlay =
    Boolean(pendingHref) && normalizePath(pendingHref!) !== normalizePath(pathname);
  const overlay = showOverlay && pendingHref ? skeletonForHref(pendingHref) : null;

  return (
    <RouteTransitionContext.Provider value={value}>
      {children}
      {overlay ? (
        <div
          className="fixed inset-0 z-[100] overflow-y-auto bg-background"
          aria-busy="true"
          aria-live="polite"
        >
          {overlay}
        </div>
      ) : null}
    </RouteTransitionContext.Provider>
  );
}

export function useRouteTransition() {
  const ctx = useContext(RouteTransitionContext);
  if (!ctx) {
    return {
      pendingHref: null,
      start: (_href: string) => undefined,
      clear: () => undefined,
    };
  }
  return ctx;
}
