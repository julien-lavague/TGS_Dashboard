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

export interface EquipmentItem {
  name: string;
  user: string;
}

export interface EquipmentCategory {
  type: string;
  items: EquipmentItem[];
}

export interface EquipmentSport {
  sport: string;
  categories: EquipmentCategory[];
}

export interface EquipmentNamesResponse {
  sports: EquipmentSport[];
}

export interface EquipmentCharStat {
  sport: string;
  level: string;
  type: string;
  spec: string;
  unit: string;
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface EquipmentCharacteristicsResponse {
  figures: Record<string, string>;
  stats: EquipmentCharStat[];
}
