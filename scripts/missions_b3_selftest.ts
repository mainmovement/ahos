import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join } from "node:path";
import { healthFromSoak, lessonHighlights, normalizeLesson, oilGoldHighlights, parseReplayResults, portableHighlights, probeStatus, resolveRamGuardState, toMission } from "../src/features/missions-b3/lib/model";
import { validateArenaContract } from "../src/features/missions-b3/contract/validate";
import { buildMissionMap, redact, capHighlights } from "../src/features/missions-b2/lib/model";
import { headerConflicts, parseMissionsStatus } from "../src/features/missions-b2/lib/missions-status";
import { findForbiddenControl } from "../src/features/trade-venue/logic/truth";
import type { ArenaContract, LessonRecord } from "../src/features/missions-b3/contract/types";

const ROOT = join(import.meta.dirname, "..");
const FEATURE = join(ROOT, "src", "features", "missions-b3");
const contract = JSON.parse(readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8")) as ArenaContract;
const fa = JSON.parse(readFileSync(join(ROOT, "src", "i18n", "fa.json"), "utf8"));
const NOW = Date.parse("2026-10-17T00:00:00Z");
const walk = (d: string): string[] => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });

const soak = (over: Record<string, unknown> = {}) => ({
  soak: "M13-GOLD-PAPER", paper_only: true, started_hint: "2026-10-16T20:00:00Z", cycle_interval_sec: 900, planned_days: 2, cycles_ok: 13, cycles_failed: 0,
  last_cycle: { ts: "2026-10-16T23:56:16Z", cycle: 489, witness_state: "UNRESOLVED", witness_reason: "insufficient", ledger_error: null, breaker: { state: "ARMED" } },
  ledger_state: { breaker: { state: "ARMED" } }, last_tier_gate: { tier: "T0", ready_for_owner_review: false, day: "2026-10-16" }, ...over,
});

test("contract: example validates, demo, paper-only", () => {
  const r = validateArenaContract(contract);
  assert.equal(r.ok, true);
  assert.equal(contract.demo, true);
  assert.equal(contract.executionMode, "PAPER_ONLY");
  assert.equal(contract.realTrading, false);
  assert.equal(validateArenaContract(null).ok, false);
  assert.equal(validateArenaContract({ ...contract, healthMonitor: null }).ok, false);
});
test("health: fresh soak => LIVE runner; old => STALE; no ts => UNKNOWN", () => {
  const fresh = healthFromSoak(soak(), { bridge: "open", arena: "closed" }, "2026-10-16T23:57:00Z", NOW)!;
  assert.equal(fresh.snapshot.services[0].status, "LIVE");
  assert.equal(fresh.snapshot.services[1].status, "LIVE");
  assert.equal(fresh.snapshot.services[2].status, "UNAVAILABLE");
  assert.equal(fresh.mode, "PAPER_ONLY");
  assert.equal(fresh.real, false);
  const old = healthFromSoak(soak(), { bridge: "open", arena: "open" }, "x", NOW + 3 * 3600_000)!;
  assert.equal(old.status, "STALE");
  const none = healthFromSoak(soak({ last_cycle: { witness_state: null } }), { bridge: "unknown", arena: "unknown" }, "x", NOW)!;
  assert.equal(none.status, "UNKNOWN");
  assert.equal(none.snapshot.services[1].status, "UNKNOWN");
});
test("health: unrecognised/non-paper input never fabricates; ram guard unknown without numbers", () => {
  assert.equal(healthFromSoak(null, { bridge: "open", arena: "open" }, "x", NOW), null);
  assert.equal(healthFromSoak({ foo: 1 }, { bridge: "open", arena: "open" }, "x", NOW), null);
  const np = healthFromSoak(soak({ paper_only: false }), { bridge: "open", arena: "open" }, "x", NOW)!;
  assert.equal(np.snapshot.executionMode, null);
  assert.equal(np.real, true); // unknown mode is treated as a violation, not as paper
  const v = healthFromSoak(soak(), { bridge: "open", arena: "open" }, "x", NOW)!;
  assert.equal(resolveRamGuardState(v.snapshot), "UNKNOWN");
  assert.ok(capHighlights(v.highlights).shown.length <= 7);
  assert.equal(probeStatus("unknown"), "UNKNOWN");
  assert.equal(v.highlights.find((h) => h.id === "witness")!.status, "PARTIAL");
});
test("lessons: ACCEPTED without complete unseen test is shown PROPOSED; DEMO never LIVE", () => {
  const base = contract.lessons.lessons[0];
  const acc: LessonRecord = { ...base, status: "ACCEPTED", unseenTest: { datasetId: null, outOfSamplePeriod: null, result: "PASS", sampleSize: 10 } };
  assert.equal(normalizeLesson(acc).status, "PROPOSED");
  const full: LessonRecord = { ...base, status: "ACCEPTED", unseenTest: { datasetId: "d", outOfSamplePeriod: "2025", result: "PASS", sampleSize: 10 } };
  assert.equal(normalizeLesson(full).status, "ACCEPTED");
  assert.ok(lessonHighlights([full], true).every((h) => h.status !== "LIVE"));
});
test("workroom: counts derived from rows; parser agrees with itself; demo has no counts", () => {
  const md = "# x\nClaude missions\nUnits tracked: **3**\n- DONE: **1**\n- PARTIAL: **1**\n- NOT STARTED: **1**\n### DONE\n- [x] **M1**: a. e\n### PARTIAL\n- [~] **M2**: b. CAVEAT: c\n### NOT STARTED\n- [ ] **M3**: d. BLOCKED_OWNER\n";
  const p = parseMissionsStatus(md)!;
  assert.equal(p.missions.length, 3);
  assert.equal(headerConflicts(p), false);
  assert.equal(buildMissionMap(p.missions, false).counts!.done, 1);
  assert.equal(buildMissionMap(contract.workroom.missions.map(toMission), true).counts, null);
});
test("portable: unknown hardware never promoted; checklist UNKNOWN stays UNKNOWN or DEMO", () => {
  assert.equal(contract.portable.hardware.tier, "UNKNOWN");
  assert.ok(portableHighlights(contract.portable, true).every((h) => h.status === "DEMO"));
  assert.ok(portableHighlights(contract.portable, false).every((h) => h.status === "UNKNOWN"));
});
test("oil-gold: always 'no proven edge yet'; replay is labelled REPLAY_NOT_LIVE and never live", () => {
  const rp = parseReplayResults("# Replay 2025\nbars: 100\nsecret: abc123");
  assert.equal(rp!.edge, "NO_PROVEN_EDGE");
  assert.equal(parseReplayResults(""), null);
  assert.ok(!rp!.lines.join("|").includes("abc123"));
  const hl = oilGoldHighlights(contract.oilGold, rp, false);
  assert.equal(hl.find((h) => h.id === "replay")!.tag, "REPLAY_NOT_LIVE");
  assert.notEqual(hl.find((h) => h.id === "live")!.status, "LIVE");
  assert.equal(hl.find((h) => h.id === "edge")!.tag, "NO_PROVEN_EDGE");
  assert.equal(redact("token=abc"), "[redacted]");
});
test("real soak_status.json (if present) maps without throwing", { skip: !existsSync(join(ROOT, "..", "ahos", "reports", "grok", "M13_SOAK", "soak_status.json")) }, () => {
  const raw = JSON.parse(readFileSync(join(ROOT, "..", "ahos", "reports", "grok", "M13_SOAK", "soak_status.json"), "utf8"));
  const v = healthFromSoak(raw, { bridge: "unknown", arena: "unknown" }, "2026-10-17T00:00:00Z", Date.now())!;
  assert.ok(v);
  assert.ok(["LIVE", "STALE", "UNKNOWN"].includes(v.status));
  assert.equal(v.snapshot.demo, false);
});
test("source scan: no controls, no <12px, no green/red, no JSON hard-coded Persian outside i18n", () => {
  for (const f of walk(FEATURE).filter((x) => /\.(tsx|ts|css)$/.test(x) && !x.includes("contract"))) {
    const s = readFileSync(f, "utf8");
    assert.ok(!/<button\b|onClick=|<input\b|<form\b/.test(s), `control element in ${f}`);
    assert.ok(!/(green|#0f0|#00ff00|#f00\b|#ff0000)/i.test(s), `green/red in ${f}`);
    assert.ok(!/font-size:\s*(\d|1[01])px/.test(s), `<12px in ${f}`);
    assert.ok(!/[\u0600-\u06FF]/.test(s), `hard-coded Persian in ${f}`);
  }
});
test("i18n: every missionsB3 key used exists; no forbidden control wording", () => {
  const src = readFileSync(join(FEATURE, "components", "pages.tsx"), "utf8");
  const get = (o: any, p: string) => p.split(".").reduce((a, k) => (a == null ? a : a[k]), o);
  const keys = [...src.matchAll(/\bt\("([^"$]+)"\)/g)].map((m) => m[1]);
  assert.ok(keys.length > 20);
  for (const k of keys) assert.equal(typeof (get(fa.missionsB3, k) ?? get(fa.missionsB2, k)), "string", `missing key ${k}`);
  for (const p of ["health-monitor", "lessons", "workroom", "portable", "oil-gold"]) { assert.equal(typeof fa.missionsB3.page[p].title, "string"); assert.equal(typeof fa.missionsB3.page[p].sub, "string"); }
  const flat: string[] = [];
  (function w(o: any) { for (const v of Object.values(o)) typeof v === "string" ? flat.push(v) : w(v); })(fa.missionsB3);
  for (const s of flat) assert.equal(findForbiddenControl(s), null, `forbidden wording: ${s}`);
});
