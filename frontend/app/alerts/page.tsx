"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AlertsTable } from "@/components/tables/AlertsTable";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";

export default function AlertsPage() {
  const [segment, setSegment] = useState<Segment>("release");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["alerts-schedule", segment],
    queryFn: () => api.alerts.getSchedule(segment),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Scheduled alerts per user — day and time breakdown
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      {isLoading && (
        <div className="text-sm text-muted-foreground">Loading alerts…</div>
      )}
      {isError && (
        <div className="text-sm text-destructive">
          Failed to load alerts. Make sure the backend is running on port 8000.
        </div>
      )}
      {data && <AlertsTable rows={data.rows} />}
    </div>
  );
}
