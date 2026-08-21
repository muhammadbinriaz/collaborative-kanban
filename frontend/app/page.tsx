"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { HomeRedirectSkeleton } from "@/components/skeletons";
import { getAccessToken } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(getAccessToken() ? "/workspaces" : "/login");
  }, [router]);

  return <HomeRedirectSkeleton />;
}
