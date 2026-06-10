"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TimeRangeSelector, type TimeRange, DAYS_FOR_RANGE } from "@/components/ui/TimeRangeSelector";
import { TabBar } from "@/components/ui/TabBar";

const TABS = [
  { id: "page-views", label: "Page Views" },
  { id: "sessions", label: "Sessions" },
  { id: "daily-active-users", label: "Daily Active Users" },
  { id: "sessions-since-signup", label: "Sessions / Signup" },
  { id: "visit-duration", label: "Visit Duration" },
  { id: "timeline", label: "Timeline" },
  { id: "user-visits-pareto", label: "User Visits" },
  { id: "visit-frequency", label: "Visit Frequency" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function UsagePage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [timeRange, setTimeRange] = useState<TimeRange>("all");
  const [activeTab, setActiveTab] = useState<TabId>("page-views");

  const days = DAYS_FOR_RANGE[timeRange];

  const pageViews = useQuery({
    queryKey: ["page-views", segment, timeRange],
    queryFn: () => api.usage.getPageViews(segment, days),
    enabled: activeTab === "page-views",
  });

  const sessions = useQuery({
    queryKey: ["sessions", segment, timeRange],
    queryFn: () => api.usage.getSessions(segment, days),
    enabled: activeTab === "sessions",
  });

  const sessionsPerWeek = useQuery({
    queryKey: ["sessions-per-week-since-signup", segment, timeRange],
    queryFn: () => api.usage.getSessionsPerWeekSinceSignup(segment, days),
    enabled: activeTab === "sessions-since-signup",
  });

  const visitDuration = useQuery({
    queryKey: ["visit-duration", segment, timeRange],
    queryFn: () => api.usage.getVisitDuration(segment, days),
    enabled: activeTab === "visit-duration",
  });

  const dailyActiveUsers = useQuery({
    queryKey: ["daily-active-users", segment, timeRange],
    queryFn: () => api.usage.getDailyActiveUsers(segment, days),
    enabled: activeTab === "daily-active-users",
  });

  const timeline = useQuery({
    queryKey: ["timeline", segment, timeRange],
    queryFn: () => api.usage.getTimeline(segment, days),
    enabled: activeTab === "timeline",
  });

  const userVisitsPareto = useQuery({
    queryKey: ["user-visits-pareto", segment, timeRange],
    queryFn: () => api.usage.getUserVisitsPareto(segment, days),
    enabled: activeTab === "user-visits-pareto",
  });

  const visitFrequency = useQuery({
    queryKey: ["visit-frequency", segment, timeRange],
    queryFn: () => api.usage.getVisitFrequency(segment, days),
    enabled: activeTab === "visit-frequency",
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
        <div className="flex gap-3 items-center flex-wrap justify-end">
          <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          <SegmentSelector value={segment} onChange={setSegment} />
        </div>
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

      {activeTab === "daily-active-users" && (
        <Card>
          <CardHeader>
            <CardTitle>
              Signed-in Users &amp; Visitors per{" "}
              {timeRange === "all" ? "Month" : timeRange === "30d" ? "Week" : "Day"}
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={dailyActiveUsers} />
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

      {activeTab === "visit-duration" && (
        <Card>
          <CardHeader>
            <CardTitle>Visit Duration by Page Type</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={visitDuration} />
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

      {activeTab === "user-visits-pareto" && (
        <Card>
          <CardHeader>
            <CardTitle>User Day Visits — Pareto</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={userVisitsPareto} />
          </CardContent>
        </Card>
      )}

      {activeTab === "visit-frequency" && (
        <Card>
          <CardHeader>
            <CardTitle>Visit Frequency per User</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={visitFrequency} />
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
