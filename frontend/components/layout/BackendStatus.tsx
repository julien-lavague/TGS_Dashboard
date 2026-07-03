"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function BackendStatus() {
  const queryClient = useQueryClient();
  const [restarting, setRestarting] = useState(false);

  const { data, isError } = useQuery({
    queryKey: ["system-health"],
    queryFn: api.system.getHealth,
    // Poll continuously so the dot reflects live availability.
    refetchInterval: restarting ? 1000 : 5000,
    staleTime: 0,
    retry: false,
  });

  const online = !!data && !isError;

  async function handleRestart() {
    if (restarting) return;
    setRestarting(true);
    try {
      await api.system.restart();
    } catch {
      // The request itself may be cut off as the server tears down — that's expected.
    }
    // Poll until the backend answers /health again, then stop the "restarting" state.
    const start = Date.now();
    const timer = setInterval(async () => {
      try {
        await api.system.getHealth();
        clearInterval(timer);
        setRestarting(false);
        queryClient.invalidateQueries();
      } catch {
        if (Date.now() - start > 30_000) {
          clearInterval(timer);
          setRestarting(false);
        }
      }
    }, 1000);
  }

  return (
    <div className="border-t px-3 py-3 space-y-2">
      <div className="flex items-center gap-2 px-1 text-xs text-muted-foreground">
        <span
          className={`inline-block size-2 rounded-full ${
            restarting
              ? "bg-amber-400 animate-pulse"
              : online
                ? "bg-emerald-500"
                : "bg-red-500"
          }`}
        />
        <span>
          Backend:{" "}
          {restarting ? "restarting…" : online ? "online" : "offline"}
        </span>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="w-full"
        disabled={restarting}
        onClick={handleRestart}
      >
        {restarting ? "Restarting…" : "Restart backend"}
      </Button>
    </div>
  );
}
