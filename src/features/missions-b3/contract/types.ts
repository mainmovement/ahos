export type TruthStatus =
  | "LIVE"
  | "STALE"
  | "UNKNOWN"
  | "DEMO"
  | "CONFLICT"
  | "REJECTED"
  | "UNAVAILABLE"
  | "PARTIAL"
  | "PLANNED"
  | "MISSING"
  | "ERROR";

export type RecordState = "DONE" | "PARTIAL" | "NOT STARTED" | "UNKNOWN";
export type MissionState = "DONE" | "PARTIAL" | "NOT STARTED";
export type UnseenResult = "PASS" | "FAIL" | "NOT_RUN";

export interface SnapshotBase {
  executionMode: string | null;
  realTrading: boolean | null;
  source: string | null;
  generatedAt: string | null;
  demo: boolean;
  availability: "AVAILABLE" | "UNAVAILABLE";
  unavailableReason?: string;
}

export interface ServiceRecord {
  demo: boolean;
  name: string;
  status: TruthStatus;
  lastHeartbeat: string | null;
  version: string | null;
  uptimeSeconds: number | null;
}

export interface FaultRecord {
  demo: boolean;
  id: string;
  time: string | null;
  faultType: string;
  targetService: string;
  expected: string;
  observed: string | null;
  recovered: boolean | null;
  detail: string | null;
}

export interface HealthSnapshot extends SnapshotBase {
  services: ServiceRecord[];
  soak: {
    currentRun: string | null;
    elapsedHours: number | null;
    targetHours: number | null;
    restarts: number | null;
    lastError: string | null;
  };
  ramGuard: {
    usedGb: number | null;
    limitGb: number | null;
    headroomGb: number | null;
    state: "ARMED" | "TRIPPED" | "UNKNOWN";
  };
  faults: FaultRecord[];
}

export interface LessonRecord {
  demo: boolean;
  id: string;
  market: "GOLD" | "OIL" | string;
  mistake: string;
  lesson: string;
  sourceReplayId: string | null;
  status: "PROPOSED" | "ACCEPTED" | "REJECTED";
  reason: string;
  unseenTest: {
    datasetId: string | null;
    outOfSamplePeriod: string | null;
    result: UnseenResult;
    sampleSize: number | null;
  } | null;
}

export interface LessonsSnapshot extends SnapshotBase {
  lessons: LessonRecord[];
}

export interface AgentRecord {
  demo: boolean;
  name: string;
  role: string;
  currentMissionId: string | null;
  lastActivity: string | null;
  status: TruthStatus;
}

export interface MissionRecord {
  demo: boolean;
  id: string;
  title: string;
  ownerAgent: string | null;
  status: MissionState;
  evidence: string | null;
  lastUpdate: string | null;
}

export interface WorkroomSnapshot extends SnapshotBase {
  agents: AgentRecord[];
  missions: MissionRecord[];
}

export interface PortableSnapshot extends SnapshotBase {
  packageVersion: string | null;
  buildTime: string | null;
  checklist: {
    nodeBundled: RecordState;
    fonts: RecordState;
    models: RecordState;
    configTemplate: RecordState;
    smokeTest: RecordState;
  };
  hardware: {
    tier: "T0" | "T1" | "T2" | "UNKNOWN";
    ramGb: number | null;
    cpu: string | null;
    gpu: string | null;
    heavyFeaturesAllowed: boolean | null;
    note: string | null;
  };
}

export interface OilGoldSnapshot extends SnapshotBase {
  replay: {
    historicalPeriod: string | null;
    replayId: string | null;
    bars: number | null;
    markets: Array<"OIL" | "GOLD">;
    summary: string | null;
  };
  live: {
    status: "LIVE" | "UNKNOWN" | "UNAVAILABLE";
    timestamp: string | null;
    oil: number | null;
    gold: number | null;
    source: string | null;
  };
  evidence: {
    status: "NO_PROVEN_EDGE" | "EVIDENCE_AVAILABLE";
    datasetId: string | null;
    outOfSamplePeriod: string | null;
    sampleSize: number | null;
    costModel: string | null;
    note: string;
  };
  news: {
    oil: string | null;
    gold: string | null;
    otherMarkets: "PLANNED";
  };
}

export type SnapshotKey = "healthMonitor" | "lessons" | "workroom" | "portable" | "oilGold";
export interface ArenaContract {
  executionMode: string | null;
  realTrading: boolean | null;
  source: string | null;
  generatedAt: string | null;
  demo: boolean;
  healthMonitor: HealthSnapshot;
  lessons: LessonsSnapshot;
  workroom: WorkroomSnapshot;
  portable: PortableSnapshot;
  oilGold: OilGoldSnapshot;
}

export type ContractResult<T> =
  | { ok: true; value: T }
  | { ok: false; status: "UNAVAILABLE"; reason: string };
