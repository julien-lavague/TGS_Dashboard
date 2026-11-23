"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TimeRangeSelector, type TimeRange, DAYS_FOR_RANGE } from "@/components/ui/TimeRangeSelector";
import { SiteSelector, type Site } from "@/components/ui/SiteSelector";
import { TabBar } from "@/components/ui/TabBar";

const TABS = [
  { id: "element-usage", label: "Usage par élément" },
  { id: "timeline-depth", label: "Profondeur timeline" },
  { id: "cell-clicks", label: "Clics scores" },
  { id: "filters", label: "Filtres" },
  { id: "paywall-funnel", label: "Premium" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const TITLES: Record<TabId, string> = {
  "element-usage": "Part des visites de /sessions qui utilisent chaque élément",
  "timeline-depth": "Jusqu'où la timeline est parcourue",
  "cell-clicks": "Clics sur les scores individuels",
  "filters": "Filtre de score et mode de vue",
  "paywall-funnel": "Incitations Premium : vue → clic → pricing → abonnement",
};

const FETCHERS: Record<TabId, (segment: Segment, days?: number, site?: Site) => Promise<{ figure: string }>> = {
  "element-usage": api.widgets.getElementUsage,
  "timeline-depth": api.widgets.getTimelineDepth,
  "cell-clicks": api.widgets.getCellClicks,
  "filters": api.widgets.getFilters,
  "paywall-funnel": api.widgets.getPaywallFunnel,
};

export default function WidgetsPage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [timeRange, setTimeRange] = useState<TimeRange>("14d");
  const [site, setSite] = useState<Site>("prod");
  const [activeTab, setActiveTab] = useState<TabId>("element-usage");

  const days = DAYS_FOR_RANGE[timeRange];

  const query = useQuery({
    queryKey: ["widgets", activeTab, segment, timeRange, site],
    queryFn: () => FETCHERS[activeTab](segment, days, site),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Widgets</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Interactions sur la page sessions (table ui_events), visiteurs anonymes compris
          </p>
        </div>
        <div className="flex gap-3 items-center flex-wrap md:justify-end">
          <SiteSelector value={site} onChange={setSite} />
          <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          <SegmentSelector value={segment} onChange={setSegment} />
        </div>
      </div>

      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      <Card>
        <CardHeader>
          <CardTitle>{TITLES[activeTab]}</CardTitle>
        </CardHeader>
        {/* Usage par élément : une barre par élément, la figure grandit avec la liste */}
        <CardContent className="h-[65vh] min-h-[380px] md:h-[calc(100vh-260px)] overflow-y-auto">
          {query.isPending ? (
            <Placeholder text="Loading…" />
          ) : query.isError ? (
            <Placeholder text="Failed to load — is the backend running?" error />
          ) : (
            <PlotlyChart
              figure={query.data.figure}
              className={activeTab === "element-usage" ? "w-full" : "h-full"}
            />
          )}
        </CardContent>
      </Card>
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
