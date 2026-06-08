import axios from "axios";
import type { AlertsResponse, FigureResponse, UsersListResponse, SpotsPerProfileDetailResponse } from "./types";

const client = axios.create({ baseURL: "/api" });

export const api = {
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
  },

  users: {
    getList: () =>
      client.get<UsersListResponse>("/users/list").then((r) => r.data),
  },

  usage: {
    getPageViews: (segment = "release") =>
      client
        .get<FigureResponse>("/usage/page-views", { params: { segment } })
        .then((r) => r.data),
    getSessions: (segment = "release") =>
      client
        .get<FigureResponse>("/usage/sessions", { params: { segment } })
        .then((r) => r.data),
    getSessionsPerWeekSinceSignup: (segment = "release") =>
      client
        .get<FigureResponse>("/usage/sessions-per-week-since-signup", { params: { segment } })
        .then((r) => r.data),
    getTimeline: (segment = "release") =>
      client
        .get<FigureResponse>("/usage/timeline", { params: { segment } })
        .then((r) => r.data),
  },
};
