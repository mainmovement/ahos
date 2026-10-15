export type Localized = { fa: string; en: string };
export type DataStatus = "LIVE" | "STALE" | "UNKNOWN" | "UNAVAILABLE" | "DEMO";
export type Provenance = {
  source: string;
  retrievedAt: string;
  status: DataStatus;
};
export type Metric = {
  id: string;
  title: Localized;
  value: string;
  change: string;
  note: Localized;
  tone: "gold" | "cyan" | "green" | "danger";
  trend: number[];
};
export type MarketAsset = {
  symbol: string;
  name: Localized;
  category: "crypto" | "gold" | "oil" | "us" | "eu" | "asia";
  price: number;
  change: number;
  volume: string;
  freshness: "DEMO" | "STALE" | "UNKNOWN";
  history: number[];
  unit: string;
};
export type Candle = {
  time: string;
  open: number;
  close: number;
  low: number;
  high: number;
  volume: number;
};
export type AgentState =
  "registered" | "running" | "blocked" | "failed" | "planned";
export type Agent = {
  id: string;
  name: Localized;
  role: Localized;
  department: Localized;
  state: AgentState;
  implementation: Localized;
  task: Localized;
  activityAt: string;
  evidence: string;
  progress: number;
};
export type Alert = {
  id: string;
  title: Localized;
  body: Localized;
  severity: "warning" | "unknown" | "info";
  time: string;
};
export type NewsItem = {
  id: string;
  title: Localized;
  category: Localized;
  verification: "verified" | "unverified" | "conflicting";
  time: string;
  sources: number;
  body: Localized;
};
export type Position = {
  id: string;
  symbol: string;
  quantity: number;
  entry: number;
  mark: number;
  risk: number;
};
export type DashboardSnapshot = {
  provenance: Provenance;
  metrics: Metric[];
  agents: Agent[];
  alerts: Alert[];
  news: NewsItem[];
  positions: Position[];
  system: { name: string; value: number; unit: string }[];
  university: {
    passed: number;
    failed: number;
    queued: number;
    courses: Localized[];
  };
};
export type DemoAnswer = { answer: Localized; source: string };

export type WorkspaceRow = { id: string; cells: (string | Localized)[]; state: string; detail: Localized };
export type WorkspaceTab = { id: string; title: Localized; columns: Localized[]; rows: WorkspaceRow[] };
export type WorkspaceData = { id: string; description: Localized; metrics: { label: Localized; value: string; note: Localized }[]; tabs: WorkspaceTab[]; note: Localized };
