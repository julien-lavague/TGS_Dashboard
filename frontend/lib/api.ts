import axios from "axios";
import type { AlertsResponse, FigureResponse, UsersListResponse, AnonymousStatsResponse, SpotsPerProfileDetailResponse, ProfileCharacteristicsResponse, UserProfilesResponse, EquipmentNamesResponse, EquipmentDistributionResponse, EquipmentCharacteristicsResponse, EquipmentQuantityResponse, ReleaseNote, ReleaseNoteCreate, ReleaseNotesResponse, GcpStatusResponse } from "./types";
import type { Site } from "@/components/ui/SiteSelector";

const client = axios.create({ baseURL: "/api" });

export const api = {
  dashboard: {
    getGcpStatus: (refresh = false) =>
      client
        .get<GcpStatusResponse>("/dashboard/gcp-status", { params: refresh ? { refresh: true } : {} })
        .then((r) => r.data),
  },

  alerts: {
    getSchedule: (segment = "release") =>
      client
        .get<AlertsResponse>("/alerts/schedule", { params: { segment } })
        .then((r) => r.data),
  },

  overview: {
    getUserGrowth: (segment = "release") =>
      client
        .get<FigureResponse>("/overview/user-growth", { params: { segment } })
        .then((r) => r.data),
    getMessagesOverTime: (segment = "release") =>
      client
        .get<FigureResponse>("/overview/messages-over-time", {
          params: { segment },
        })
        .then((r) => r.data),
    startTopicAnalysis: (segment = "release") =>
      client
        .post<{ job_id: string }>("/overview/topic-analysis/start", null, {
          params: { segment },
        })
        .then((r) => r.data),
    getTopicAnalysisStatus: (jobId: string) =>
      client
        .get<{ status: string; results: Record<string, string> | null }>(
          `/overview/topic-analysis/status/${jobId}`
        )
        .then((r) => r.data),
  },

  profils: {
    getSpotDistribution: (segment = "release") =>
      client
        .get<FigureResponse>("/profils/spot-distribution", { params: { segment } })
        .then((r) => r.data),
    getSpotMap: (segment = "release") =>
      client
        .get<FigureResponse>("/profils/spot-map", { params: { segment } })
        .then((r) => r.data),
    getLevelBySport: (segment = "release") =>
      client
        .get<FigureResponse>("/profils/level-by-sport", { params: { segment } })
        .then((r) => r.data),
    getSpotsPerProfile: (segment = "release") =>
      client
        .get<FigureResponse>("/profils/spots-per-profile", { params: { segment } })
        .then((r) => r.data),
    getSpotsPerProfileDetail: (segment = "release") =>
      client
        .get<SpotsPerProfileDetailResponse>("/profils/spots-per-profile-detail", { params: { segment } })
        .then((r) => r.data),
    getCharacteristics: (segment = "release", groupBy = "level") =>
      client
        .get<ProfileCharacteristicsResponse>("/profils/characteristics", { params: { segment, group_by: groupBy } })
        .then((r) => r.data),
    getUserProfiles: (segment = "release") =>
      client
        .get<UserProfilesResponse>("/profils/user-profiles", { params: { segment } })
        .then((r) => r.data),
    getUserSpotMap: (segment = "release", email: string) =>
      client
        .get<FigureResponse>("/profils/user-spot-map", { params: { segment, email } })
        .then((r) => r.data),
  },

  users: {
    getList: () =>
      client.get<UsersListResponse>("/users/list").then((r) => r.data),
    getAnonymousStats: () =>
      client.get<AnonymousStatsResponse>("/users/anonymous-stats").then((r) => r.data),
  },

  equipments: {
    getCoverage: (segment = "all") =>
      client
        .get<FigureResponse>("/equipments/coverage", { params: { segment } })
        .then((r) => r.data),
    getByType: (segment = "all") =>
      client
        .get<FigureResponse>("/equipments/by-type", { params: { segment } })
        .then((r) => r.data),
    getNames: (segment = "all") =>
      client
        .get<EquipmentNamesResponse>("/equipments/names", { params: { segment } })
        .then((r) => r.data),
    getDistribution: (segment = "all") =>
      client
        .get<EquipmentDistributionResponse>("/equipments/distribution", { params: { segment } })
        .then((r) => r.data),
    getCharacteristics: (segment = "all") =>
      client
        .get<EquipmentCharacteristicsResponse>("/equipments/characteristics", { params: { segment } })
        .then((r) => r.data),
    getQuantityStats: (segment = "all") =>
      client
        .get<EquipmentQuantityResponse>("/equipments/quantity-stats", { params: { segment } })
        .then((r) => r.data),
  },

  system: {
    getHealth: () =>
      client.get<{ status: string }>("/system/health").then((r) => r.data),
    restart: () =>
      client.post<{ restarting: boolean }>("/system/restart").then((r) => r.data),
  },

  usage: {
    getPageViews: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/page-views", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getSessions: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/sessions", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getSessionsPerWeekSinceSignup: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/sessions-per-week-since-signup", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getTimeline: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/timeline", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getVisitDuration: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/visit-duration", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getDailyActiveUsers: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/daily-active-users", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getUserVisitsPareto: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/user-visits-pareto", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getVisitFrequency: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/visit-frequency", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getVisitorProfilesPareto: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/usage/visitor-profiles-pareto", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
  },

  widgets: {
    getElementUsage: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/element-usage", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getTimelineDepth: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/timeline-depth", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getCellClicks: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/cell-clicks", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getFilters: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/filters", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getPaywallFunnel: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/paywall-funnel", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
    getSailCatalog: (segment = "release", days?: number, site: Site = "prod") =>
      client
        .get<FigureResponse>("/widgets/sail-catalog", { params: { segment, site, ...(days !== undefined && { days }) } })
        .then((r) => r.data),
  },

  releaseNotes: {
    list: () =>
      client.get<ReleaseNotesResponse>("/release-notes").then((r) => r.data),
    create: (note: ReleaseNoteCreate) =>
      client.post<ReleaseNote>("/release-notes", note).then((r) => r.data),
    remove: (id: string) =>
      client.delete(`/release-notes/${id}`).then((r) => r.data),
    uploadImage: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return client
        .post<{ image_url: string }>("/release-notes/images", form)
        .then((r) => r.data);
    },
  },
};
