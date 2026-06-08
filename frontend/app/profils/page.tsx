"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TabBar } from "@/components/ui/TabBar";
import type { ProfileDetailUser } from "@/lib/types";

const TABS = [
  { id: "level-by-sport", label: "Level by Sport" },
  { id: "spots-per-profile", label: "Spots per Profile" },
  { id: "spot-distribution", label: "Spot Distribution" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ProfilsPage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [activeTab, setActiveTab] = useState<TabId>("level-by-sport");
  const [selectedSpotCount, setSelectedSpotCount] = useState<number | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const levelBySport = useQuery({
    queryKey: ["level-by-sport", segment],
    queryFn: () => api.profils.getLevelBySport(segment),
    enabled: activeTab === "level-by-sport",
  });

  const spotsPerProfile = useQuery({
    queryKey: ["spots-per-profile", segment],
    queryFn: () => api.profils.getSpotsPerProfile(segment),
    enabled: activeTab === "spots-per-profile",
  });

  const spotsPerProfileDetail = useQuery({
    queryKey: ["spots-per-profile-detail", segment],
    queryFn: () => api.profils.getSpotsPerProfileDetail(segment),
    enabled: activeTab === "spots-per-profile",
  });

  const spotDistribution = useQuery({
    queryKey: ["spot-distribution", segment],
    queryFn: () => api.profils.getSpotDistribution(segment),
    enabled: activeTab === "spot-distribution",
  });

  function handleBarClick(spotCount: number) {
    if (selectedSpotCount === spotCount) {
      setSelectedSpotCount(null);
    } else {
      setSelectedSpotCount(spotCount);
      setDetailOpen(true);
    }
  }

  function handleTabChange(tab: TabId) {
    setActiveTab(tab);
    if (tab !== "spots-per-profile") {
      setSelectedSpotCount(null);
      setDetailOpen(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">User Profiles</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Typology and preferences of active users
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      <TabBar tabs={TABS} active={activeTab} onChange={handleTabChange} />

      {/* Tab panels */}
      {activeTab === "level-by-sport" && (
        <Card>
          <CardHeader>
            <CardTitle>Level Distribution by Sport</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={levelBySport} />
          </CardContent>
        </Card>
      )}

      {activeTab === "spots-per-profile" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Number of Spots per Profile</CardTitle>
            </CardHeader>
            <CardContent className="h-[400px]">
              {spotsPerProfile.isLoading && <Placeholder text="Loading…" />}
              {spotsPerProfile.isError && (
                <Placeholder text="Failed to load — is the backend running?" error />
              )}
              {spotsPerProfile.data && (
                <PlotlyChart
                  figure={spotsPerProfile.data.figure}
                  className="h-full"
                  onBarClick={handleBarClick}
                />
              )}
            </CardContent>
          </Card>

          <SpotsPerProfileDetail
            users={spotsPerProfileDetail.data?.users}
            isLoading={spotsPerProfileDetail.isLoading}
            selectedSpotCount={selectedSpotCount}
            onClearFilter={() => setSelectedSpotCount(null)}
            open={detailOpen}
            setOpen={setDetailOpen}
          />
        </div>
      )}

      {activeTab === "spot-distribution" && (
        <Card>
          <CardHeader>
            <CardTitle>Spot Distribution in Profiles</CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100vh-260px)]">
            <ChartArea query={spotDistribution} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SpotsPerProfileDetail({
  users,
  isLoading,
  selectedSpotCount,
  onClearFilter,
  open,
  setOpen,
}: {
  users?: ProfileDetailUser[];
  isLoading: boolean;
  selectedSpotCount: number | null;
  onClearFilter: () => void;
  open: boolean;
  setOpen: (v: boolean) => void;
}) {
  const [view, setView] = useState<"users" | "spots">("users");

  const filteredUsers = useMemo(() => {
    if (!users) return [];
    if (selectedSpotCount === null) return users;
    return users.filter((u) => u.spot_count === selectedSpotCount);
  }, [users, selectedSpotCount]);

  const spotRows = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const u of filteredUsers) {
      for (const s of u.spots) {
        counts[s] = (counts[s] ?? 0) + 1;
      }
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [filteredUsers]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <CardTitle className="text-base font-medium text-muted-foreground">
            Detail
          </CardTitle>
          {selectedSpotCount !== null && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {selectedSpotCount} spot{selectedSpotCount !== 1 ? "s" : ""}
              <button
                onClick={onClearFilter}
                className="hover:text-destructive leading-none"
                aria-label="Clear filter"
              >
                ×
              </button>
            </span>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={isLoading || !users}
          onClick={() => setOpen(!open)}
        >
          {open ? "Hide" : "Show details"}
        </Button>
      </CardHeader>

      {open && users && (
        <CardContent>
          <div className="flex gap-2 mb-4">
            <Button
              variant={view === "users" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("users")}
            >
              Users ({filteredUsers.length})
            </Button>
            <Button
              variant={view === "spots" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("spots")}
            >
              Spots ({spotRows.length})
            </Button>
          </div>

          <div className="max-h-80 overflow-y-auto rounded border">
            {view === "users" ? (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium">Email</th>
                    <th className="text-right px-3 py-2 font-medium">Nb spots</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr key={u.email} className="border-b last:border-0 hover:bg-muted/40">
                      <td className="px-3 py-1.5 text-muted-foreground">{u.email}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">{u.spot_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium">Spot</th>
                    <th className="text-right px-3 py-2 font-medium">Nb profiles</th>
                  </tr>
                </thead>
                <tbody>
                  {spotRows.map((s) => (
                    <tr key={s.name} className="border-b last:border-0 hover:bg-muted/40">
                      <td className="px-3 py-1.5 text-muted-foreground">{s.name}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">{s.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </CardContent>
      )}
    </Card>
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
