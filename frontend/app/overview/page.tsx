"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TabBar } from "@/components/ui/TabBar";

const TABS = [
  { id: "user-growth", label: "User Growth" },
  { id: "topic-analysis", label: "Topic Analysis" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function OverviewPage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [activeTab, setActiveTab] = useState<TabId>("user-growth");
  const [jobId, setJobId] = useState<string | null>(null);

  const userGrowth = useQuery({
    queryKey: ["user-growth", segment],
    queryFn: () => api.overview.getUserGrowth(segment),
    enabled: activeTab === "user-growth",
  });

  const startAnalysis = useMutation({
    mutationFn: () => api.overview.startTopicAnalysis(segment),
    onSuccess: (data) => setJobId(data.job_id),
  });

  const analysisStatus = useQuery({
    queryKey: ["topic-analysis", jobId],
    queryFn: () => api.overview.getTopicAnalysisStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 3000 : false,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Overview</h1>
          <p className="text-muted-foreground text-sm mt-1">
            User growth and engagement metrics
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === "user-growth" && (
        <Card>
          <CardHeader>
            <CardTitle>New Users Per Week</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            {userGrowth.isLoading && <Placeholder text="Loading…" />}
            {userGrowth.isError && (
              <Placeholder text="Failed to load — is the backend running?" error />
            )}
            {userGrowth.data && (
              <PlotlyChart figure={userGrowth.data.figure} className="h-full" />
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "topic-analysis" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              Topic Analysis
              {analysisStatus.data?.status === "running" && (
                <Badge variant="secondary">Analyzing…</Badge>
              )}
              {analysisStatus.data?.status === "done" && <Badge>Done</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!jobId && (
              <Button
                onClick={() => startAnalysis.mutate()}
                disabled={startAnalysis.isPending}
              >
                {startAnalysis.isPending ? "Starting…" : "Run Analysis"}
              </Button>
            )}
            {analysisStatus.data?.status === "running" && (
              <p className="text-sm text-muted-foreground">
                Analyzing topics… this may take ~30 seconds.
              </p>
            )}
            {analysisStatus.data?.status === "done" &&
              analysisStatus.data.results &&
              Object.entries(analysisStatus.data.results).map(([email, text]) => (
                <div key={email} className="rounded-md border p-4 space-y-2">
                  <p className="font-mono text-xs text-muted-foreground">{email}</p>
                  <p className="text-sm whitespace-pre-wrap">{text}</p>
                </div>
              ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
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
