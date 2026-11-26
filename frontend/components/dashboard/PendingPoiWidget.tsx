"use client";

import { useQuery } from "@tanstack/react-query";
import { ExternalLink, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";

function formatDate(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
}

function waitingDays(value: string | null) {
  if (!value) return null;
  const ms = Date.now() - new Date(value).getTime();
  return Number.isNaN(ms) ? null : Math.floor(ms / 86_400_000);
}

export function PendingPoiWidget() {
  const { data, isLoading, isFetching, isError, error, refetch } = useQuery({
    queryKey: ["pending-poi"],
    queryFn: api.dashboard.getPendingPoi,
    refetchInterval: 5 * 60_000,
  });

  const total = data?.total ?? 0;

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          POI à valider
          {data && (
            <span
              className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-semibold ${
                total > 0 ? "bg-amber-500 text-white" : "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
              }`}
            >
              {total}
            </span>
          )}
        </CardTitle>
        <CardDescription>Soumissions des utilisateurs en attente de validation admin</CardDescription>
        <CardAction className="flex gap-2">
          {data && (
            <a
              href={data.admin_url}
              target="_blank"
              rel="noreferrer"
              className={buttonVariants({ variant: "outline", size: "sm" })}
            >
              <ExternalLink className="size-3.5" />
              Admin
            </a>
          )}
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching} aria-label="Rafraîchir">
            <RefreshCw className={`size-3.5 ${isFetching ? "animate-spin" : ""}`} />
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading && <p className="text-sm text-muted-foreground">Chargement…</p>}

        {isError && (
          <div className="rounded-lg bg-destructive/10 text-destructive px-4 py-3 text-sm">
            Impossible de récupérer les POI : {(error as Error)?.message}
          </div>
        )}

        {data && (
          <div className="grid grid-cols-2 gap-3">
            {data.groups.map((g) => (
              <div key={g.key} className="rounded-lg border px-4 py-3">
                <div className="text-xs text-muted-foreground">{g.label}</div>
                <div
                  className={`mt-1 text-2xl font-semibold tabular-nums ${
                    g.error ? "text-destructive" : g.count ? "text-amber-600 dark:text-amber-400" : ""
                  }`}
                >
                  {g.error ? "!" : g.count}
                </div>
              </div>
            ))}
          </div>
        )}

        {data?.groups.map((g) =>
          g.error ? (
            <div key={g.key} className="rounded-lg bg-destructive/10 text-destructive px-4 py-3 text-sm">
              <span className="font-medium">{g.label} :</span> {g.error}
            </div>
          ) : g.items.length > 0 ? (
            <div key={g.key} className="space-y-1.5">
              <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{g.label}</h3>
              <ul className="divide-y rounded-lg border">
                {g.items.map((item) => {
                  const days = waitingDays(item.created_at);
                  return (
                    <li key={item.id} className="flex items-start gap-3 px-4 py-2.5">
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium">{item.title}</div>
                        {item.subtitle && (
                          <div className="truncate text-xs text-muted-foreground">{item.subtitle}</div>
                        )}
                      </div>
                      <div className="shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                        <div>{formatDate(item.created_at)}</div>
                        {days !== null && (
                          <div className={days > 30 ? "text-amber-600 dark:text-amber-400" : ""}>
                            {days === 0 ? "aujourd'hui" : `il y a ${days} j`}
                          </div>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null
        )}

        {data && total === 0 && !data.groups.some((g) => g.error) && (
          <p className="text-sm text-muted-foreground">Rien à valider 🎉</p>
        )}
      </CardContent>
    </Card>
  );
}
