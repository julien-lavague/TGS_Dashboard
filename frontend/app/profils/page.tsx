"use client";

import { useState, useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PlotlyChart } from "@/components/charts/PlotlyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";
import { TabBar } from "@/components/ui/TabBar";
import type { ProfileDetailUser, ProfileCharacteristicsResponse, ProfileCharStat, UserProfilesResponse, UserProfile } from "@/lib/types";

const TABS = [
  { id: "level-by-sport", label: "Level by Sport" },
  { id: "spots-per-profile", label: "Spots per Profile" },
  { id: "spot-distribution", label: "Spot Distribution" },
  { id: "spot-map", label: "Carte des spots" },
  { id: "characteristics", label: "Caractéristiques" },
  { id: "user-detail", label: "Fiche utilisateur" },
] as const;

type TabId = (typeof TABS)[number]["id"];

type GroupBy = "sport" | "spot";

export default function ProfilsPage() {
  const [segment, setSegment] = useState<Segment>("release");
  const [activeTab, setActiveTab] = useState<TabId>("level-by-sport");
  const [selectedSpotCount, setSelectedSpotCount] = useState<number | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [groupBy, setGroupBy] = useState<GroupBy>("sport");

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

  const spotMap = useQuery({
    queryKey: ["spot-map", segment],
    queryFn: () => api.profils.getSpotMap(segment),
    enabled: activeTab === "spot-map",
  });

  const characteristics = useQuery({
    queryKey: ["profile-characteristics", segment, groupBy],
    queryFn: () => api.profils.getCharacteristics(segment, groupBy),
    enabled: activeTab === "characteristics",
  });

  const userProfiles = useQuery({
    queryKey: ["user-profiles", segment],
    queryFn: () => api.profils.getUserProfiles(segment),
    enabled: activeTab === "user-detail",
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

      {activeTab === "spot-map" && (
        <Card>
          <CardHeader>
            <CardTitle>Carte des spots favoris</CardTitle>
          </CardHeader>
          <CardContent className="h-[600px] p-0 overflow-hidden rounded-b-lg">
            {spotMap.isLoading && <Placeholder text="Loading…" />}
            {spotMap.isError && (
              <Placeholder text="Failed to load — is the backend running?" error />
            )}
            {spotMap.data && <PlotlyChart figure={spotMap.data.figure} className="h-full" />}
          </CardContent>
        </Card>
      )}

      {activeTab === "characteristics" && (
        <CharacteristicsTab
          data={characteristics.data}
          isLoading={characteristics.isLoading}
          isError={characteristics.isError}
          groupBy={groupBy}
          onGroupByChange={setGroupBy}
        />
      )}

      {activeTab === "user-detail" && (
        <UserDetailTab
          data={userProfiles.data}
          isLoading={userProfiles.isLoading}
          isError={userProfiles.isError}
        />
      )}
    </div>
  );
}

function UserDetailTab({
  data,
  isLoading,
  isError,
}: {
  data?: UserProfilesResponse;
  isLoading: boolean;
  isError: boolean;
}) {
  const [email, setEmail] = useState<string>("");

  const selected = useMemo(
    () => data?.users.find((u) => u.email === email),
    [data, email]
  );

  if (isLoading) return <Placeholder text="Loading…" />;
  if (isError) return <Placeholder text="Failed to load — is the backend running?" error />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sélectionner un utilisateur</CardTitle>
        </CardHeader>
        <CardContent>
          <select
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full max-w-md rounded-md border bg-background px-3 py-2 text-sm"
          >
            <option value="">— Choisir un utilisateur ({data.users.length}) —</option>
            {data.users.map((u) => (
              <option key={u.email} value={u.email}>
                {u.email} ({u.profiles.length} profil{u.profiles.length > 1 ? "s" : ""})
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      {!selected && (
        <Placeholder text="Choisissez un utilisateur pour afficher ses profils." />
      )}

      {selected &&
        selected.profiles.map((profile, i) => (
          <UserProfileCard key={`${profile.sport}-${i}`} profile={profile} />
        ))}
    </div>
  );
}

function UserProfileCard({ profile }: { profile: UserProfile }) {
  const { wind, waves, tide } = profile;
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-3">
          {profile.sport}
          <span className="inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            {profile.level}
          </span>
        </CardTitle>
        {profile.weight != null && (
          <span className="text-sm text-muted-foreground">Poids : {profile.weight} kg</span>
        )}
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <ModulePanel title="Vent" enabled={wind.enabled}>
          <FieldRow label="Vent moyen" value={rangeText(wind.min, wind.max, "kn")} />
          <FieldRow label="Rafales" value={rangeText(wind.gusts_min, wind.gusts, "kn")} />
          <ChipRow label="Orientations" values={wind.directions} />
        </ModulePanel>

        <ModulePanel title="Vagues" enabled={waves.enabled}>
          <FieldRow label="Hauteur max" value={numText(waves.max_height, "m")} />
          <FieldRow label="Période" value={rangeText(waves.period_min, waves.period_max, "s")} />
          <ChipRow label="Orientations" values={waves.directions} />
        </ModulePanel>

        <ModulePanel title="Marée" enabled={tide.enabled}>
          <FieldRow label="Montante" value={tide.rising ? "Oui" : "Non"} />
          <FieldRow label="Descendante" value={tide.decreasing ? "Oui" : "Non"} />
          <FieldRow label="Éviter marée basse" value={numText(tide.low_tide_avoid, "h")} />
          <FieldRow label="Éviter marée haute" value={numText(tide.high_tide_avoid, "h")} />
        </ModulePanel>
      </CardContent>

      <CardContent className="grid gap-4 md:grid-cols-2 pt-0">
        <div>
          <p className="text-sm font-medium mb-2">Spots favoris ({profile.spots.length})</p>
          {profile.spots.length ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.spots.map((s) => (
                <span key={s} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs">
                  {s}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">—</p>
          )}
        </div>
        <div>
          <p className="text-sm font-medium mb-2">Équipement ({profile.equipment.length})</p>
          {profile.equipment.length ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.equipment.map((e, i) => (
                <span
                  key={i}
                  className={`inline-block rounded-full px-2 py-0.5 text-xs ${
                    e.enabled ? "bg-muted" : "bg-muted/50 text-muted-foreground line-through"
                  }`}
                >
                  {e.type ?? "?"}
                  {e.size != null ? ` · ${e.size}` : ""}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">—</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ModulePanel({
  title,
  enabled,
  children,
}: {
  title: string;
  enabled: boolean;
  children: ReactNode;
}) {
  return (
    <div className={`rounded-lg border p-3 ${enabled ? "" : "opacity-50"}`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium">{title}</p>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
            enabled ? "bg-green-500/15 text-green-600" : "bg-muted text-muted-foreground"
          }`}
        >
          {enabled ? "Activé" : "Désactivé"}
        </span>
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}

function ChipRow({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="mt-1 flex flex-wrap gap-1">
        {values.length ? (
          values.map((v) => (
            <span key={v} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs">
              {v}
            </span>
          ))
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </div>
    </div>
  );
}

function rangeText(min: number | null, max: number | null, unit: string): string {
  if (min == null && max == null) return "—";
  if (min != null && max != null) return `${min} – ${max} ${unit}`;
  return `${min ?? max} ${unit}`;
}

function numText(v: number | null, unit: string): string {
  return v == null ? "—" : `${v} ${unit}`;
}

function CharacteristicsTab({
  data,
  isLoading,
  isError,
  groupBy,
  onGroupByChange,
}: {
  data?: ProfileCharacteristicsResponse;
  isLoading: boolean;
  isError: boolean;
  groupBy: GroupBy;
  onGroupByChange: (g: GroupBy) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Regrouper par :</span>
        <div className="flex gap-2">
          <Button
            variant={groupBy === "sport" ? "default" : "outline"}
            size="sm"
            onClick={() => onGroupByChange("sport")}
          >
            Sport
          </Button>
          <Button
            variant={groupBy === "spot" ? "default" : "outline"}
            size="sm"
            onClick={() => onGroupByChange("spot")}
          >
            Spot
          </Button>
        </div>
      </div>

      {isLoading && <Placeholder text="Loading…" />}
      {isError && <Placeholder text="Failed to load — is the backend running?" error />}

      {data &&
        data.params.map((param) => {
          const figure = data.figures[param.key];
          if (!figure) return null;
          const paramStats = data.stats.filter((s) => s.param === param.key);
          // Give per-spot box plots room to breathe (one row of boxes per spot).
          const primaryCount = new Set(paramStats.map((s) => s.primary)).size;
          const chartHeight =
            param.kind === "numeric" && groupBy === "spot"
              ? Math.max(400, primaryCount * 34 + 140)
              : 420;

          return (
            <Card key={param.key}>
              <CardHeader>
                <CardTitle>
                  {param.label}
                  {param.unit ? ` (${param.unit})` : ""}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div style={{ height: chartHeight }}>
                  <PlotlyChart figure={figure} className="h-full" />
                </div>
                {param.kind === "numeric" && paramStats.length > 0 && (
                  <ProfileCharStatsTable
                    stats={paramStats}
                    primaryLabel={data.primary_label}
                    secondaryLabel={param.table_secondary_label ?? data.secondary_label}
                  />
                )}
              </CardContent>
            </Card>
          );
        })}
    </div>
  );
}

function ProfileCharStatsTable({
  stats,
  primaryLabel,
  secondaryLabel,
}: {
  stats: ProfileCharStat[];
  primaryLabel: string;
  secondaryLabel: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left pb-2 pr-4 font-medium text-muted-foreground">{primaryLabel}</th>
            <th className="text-left pb-2 pr-4 font-medium text-muted-foreground">{secondaryLabel}</th>
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
              <td className="py-1.5 pr-4">{s.primary}</td>
              <td className="py-1.5 pr-4">
                <span className="inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {s.secondary}
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
