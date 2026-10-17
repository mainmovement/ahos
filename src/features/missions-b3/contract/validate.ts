import type {
  ArenaContract,
  ContractResult,
  HealthSnapshot,
  LessonsSnapshot,
  OilGoldSnapshot,
  PortableSnapshot,
  SnapshotBase,
  WorkroomSnapshot,
} from "./types";

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const isNullableString = (value: unknown): boolean => value === null || typeof value === "string";
const isNullableNumber = (value: unknown): boolean => value === null || (typeof value === "number" && Number.isFinite(value));
const truthStatuses = ["LIVE", "STALE", "UNKNOWN", "DEMO", "CONFLICT", "REJECTED", "UNAVAILABLE", "PARTIAL", "PLANNED", "MISSING", "ERROR"];

const isCommon = (value: unknown): value is SnapshotBase =>
  isObject(value) &&
  isNullableString(value.executionMode) &&
  (typeof value.realTrading === "boolean" || value.realTrading === null) &&
  isNullableString(value.source) &&
  isNullableString(value.generatedAt) &&
  typeof value.demo === "boolean";

const fail = (reason: string): ContractResult<never> => ({ ok: false, status: "UNAVAILABLE", reason });

function healthOk(v: unknown): v is HealthSnapshot {
  if (!isCommon(v) || !isObject(v) || !Array.isArray(v.services) || !Array.isArray(v.faults) || !isObject(v.soak) || !isObject(v.ramGuard)) return false;
  const ram = v.ramGuard;
  return v.services.every((row) => isObject(row) && typeof row.demo === "boolean" && typeof row.name === "string" && truthStatuses.includes(String(row.status)) && isNullableString(row.lastHeartbeat) && isNullableString(row.version) && isNullableNumber(row.uptimeSeconds)) &&
    v.faults.every((row) => isObject(row) && typeof row.demo === "boolean" && typeof row.id === "string" && isNullableString(row.time) && typeof row.faultType === "string" && typeof row.targetService === "string" && typeof row.expected === "string" && isNullableString(row.observed) && (typeof row.recovered === "boolean" || row.recovered === null)) &&
    isNullableString(v.soak.currentRun) && isNullableNumber(v.soak.elapsedHours) && isNullableNumber(v.soak.targetHours) && isNullableNumber(v.soak.restarts) && isNullableString(v.soak.lastError) &&
    isNullableNumber(ram.usedGb) && isNullableNumber(ram.limitGb) && isNullableNumber(ram.headroomGb) && ["ARMED", "TRIPPED", "UNKNOWN"].includes(String(ram.state));
}
function lessonsOk(v: unknown): v is LessonsSnapshot {
  if (!isCommon(v) || !isObject(v) || !Array.isArray(v.lessons)) return false;
  return v.lessons.every((row) => {
    if (!isObject(row) || typeof row.demo !== "boolean" || typeof row.id !== "string" || typeof row.market !== "string" || typeof row.mistake !== "string" || typeof row.lesson !== "string" || !isNullableString(row.sourceReplayId) || !["PROPOSED", "ACCEPTED", "REJECTED"].includes(String(row.status)) || (typeof row.reason !== "string" || row.reason.trim().length === 0)) return false;
    const test = row.unseenTest;
    if (test === null) return row.status !== "ACCEPTED";
    if (!isObject(test) || !isNullableString(test.datasetId) || !isNullableString(test.outOfSamplePeriod) || !["PASS", "FAIL", "NOT_RUN"].includes(String(test.result)) || !isNullableNumber(test.sampleSize)) return false;
    return row.status !== "ACCEPTED" || (test.result === "PASS" && typeof test.datasetId === "string" && test.datasetId.length > 0 && typeof test.outOfSamplePeriod === "string" && test.outOfSamplePeriod.length > 0 && typeof test.sampleSize === "number" && test.sampleSize > 0);
  });
}
function workroomOk(v: unknown): v is WorkroomSnapshot {
  if (!isCommon(v) || !isObject(v) || !Array.isArray(v.agents) || !Array.isArray(v.missions)) return false;
  return v.agents.every((row) => isObject(row) && typeof row.demo === "boolean" && typeof row.name === "string" && typeof row.role === "string" && isNullableString(row.currentMissionId) && isNullableString(row.lastActivity) && truthStatuses.includes(String(row.status))) &&
    v.missions.every((row) => isObject(row) && typeof row.demo === "boolean" && typeof row.id === "string" && typeof row.title === "string" && isNullableString(row.ownerAgent) && ["DONE", "PARTIAL", "NOT STARTED"].includes(String(row.status)) && isNullableString(row.evidence) && isNullableString(row.lastUpdate));
}
function portableOk(v: unknown): v is PortableSnapshot {
  if (!isCommon(v) || !isObject(v) || !isObject(v.checklist) || !isObject(v.hardware) || !isNullableString(v.packageVersion) || !isNullableString(v.buildTime)) return false;
  const states = ["DONE", "PARTIAL", "NOT STARTED", "UNKNOWN"];
  const checklist = v.checklist as Record<string, unknown>;
  const hardware = v.hardware as Record<string, unknown>;
  return ["nodeBundled", "fonts", "models", "configTemplate", "smokeTest"].every((key) => Object.prototype.hasOwnProperty.call(checklist, key) && states.includes(String(checklist[key]))) && Object.keys(checklist).length === 5 &&
    ["T0", "T1", "T2", "UNKNOWN"].includes(String(hardware.tier)) && isNullableNumber(hardware.ramGb) && isNullableString(hardware.cpu) && isNullableString(hardware.gpu) && (typeof hardware.heavyFeaturesAllowed === "boolean" || hardware.heavyFeaturesAllowed === null) && isNullableString(hardware.note);
}
function oilGoldOk(v: unknown): v is OilGoldSnapshot {
  if (!isCommon(v) || !isObject(v) || !isObject(v.replay) || !isObject(v.live) || !isObject(v.evidence) || !isObject(v.news)) return false;
  const replay = v.replay;
  const live = v.live;
  const evidence = v.evidence;
  return isNullableString(replay.historicalPeriod) && isNullableString(replay.replayId) && isNullableNumber(replay.bars) && Array.isArray(replay.markets) && replay.markets.every((m) => m === "OIL" || m === "GOLD") && isNullableString(replay.summary) &&
    ["LIVE", "UNKNOWN", "UNAVAILABLE"].includes(String(live.status)) && isNullableString(live.timestamp) && isNullableNumber(live.oil) && isNullableNumber(live.gold) && isNullableString(live.source) &&
    ["NO_PROVEN_EDGE", "EVIDENCE_AVAILABLE"].includes(String(evidence.status)) && isNullableString(evidence.datasetId) && isNullableString(evidence.outOfSamplePeriod) && isNullableNumber(evidence.sampleSize) && isNullableString(evidence.costModel) && typeof evidence.note === "string" &&
    isNullableString(v.news.oil) && isNullableString(v.news.gold) && v.news.otherMarkets === "PLANNED" && !(live.status === "LIVE" && (!live.timestamp || !live.source));
}

function withCommon<T extends SnapshotBase>(section: unknown, root: Record<string, unknown>): T {
  const value = section as Record<string, unknown>;
  return {
    ...value,
    executionMode: value.executionMode ?? root.executionMode ?? null,
    realTrading: value.realTrading ?? root.realTrading ?? null,
    source: value.source ?? root.source ?? null,
    generatedAt: value.generatedAt ?? root.generatedAt ?? null,
    demo: value.demo ?? root.demo ?? true,
    availability: "AVAILABLE",
  } as T;
}

/** Validates untrusted JSON without throwing. A missing generatedAt remains null (UNKNOWN). */
export function validateArenaContract(input: unknown): ContractResult<ArenaContract> {
  try {
    if (!isObject(input)) return fail("ریشهٔ قرارداد باید یک شیء باشد.");
    const root = input;
    if (!isNullableString(root.executionMode) || !(typeof root.realTrading === "boolean" || root.realTrading === null) || !isNullableString(root.source) || !isNullableString(root.generatedAt) || typeof root.demo !== "boolean") return fail("فیلدهای مشترک قرارداد معتبر نیستند.");
    const sections = {
      healthMonitor: withCommon<HealthSnapshot>(root.healthMonitor, root),
      lessons: withCommon<LessonsSnapshot>(root.lessons, root),
      workroom: withCommon<WorkroomSnapshot>(root.workroom, root),
      portable: withCommon<PortableSnapshot>(root.portable, root),
      oilGold: withCommon<OilGoldSnapshot>(root.oilGold, root),
    };
    if (![healthOk(sections.healthMonitor), lessonsOk(sections.lessons), workroomOk(sections.workroom), portableOk(sections.portable), oilGoldOk(sections.oilGold)].every(Boolean)) return fail("یک یا چند بخش قرارداد با طرح داده سازگار نیستند.");
    return { ok: true, value: { ...root, ...sections } as ArenaContract };
  } catch {
    return fail("خواندن قرارداد ناموفق بود.");
  }
}
