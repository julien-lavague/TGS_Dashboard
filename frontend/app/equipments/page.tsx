"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TabBar } from "@/components/ui/TabBar";
import type { EquipmentNamesResponse, EquipmentCharacteristicsResponse, EquipmentCharStat } from "@/lib/types";

const TABS = [
  { id: "coverage", label: "Coverage" },
  { id: "by-type", label: "By Category" },
  { id: "names", label: "Equipment Names" },
  { id: "characteristics", label: "Characteristics" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const TYPE_LABELS: Record<string, string> = {
  wing: "Wing",
  foil: "Foil",
  kite: "Kite",
  board: "Board",
};

export default function EquipmentsPage() {
  const [segment, setSegment] = useState<Segment>("all");
  const [activeTab, setActiveTab] = useState<TabId>("coverage");

  const coverage = useQuery({
    queryKey: ["equipment-coverage", segment],
    queryFn: () => api.equipments.getCoverage(segment),
    enabled: activeTab === "coverage",
  });

  const byType = useQuery({
    queryKey: ["equipment-by-type", segment],
    queryFn: () => api.equipments.getByType(segment),
    enabled: activeTab === "by-type",
  });

  const names = useQuery({
    queryKey: ["equipment-names", segment],
    queryFn: () => api.equipments.getNames(segment),
    enabled: activeTab === "names",
  });

  const characteristics = useQuery({
    queryKey: ["equipment-characteristics", segment],
    queryFn: () => api.equipments.getCharacteristics(segment),
    enabled: activeTab === "characteristics",
  });

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Equipments</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Equipment coverage and distribution by sport
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === "coverage" && (
        <Card>
          <CardHeader>
            <CardTitle>Equipment Coverage by Sport & Level</CardTitle>
          </CardHeader>
          <CardContent className="h-[450px]">
            <ChartArea query={coverage} />
          </CardContent>
        </Card>
      )}

      {activeTab === "by-type" && (
        <Card>
          <CardHeader>
            <CardTitle>Equipment Count by Category & Sport</CardTitle>
          </CardHeader>
          <CardContent className="h-[450px]">
            <ChartArea query={byType} />
          </CardContent>
        </Card>
      )}

      {activeTab === "names" && (
        <EquipmentNamesList
          data={names.data}
          isLoading={names.isLoading}
          isError={names.isError}
        />
      )}

      {activeTab === "characteristics" && (
        <CharacteristicsTab
          data={characteristics.data}
          isLoading={characteristics.isLoading}
          isError={characteristics.isError}
        />
      )}
    </div>
  );
}

function CharacteristicsTab({
  data,
  isLoading,
  isError,
}: {
  data?: EquipmentCharacteristicsResponse;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) return <Placeholder text="Loading…" />;
  if (isError)
    return <Placeholder text="Failed to load — is the backend running?" error />;
  if (!data) return null;

  const types = Object.keys(data.figures);

  return (
    <div className="space-y-6">
      {types.map((eqType) => {
        const typeStats = data.stats.filter((s) => s.type === eqType);
        const unit = typeStats[0]?.unit ?? "";
        const label = TYPE_LABELS[eqType] ?? eqType;

        return (
          <Card key={eqType}>
            <CardHeader>
              <CardTitle>
                {label} — size distribution ({unit})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-[400px]">
                <PlotlyChart figure={data.figures[eqType]} className="h-full" />
              </div>
              <CharStatsTable stats={typeStats} />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function CharStatsTable({ stats }: { stats: EquipmentCharStat[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left pb-2 pr-4 font-medium text-muted-foreground">Sport</th>
            <th className="text-left pb-2 pr-4 font-medium text-muted-foreground">Level</th>
            <th className="text-right pb-2 pr-4 font-medium text-muted-foreground">n</th>
            <th className="text-right pb-2 pr-4 font-medium text-muted-foreground">Min</th>
            <th className="text-right pb-2 pr-4 font-medium text-muted-foreground">Max</th>
            <th className="text-right pb-2 pr-4 font-medium text-muted-foreground">Mean</th>
            <th className="text-right pb-2 font-medium text-muted-foreground">Median</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-muted/40">
              <td className="py-1.5 pr-4">{s.sport}</td>
              <td className="py-1.5 pr-4">
                <span className="inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {s.level}
                </span>
              </td>
              <td className="py-1.5 pr-4 text-right text-muted-foreground">{s.count}</td>
              <td className="py-1.5 pr-4 text-right">{s.min}</td>
              <td className="py-1.5 pr-4 text-right">{s.max}</td>
              <td className="py-1.5 pr-4 text-right">{s.mean}</td>
              <td className="py-1.5 text-right">{s.median}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EquipmentNamesList({
  data,
  isLoading,
  isError,
}: {
  data?: EquipmentNamesResponse;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading)
    return (
      <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  if (isError)
    return (
      <div className="flex items-center justify-center h-40 text-sm text-destructive">
        Failed to load — is the backend running?
      </div>
    );
  if (!data) return null;

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      {data.sports.map((sport) => (
        <Card key={sport.sport}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">{sport.sport}</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left pb-2 pr-4 font-medium text-muted-foreground w-24">
                    Category
                  </th>
                  <th className="text-left pb-2 font-medium text-muted-foreground">
                    Name
                  </th>
                  <th className="text-left pb-2 font-medium text-muted-foreground">
                    User
                  </th>
                </tr>
              </thead>
              <tbody>
                {sport.categories.map((cat) =>
                  cat.items.map((item, i) => (
                    <tr
                      key={`${cat.type}-${i}`}
                      className="border-b last:border-0 hover:bg-muted/40"
                    >
                      <td className="py-1.5 pr-4">
                        {i === 0 ? (
                          <span className="inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                            {cat.type}
                          </span>
                        ) : null}
                      </td>
                      <td className="py-1.5 pr-4">{item.name || "—"}</td>
                      <td className="py-1.5 text-muted-foreground text-xs">
                        {item.user}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}
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
