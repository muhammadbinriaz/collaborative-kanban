"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type AiJob = {
  id: string;
  job_type: string;
  status: string;
  result: Record<string, unknown> | null;
  error: string | null;
};

type AiStatus = {
  groq_configured: boolean;
  model: string;
  embeddings: string;
};

const ACTIONS: { type: string; path: string; label: string; needsCard?: boolean }[] = [
  { type: "prioritize", path: "prioritize", label: "Prioritize tasks" },
  { type: "standup", path: "standup", label: "Standup summary" },
  { type: "risk", path: "risk-detection", label: "Detect risks" },
  { type: "workload", path: "workload-balance", label: "Balance workload" },
  { type: "sprint-plan", path: "sprint-plan", label: "Plan sprint" },
  { type: "predict", path: "predict", label: "Predict ETAs" },
  { type: "similar", path: "similar", label: "Find similar (selected card)", needsCard: true },
];

export function AiPanel({ boardId, selectedCardId }: { boardId: string; selectedCardId?: string | null }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [output, setOutput] = useState<AiJob | null>(null);

  const status = useQuery({
    queryKey: ["ai-status"],
    queryFn: () => api<AiStatus>("/api/v1/ai/status"),
  });

  const job = useQuery({
    queryKey: ["ai-job", jobId],
    queryFn: () => api<AiJob>(`/api/v1/ai/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      return state === "pending" || state === "running" ? 1500 : false;
    },
  });

  useEffect(() => {
    if (job.data && (job.data.status === "completed" || job.data.status === "failed")) {
      setOutput(job.data);
    }
  }, [job.data]);

  const run = useMutation({
    mutationFn: async (action: (typeof ACTIONS)[number]) => {
      if (action.needsCard && !selectedCardId) {
        throw new Error("Open a card first, then run similar search");
      }
      return api<AiJob>(`/api/v1/ai/boards/${boardId}/${action.path}`, {
        method: "POST",
        body: JSON.stringify(action.needsCard ? { card_id: selectedCardId } : {}),
      });
    },
    onSuccess: (created) => {
      setJobId(created.id);
      setOutput(created);
      toast.success("AI job started");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 font-serif text-2xl">
            <Sparkles className="h-5 w-5 text-primary" />
            AI Project Manager
          </h2>
          <p className="text-sm text-muted-foreground">
            {status.data?.groq_configured
              ? `Connected · ${status.data.model} · embeddings: ${status.data.embeddings}`
              : "Groq key missing — add GROQ_API_KEY to .env and restart backend"}
          </p>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {ACTIONS.map((action) => (
          <Button
            key={action.type}
            variant="outline"
            className="justify-start"
            disabled={run.isPending || !status.data?.groq_configured && action.type !== "similar"}
            onClick={() => run.mutate(action)}
          >
            {action.label}
          </Button>
        ))}
      </div>

      <section className="rounded-xl border bg-card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Result</h3>
          {output ? (
            <span className="text-xs uppercase tracking-wide text-muted-foreground">{output.status}</span>
          ) : null}
        </div>
        {!output ? (
          <p className="text-sm text-muted-foreground">Run an AI action to see suggestions here.</p>
        ) : output.status === "failed" ? (
          <p className="text-sm text-destructive">{output.error || "AI job failed"}</p>
        ) : output.status !== "completed" ? (
          <p className="text-sm text-muted-foreground">Working… this usually takes a few seconds.</p>
        ) : (
          <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-lg bg-muted/50 p-3 text-xs leading-relaxed">
            {JSON.stringify(output.result, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
