"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TabBar } from "@/components/ui/TabBar";

const TABS = [
  { id: "page-views", label: "Page Views" },
  { id: "sessions", label: "Sessions" },
  { id: "sessions-since-signup", label: "Sessions / Signup" },
  { id: "timeline", label: "Timeline" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function UsagePage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [activeTab, setActiveTab] = useState<TabId>("page-views");

  const pageViews = useQuery({
    queryKey: ["page-views", segment],
    queryFn: () => api.usage.getPageViews(segment),
    enabled: activeTab === "page-views",
  });

  const sessions = useQuery({
    queryKey: ["sessions", segment],
    queryFn: () => api.usage.getSessions(segment),
    enabled: activeTab === "sessions",
  });

  const sessionsPerWeek = useQuery({
    queryKey: ["sessions-per-week-since-signup", segment],
    queryFn: () => api.usage.getSessionsPerWeekSinceSignup(segment),
    enabled: activeTab === "sessions-since-signup",
  });

  const timeline = useQuery({
    queryKey: ["timeline", segment],
    queryFn: () => api.usage.getTimeline(segment),
    enabled: activeTab === "timeline",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">User Usage</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Page views, sessions, and time-on-page analytics
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === "page-views" && (
        <Card>
          <CardHeader>
            <CardTitle>Page Views by Type Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={pageViews} />
          </CardContent>
        </Card>
      )}

      {activeTab === "sessions" && (
        <Card>
          <CardHeader>
            <CardTitle>Sessions per User Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={sessions} />
          </CardContent>
        </Card>
      )}

      {activeTab === "sessions-since-signup" && (
        <Card>
          <CardHeader>
            <CardTitle>Sessions per Week Since Signup</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={sessionsPerWeek} />
          </CardContent>
        </Card>
      )}

      {activeTab === "timeline" && (
        <Card>
          <CardHeader>
            <CardTitle>Page Duration Timeline</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={timeline} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ChartArea({ query }: { query: ReturnType<typeof useQuery<{ figure: string }>> }) {
  if (query.isLoading) return <Placeholder text="Loading…" />;
  if (query.isError) return <Placeholder text="Failed to load — is the backend running?" error />;
  if (query.data) return <PlotlyChart figure={query.data.figure} className="h-full" />;
  return null;
}

function Placeholder({ text, error }: { text: string; error?: boolean }) {
  return (
    <div
      className={`flex items-center justify-center h-full text-sm ${
        error ? "text-destructive" : "text-muted-foreground"
      }`}
    >
      {text}
    </div>
  );
}
