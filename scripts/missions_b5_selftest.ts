import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  CALM_MAX, HEARTBEAT_MAX_MIN, buildAgents, buildCapability, buildNightly, buildUniversity, capHighlights, clean, examResult, freshOf, needsOwner,
  parseAgentRegistry, parseBenchmark, parseCriteria, parseDigest, parseJudgeNumbers, parseProposal, parseTier, parseUniversitySources, parseVerdict, presenceOf, stageOf, trend, verdictStatus,
} from "../src/features/missions-b5/lib/model";
import { validateContract } from "../src/features/missions-b5/contract/validate";
import { findForbiddenControl } from "../src/features/trade-venue/logic/truth";
import type { AhosArenaContract } from "../src/features/missions-b5/contract/types";

const ROOT = join(import.meta.dirname, "..");
const FEATURE = join(ROOT, "src", "features", "missions-b5");
const contract = JSON.parse(readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8")) as AhosArenaContract;
const fa = JSON.parse(readFileSync(join(ROOT, "src", "i18n", "fa.json"), "utf8"));
const walk = (d: string): string[] => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
const NOW = Date.parse("2026-10-18T00:00:00Z");

test("contract: example validates, every section DEMO + paper-only; bad input rejected", () => {
  assert.ok(validateContract(contract));
  for (const k of ["nightlyReport", "university", "capabilityLab", "agentCenter"] as const) assert.equal(contract[k].demo, true);
  assert.equal(contract.executionMode, "PAPER_ONLY");
  assert.equal(contract.realTrading, false);
  for (const bad of [null, undefined, 3, "x", [], {}, { ...contract, agentCenter: null }, { ...contract, extra: 1 }]) assert.equal(validateContract(bad), null);
  const badTier = structuredClone(contract); badTier.nightlyReport.nights[0].tier = 9;
  assert.equal(validateContract(badTier), null);
  const badRetests = structuredClone(contract); badRetests.university.exams[0].retests = 4;
  assert.equal(validateContract(badRetests), null);
});

test("nightly parsers: real M13 formats, tolerant, unparseable => null", () => {
  assert.equal(parseVerdict("# M42 paper judge\n\n**Verdict: CLEAN**\n- x"), "CLEAN");
  assert.equal(parseVerdict("# Verdict - pass"), "PASS");
  assert.equal(parseVerdict("verdict : DISCREPANCY"), "DISCREPANCY");
  assert.equal(parseVerdict("no such line"), null);
  assert.equal(parseVerdict(""), null);
  assert.equal(parseVerdict(null), null);
  assert.equal(parseTier("Tier today: **T0** (paper only)"), 0);
  assert.equal(parseTier("Tier today: **T7**"), null);
  assert.equal(parseTier("garbage"), null);
  assert.equal(parseCriteria("1/7 measurable criteria passed; 4 unmeasurable."), "1/7 (+4 unmeasurable)");
  assert.equal(parseCriteria("nothing"), null);
  const n = parseJudgeNumbers("- closed trades: 4 (3 settled)\n- wins / losses: 1 / 2\n- gross realized PnL: 0.82 (PAPER)");
  assert.deepEqual(n, { closed: 4, wins: 1, losses: 2, pnl: 0.82 });
  assert.deepEqual(parseJudgeNumbers("zzz"), { closed: null, wins: null, losses: null, pnl: null });
  assert.deepEqual(parseDigest('{"day":"2026-10-17","entries":78,"signed":false}'), { day: "2026-10-17", entries: 78, signed: false });
  assert.deepEqual(parseDigest("{not json"), { day: null, entries: null, signed: null });
  assert.deepEqual(parseDigest("[1]"), { day: null, entries: null, signed: null });
  assert.deepEqual(parseDigest('{"day":"x","entries":-1,"signed":"no"}'), { day: null, entries: null, signed: null });
});

test("verdict chips: CLEAN is green only while fresh; unknown/unparseable never green; DEMO never LIVE", () => {
  assert.equal(verdictStatus("CLEAN", "LIVE", false), "LIVE");
  assert.equal(verdictStatus("CLEAN", "STALE", false), "STALE");
  assert.equal(verdictStatus("CLEAN", "UNKNOWN", false), "UNKNOWN");
  assert.equal(verdictStatus(null, "LIVE", false), "UNKNOWN");
  assert.equal(verdictStatus("WHATEVER", "LIVE", false), "UNKNOWN");
  assert.equal(verdictStatus("DISCREPANCY", "LIVE", false), "CONFLICT");
  assert.equal(verdictStatus("CLEAN", "LIVE", true), "DEMO");
});

test("staleness: >26h STALE, no/invalid/future timestamp UNKNOWN", () => {
  assert.equal(freshOf("2026-10-17T23:00:00Z", NOW), "LIVE");
  assert.equal(freshOf("2026-10-16T21:00:00Z", NOW), "STALE");
  assert.equal(freshOf(null, NOW), "UNKNOWN");
  assert.equal(freshOf("nope", NOW), "UNKNOWN");
  assert.equal(freshOf("2026-10-19T00:00:00Z", NOW), "UNKNOWN");
});

test("nightly view: DEMO excluded from counts, real counted, latest first, missing stays null", () => {
  const demo = buildNightly(contract.nightlyReport.nights, NOW, true);
  assert.equal(demo.counts, null);
  assert.ok(demo.highlights.every((h) => h.status === "DEMO"));
  const real = contract.nightlyReport.nights.map((n, i) => ({ ...n, demo: false, id: `r${i}`, timestamp: i === 0 ? "2026-10-17T23:00:00Z" : null }));
  const v = buildNightly([...real, { ...real[0], demo: true, id: "d", closed: 99 }], NOW, false);
  assert.deepEqual(v.counts, { nights: 2, closed: 8, fresh: 1, unknownVerdicts: 1 });
  assert.equal(v.latest?.day, "2026-10-16");
  assert.equal(buildNightly([], NOW, false).latest, null);
});

test("university: parseUniversitySources reads registry rows from yaml", () => {
  const yaml = `schema: ahos.university.sources.v1\nsources:\n  - url: https://example.org/x\n    license: CC0\n    faculty: quant\n`;
  const rows = parseUniversitySources(yaml);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].demo, false);
  assert.equal(rows[0].domain, "example.org");
  assert.equal(rows[0].access, "registry");
});

test("university: exam score is neutral and insufficient without items>=30, CI and hash; DEMO not counted", () => {
  const [good, thin] = contract.university.exams;
  assert.deepEqual(examResult(good), { label: "91", sufficient: true });
  assert.equal(examResult(thin).sufficient, false);
  assert.equal(examResult({ ...good, items: 29 }).sufficient, false);
  assert.equal(examResult({ ...good, hash: "  " }).sufficient, false);
  assert.equal(examResult({ ...good, ci: null }).sufficient, false);
  assert.equal(examResult({ ...good, score: null }).sufficient, false);
  const u = buildUniversity(contract.university, true);
  assert.equal(u.counts, null);
  assert.ok(u.highlights.every((h) => h.status === "DEMO"));
  const real = buildUniversity({ sources: [], exams: [{ ...good, demo: false }, { ...good, demo: true }], bank: [{ demo: false, count: 5 }, { demo: true, count: 500 }] }, false);
  assert.deepEqual(real.counts, { sources: 0, exams: 1, bankItems: 5 });
});

test("capability-lab: delta only from two timestamped measurements with item counts; proposals map; owner gate", () => {
  const p = (value: number | null, items: number | null, timestamp: string | null) => ({ demo: false, capability: "c", unit: null, timestamp, value, seed: null, items });
  assert.equal(trend([p(1, 5, "2026-10-01T00:00:00Z")])[0].delta, null);
  assert.equal(trend([p(1, 5, "2026-10-01T00:00:00Z"), p(3, 5, "2026-10-02T00:00:00Z")])[0].delta, 2);
  assert.equal(trend([p(1, null, "2026-10-01T00:00:00Z"), p(3, 5, "2026-10-02T00:00:00Z")])[0].delta, null);
  assert.equal(trend([p(1, 5, null), p(3, 5, "2026-10-02T00:00:00Z")])[0].delta, null);
  assert.equal(trend([p(null, 5, "2026-10-01T00:00:00Z"), p(3, 5, "2026-10-02T00:00:00Z")])[0].delta, null);
  assert.equal(trend([]).length, 0);
  assert.equal(stageOf("proposed"), "PROPOSED");
  assert.equal(stageOf("WEIRD"), "UNKNOWN");
  assert.equal(stageOf(7), "UNKNOWN");
  const prop = parseProposal(JSON.stringify({ proposal_id: "prop_1", created_ts: 1787220693.7, diagnosis: "cycle token=SECRETVALUE", requires_human: true, governance_touching: false, redteam_verdict: "NEEDS_MORE_DATA", current_stage: "PROPOSED" }));
  assert.ok(prop);
  assert.equal(prop!.stage, "PROPOSED");
  assert.equal(prop!.requiresHuman, true);
  assert.ok(!prop!.title.includes("SECRETVALUE"));
  assert.ok(needsOwner(prop!));
  assert.equal(parseProposal("{bad"), null);
  assert.equal(parseProposal("{}"), null);
  const c = buildCapability(contract.capabilityLab, true);
  assert.equal(c.counts, null);
  assert.ok(c.highlights.every((h) => h.status === "DEMO"));
  const bench = parseBenchmark(JSON.stringify({ timestamp_utc: "2026-08-20T09:51:19Z", results: { vectorized_backtest: { combinations_evaluated: 64, evaluations_per_sec: 1468.8 }, quantstats_tearsheet: { runs: 50, latency_per_tearsheet_ms: 0.57 } } }));
  assert.equal(bench.length, 2);
  assert.equal(bench[0].items, 64);
  assert.equal(bench[0].seed, null);
  assert.deepEqual(parseBenchmark("nope"), []);
});

const REG = [
  "# comment", "matrix_version: X", "agents:",
  "  - agent_id: AG-01", "    name: Master Orchestrator", "    status: MISSING", "    lane: B", "    criticality: CRITICAL", "    ops:",
  "      operability: {implemented: false, contracted: false, orchestrated: false, live: false}",
  "  - agent_id: AG-02", '    name: "Data Intelligence"', "    status: EXISTS", "    lane: A", "    criticality: HIGH", "    heartbeat: 2026-10-17T23:59:30Z",
  "      operability: {implemented: true, contracted: false, orchestrated: false, live: true}",
  "  - agent_id: AG-03", "    status: PARTIAL", "    heartbeat: not-a-date", "tail: 1",
].join("\n");

test("agent-center: REGISTERED always, ONLINE only with heartbeat <=2min, never from live flag; registry parsed tolerantly", () => {
  const a = parseAgentRegistry(REG);
  assert.equal(a.length, 3);
  assert.equal(a[0].regStatus, "MISSING");
  assert.equal(a[0].liveFlag, false);
  assert.equal(a[1].name, "Data Intelligence");
  assert.equal(a[1].liveFlag, true);
  assert.equal(a[2].heartbeat, null);
  assert.equal(a[2].name, "AG-03");
  assert.deepEqual(parseAgentRegistry("garbage: [\nnothing"), []);
  assert.equal(HEARTBEAT_MAX_MIN, 2);
  assert.equal(presenceOf({ heartbeat: "2026-10-17T23:59:30Z" }, NOW), "ONLINE");
  assert.equal(presenceOf({ heartbeat: "2026-10-17T23:57:00Z" }, NOW), "UNKNOWN");
  assert.equal(presenceOf({ heartbeat: "2026-10-18T00:05:00Z" }, NOW), "UNKNOWN");
  assert.equal(presenceOf({ heartbeat: null }, NOW), "UNKNOWN");
  assert.equal(presenceOf({ heartbeat: "x" }, NOW), "UNKNOWN");
  const v = buildAgents(a, NOW, false);
  assert.deepEqual(v.counts, { registered: 3, online: 1, unknown: 2, exists: 1, partial: 1, planned: 0, missing: 1 });
  assert.equal(v.rows[0].a.id, "AG-01"); // CRITICAL first
  assert.equal(v.highlights.find((h) => h.id === "AG-01")!.status, "UNKNOWN");
  assert.equal(v.highlights.find((h) => h.id === "AG-02")!.status, "LIVE");
  const d = buildAgents(contract.agentCenter.agents, NOW, true);
  assert.equal(d.counts, null);
  assert.ok(d.highlights.every((h) => h.status === "DEMO")); // a demo heartbeat can never read ONLINE/LIVE
});

test("calm view: <= 7 highlights, the rest hidden, every page", () => {
  const many = Array.from({ length: 43 }, (_, i) => ({ demo: false, id: `AG-${i}`, name: "n", role: null, regStatus: "PLANNED", lane: null, criticality: null, liveFlag: null, heartbeat: null }));
  const lists = [
    buildAgents(many, NOW, false).highlights, buildNightly(contract.nightlyReport.nights, NOW, true).highlights,
    buildUniversity(contract.university, true).highlights, buildCapability(contract.capabilityLab, true).highlights,
  ];
  for (const h of lists) {
    const c = capHighlights(h);
    assert.ok(c.shown.length <= CALM_MAX);
    assert.equal(c.shown.length + c.hidden, h.length);
  }
  assert.equal(capHighlights(lists[0]).hidden, 36);
});

test("clean(): redacts secrets and user paths, clamps", () => {
  assert.ok(!clean("C:\\Users\\alice\\proj api_key=ZZZ").includes("alice"));
  assert.ok(clean("x".repeat(500), 50).length <= 50);
});

test("no trade/approve controls and no forbidden verbs / writes in b5 sources", () => {
  const dirs = ["nightly-report", "university", "capability-lab", "agent-center"].map((p) => join(ROOT, "app", "arena", p));
  const files = [...walk(FEATURE), ...dirs.flatMap(walk)].filter((f) => /\.(tsx|ts)$/.test(f) && !f.includes("contract"));
  for (const f of files) {
    const src = readFileSync(f, "utf8");
    assert.equal(/<button|<input|<form|onClick|onSubmit|fetch\(|writeFile|appendFile|unlink|rmSync|mkdirSync/.test(src), false, f);
    assert.equal(findForbiddenControl(src), null, f);
  }
});

test("i18n: every tr key used by b5 pages exists in fa.json; min font 12px; RTL frame", () => {
  const used = new Set<string>();
  for (const f of walk(join(FEATURE, "components"))) for (const m of readFileSync(f, "utf8").matchAll(/\bt\("([^"]+)"\)/g)) used.add(m[1]);
  assert.ok(used.size > 40);
  for (const k of used) {
    const v = k.split(".").reduce<unknown>((o, p) => (o as Record<string, unknown> | undefined)?.[p], fa.missionsB5);
    assert.equal(typeof v, "string", `missing fa key ${k}`);
  }
  for (const p of ["nightly-report", "university", "capability-lab", "agent-center"]) assert.equal(typeof fa.missionsB5.page[p].title, "string");
  const css = readFileSync(join(ROOT, "src", "features", "missions-b2", "styles.css"), "utf8");
  for (const m of css.matchAll(/font-size:\s*(\d+)px/g)) assert.ok(Number(m[1]) >= 12);
  assert.ok(readFileSync(join(ROOT, "src", "features", "missions-b2", "components", "PageFrame.tsx"), "utf8").includes('dir="rtl"'));
});
