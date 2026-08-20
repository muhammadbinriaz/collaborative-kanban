"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/lib/api";
import type { BoardAnalytics } from "@/types";

export function AnalyticsPanel({ boardId }: { boardId: string }) {
  const analytics = useQuery({
    queryKey: ["analytics", boardId],
    queryFn: () => api<BoardAnalytics>(`/api/v1/boards/${boardId}/analytics`),
    refetchInterval: 30000,
  });

  const data = analytics.data;

  return (
    <div className="space-y-6 p-4">
      <div>
        <h2 className="font-serif text-2xl">Analytics</h2>
        <p className="text-sm text-muted-foreground">
          {data?.active_sprint
            ? `Active sprint: ${data.active_sprint.name} (${data.active_sprint.completed_points}/${data.active_sprint.total_points} pts)`
            : "No active sprint — start one to unlock burndown."}
        </p>
      </div>

      <section className="rounded-xl border bg-card p-4">
        <h3 className="mb-3 text-sm font-semibold">Burndown</h3>
        <div className="h-56">
          {(data?.burndown.length ?? 0) > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.burndown}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="ideal_remaining" name="Ideal" stroke="hsl(var(--muted-foreground))" strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="actual_remaining" name="Actual" stroke="hsl(var(--primary))" strokeWidth={2} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">Start a sprint with estimated cards.</p>
          )}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold">Velocity</h3>
          <div className="h-52">
            {(data?.velocity.length ?? 0) > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.velocity}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="sprint_name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="committed_points" name="Committed" fill="hsl(var(--muted-foreground))" />
                  <Bar dataKey="completed_points" name="Completed" fill="hsl(var(--primary))" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">Complete a sprint to track velocity.</p>
            )}
          </div>
        </section>

        <section className="rounded-xl border bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold">Workload</h3>
          <div className="h-52">
            {(data?.workload.length ?? 0) > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.workload} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="user_name" width={90} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="estimate_points" name="Points" fill="hsl(var(--primary))" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">Assign cards to see workload.</p>
            )}
          </div>
        </section>
      </div>

      <section className="rounded-xl border bg-card p-4">
        <h3 className="mb-3 text-sm font-semibold">Bottlenecks</h3>
        <div className="space-y-2">
          {(data?.bottlenecks ?? []).map((item, index) => (
            <div key={`${item.type}-${index}`} className="rounded-lg border px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{item.title}</p>
                <span
                  className={`text-[10px] uppercase tracking-wide ${
                    item.severity === "high"
                      ? "text-destructive"
                      : item.severity === "medium"
                        ? "text-amber-700"
                        : "text-muted-foreground"
                  }`}
                >
                  {item.severity}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{item.detail}</p>
            </div>
          ))}
          {(data?.bottlenecks.length ?? 0) === 0 ? (
            <p className="text-sm text-muted-foreground">No congestion, stale, or overdue signals right now.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
