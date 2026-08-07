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

export interface AnonymousStatsResponse {
  session_count: number;
  page_view_count: number;
  last_seen: string | null;
}

export interface ProfileDetailUser {
  email: string;
  spot_count: number;
  spots: string[];
}

export interface SpotsPerProfileDetailResponse {
  users: ProfileDetailUser[];
}

export interface ProfileCharParam {
  key: string;
  label: string;
  unit: string;
  kind: "numeric" | "categorical" | "activation";
  table_secondary_label?: string;
}

export interface ProfileCharStat {
  param: string;
  unit: string;
  primary: string;
  secondary: string;
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface ProfileCharacteristicsResponse {
  group_by: string;
  primary_label: string;
  secondary_label: string;
  params: ProfileCharParam[];
  figures: Record<string, string>;
  stats: ProfileCharStat[];
}

export interface UserProfileWind {
  enabled: boolean;
  min: number | null;
  max: number | null;
  gusts_min: number | null;
  gusts: number | null;
  directions: string[];
}

export interface UserProfileWaves {
  enabled: boolean;
  max_height: number | null;
  period_min: number | null;
  period_max: number | null;
  directions: string[];
}

export interface UserProfileTide {
  enabled: boolean;
  rising: boolean;
  decreasing: boolean;
  low_tide_avoid: number | null;
  high_tide_avoid: number | null;
}

export interface UserProfileEquipment {
  type: string | null;
  size: number | null;
  enabled: boolean;
}

export interface UserProfile {
  sport: string;
  level: string;
  weight: number | null;
  wind: UserProfileWind;
  waves: UserProfileWaves;
  tide: UserProfileTide;
  spots: string[];
  equipment: UserProfileEquipment[];
}

export interface UserProfileRecord {
  email: string;
  profiles: UserProfile[];
}

export interface UserProfilesResponse {
  users: UserProfileRecord[];
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

export interface EquipmentQuantityStat {
  sport: string;
  level: string;
  type: string;
  user_count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface EquipmentQuantityResponse {
  figure: string;
  stats: EquipmentQuantityStat[];
}
