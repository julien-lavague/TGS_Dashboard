export interface AlertRow {
  email: string;
  name: string;
  question: string;
  is_active: boolean;
  day: string | null;
  time: string | null;
}

export interface AlertsResponse {
  rows: AlertRow[];
}

export interface PlotlyFigure {
  data: object[];
  layout: object;
  config?: object;
}

export interface FigureResponse {
  figure: string; // JSON-encoded Plotly figure
}

export interface UsersListResponse {
  segments: Record<string, string[]>;
}

export interface ProfileDetailUser {
  email: string;
  spot_count: number;
  spots: string[];
}

export interface SpotsPerProfileDetailResponse {
  users: ProfileDetailUser[];
}
