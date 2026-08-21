"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

import { useRouteTransition } from "@/components/route-transition";

/** Router that shows the destination skeleton immediately on push/replace. */
export function useAppRouter() {
  const router = useRouter();
  const { start } = useRouteTransition();

  const push = useCallback(
    (href: string, options?: Parameters<typeof router.push>[1]) => {
      start(href);
      router.push(href, options);
    },
    [router, start],
  );

  const replace = useCallback(
    (href: string, options?: Parameters<typeof router.replace>[1]) => {
      start(href);
      router.replace(href, options);
    },
    [router, start],
  );

  return useMemo(() => ({ ...router, push, replace }), [router, push, replace]);
}
