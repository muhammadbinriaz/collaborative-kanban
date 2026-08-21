import { AppHeader } from "@/components/app-header";
import { Skeleton } from "@/components/ui/skeleton";

function HeaderShell({ titleWidth = "w-28" }: { titleWidth?: string }) {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className={`h-4 ${titleWidth}`} />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="hidden h-4 w-20 sm:block" />
        </div>
      </div>
    </header>
  );
}

export function WorkspacesPageSkeleton() {
  return (
    <div className="min-h-screen">
      <HeaderShell titleWidth="w-24" />
      <main className="mx-auto max-w-[1400px] px-4 py-8">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div className="space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-9 w-48" />
          </div>
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-6 space-y-3">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="mt-4 h-4 w-24" />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export function WorkspaceDetailSkeleton() {
  return (
    <div className="min-h-screen">
      <HeaderShell titleWidth="w-40" />
      <main className="mx-auto max-w-[1400px] px-4 py-8">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div className="space-y-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-9 w-56" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-9 w-36" />
            <Skeleton className="h-9 w-28" />
          </div>
        </div>
        <div className="mb-8 max-w-lg rounded-xl border p-4 space-y-3">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-32" />
        </div>
        <Skeleton className="mb-3 h-3 w-28" />
        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-6 space-y-3">
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ))}
        </div>
        <Skeleton className="mb-3 h-3 w-32" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-6 space-y-3">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export function BoardPageSkeleton() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <HeaderShell titleWidth="w-36" />
      <div className="flex shrink-0 items-center gap-2 border-b px-4 py-2">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-14" />
      </div>
      <div className="flex min-h-0 flex-1 gap-4 overflow-x-auto p-4">
        {Array.from({ length: 4 }).map((_, col) => (
          <div key={col} className="flex w-72 shrink-0 flex-col gap-3 rounded-xl border bg-muted/40 p-3">
            <Skeleton className="h-5 w-28" />
            {Array.from({ length: 3 + (col % 2) }).map((_, row) => (
              <div key={row} className="space-y-2 rounded-lg border bg-card p-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <div className="flex gap-2 pt-1">
                  <Skeleton className="h-5 w-12 rounded-full" />
                  <Skeleton className="h-5 w-10 rounded-full" />
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function WhiteboardCanvasSkeleton() {
  return (
    <div className="relative h-full w-full bg-muted/30">
      <Skeleton className="absolute left-4 top-4 h-10 w-10 rounded-lg" />
      <Skeleton className="absolute left-4 top-16 h-48 w-12 rounded-lg" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="space-y-3">
          <Skeleton className="mx-auto h-6 w-40" />
          <Skeleton className="mx-auto h-4 w-56" />
        </div>
      </div>
    </div>
  );
}

export function WhiteboardPageSkeleton() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <HeaderShell titleWidth="w-40" />
      <div className="flex items-center justify-between border-b px-4 py-2">
        <Skeleton className="h-4 w-24" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 rounded-full" />
          <Skeleton className="h-8 w-16" />
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <WhiteboardCanvasSkeleton />
      </div>
    </div>
  );
}

export function InvitePageSkeleton() {
  return (
    <div className="min-h-screen">
      <AppHeader title="Invite" />
      <main className="mx-auto flex max-w-md flex-col gap-4 px-4 py-16">
        <div className="rounded-xl border bg-card p-6 space-y-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-9 w-full" />
        </div>
      </main>
    </div>
  );
}

export function HomeRedirectSkeleton() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3">
      <Skeleton className="h-10 w-10 rounded-xl" />
      <Skeleton className="h-4 w-32" />
    </div>
  );
}
