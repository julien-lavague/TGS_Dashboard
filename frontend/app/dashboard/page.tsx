"use client";

import { GcpStatusWidget } from "@/components/dashboard/GcpStatusWidget";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">État de santé de l&apos;infrastructure TheGoodSpots</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
        <GcpStatusWidget />
      </div>
    </div>
  );
}
