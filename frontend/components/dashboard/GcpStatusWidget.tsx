"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { GcpItemStatus, GcpStatusItem, GcpStatusResponse } from "@/lib/types";

const DOT: Record<GcpItemStatus, string> = {
  ok: "bg-emerald-500",
  error: "bg-red-500",
  running: "bg-sky-500 animate-pulse",
  unknown: "bg-slate-400",
};

function formatDate(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

function consoleUrl(item: GcpStatusItem, project: string, region: string) {
  const base = "https://console.cloud.google.com";
  if (item.kind === "Cloud Run job")
    return `${base}/run/jobs/details/${region}/${item.name}/executions?project=${project}`;
  if (item.kind === "Cloud Run service")
    return `${base}/run/detail/${region}/${item.name}/logs?project=${project}`;
  return `${base}/cloudscheduler?project=${project}`;
}

export function GcpStatusWidget() {
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["gcp-status"],
    queryFn: () => api.dashboard.getGcpStatus(),
    refetchInterval: 5 * 60_000,
  });

  async function refresh() {
    setRefreshing(true);
    try {
      const fresh = await api.dashboard.getGcpStatus(true);
      queryClient.setQueryData<GcpStatusResponse>(["gcp-status"], fresh);
    } finally {
      setRefreshing(false);
    }
  }

  const items = data?.items ?? [];
  const failing = items.filter((i) => i.status === "error");
  const sourceErrors = data?.source_errors ?? [];
  const allOk = !!data && failing.length === 0 && sourceErrors.length === 0;

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          {data && <span className={`inline-block size-2.5 rounded-full ${allOk ? DOT.ok : DOT.error}`} />}
          Services GCP
        </CardTitle>
        <CardDescription>
          {data
            ? `${data.project} · ${data.region} · vérifié ${formatDate(data.checked_at)}`
            : "Cloud Run jobs, services et Cloud Scheduler"}
        </CardDescription>
        <CardAction>
          <Button variant="outline" size="sm" onClick={refresh} disabled={refreshing || isLoading}>
            <RefreshCw className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Rafraîchir
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Interrogation de GCP…</p>}

        {isError && (
          <div className="rounded-lg bg-destructive/10 text-destructive px-4 py-3 text-sm">
            Impossible de récupérer le statut : {(error as Error)?.message}
          </div>
        )}

        {data && (
          <div
            className={`rounded-lg px-4 py-3 text-sm font-medium ${
              allOk
                ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                : "bg-destructive/10 text-destructive"
            }`}
          >
            {allOk
              ? `Tout est OK — ${items.length} services opérationnels`
              : `${failing.length} service${failing.length > 1 ? "s" : ""} en erreur sur ${items.length}`}
          </div>
        )}

        {sourceErrors.map((e) => (
          <div key={e.source} className="rounded-lg bg-destructive/10 text-destructive px-4 py-3 text-sm">
            <span className="font-medium">{e.source} :</span> {e.message}
          </div>
        ))}

        {data && items.length > 0 && (
          <ul className="divide-y rounded-lg border">
            {items.map((item) => (
              <li key={`${item.kind}-${item.name}`} className="px-4 py-2.5">
                <div className="flex items-center gap-3">
                  <span className={`inline-block size-2.5 shrink-0 rounded-full ${DOT[item.status]}`} />
                  <a
                    href={consoleUrl(item, data.project, data.region)}
                    target="_blank"
                    rel="noreferrer"
                    className="min-w-0 flex-1 truncate text-sm font-medium hover:underline"
                  >
                    {item.name}
                  </a>
                  <span className="hidden sm:inline text-xs text-muted-foreground">{item.kind}</span>
                  <span className="w-28 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                    {formatDate(item.last_run)}
                  </span>
                </div>
                {item.detail && (
                  <p
                    className={`mt-1 pl-5.5 text-xs break-words ${
                      item.status === "error" ? "text-destructive" : "text-muted-foreground"
                    }`}
                  >
                    {item.detail}
                    {item.execution && item.status === "error" && item.kind === "Cloud Run job" && (
                      <span className="text-muted-foreground"> ({item.execution})</span>
                    )}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
