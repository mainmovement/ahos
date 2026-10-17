import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  CALM_MAX, buildNewsCenter, buildScienceRadar, buildSelfDebug, buildSkillMarket, buildWeeklyExam, capHighlights, clean, effectiveReview,
  newsFreshness, parseSoakRunlog,
} from "../src/features/missions-b4/lib/model";
import { validateContract, validateNewsCenter } from "../src/features/missions-b4/contract/validate";
import { findForbiddenControl } from "../src/features/trade-venue/logic/truth";
import type { AhosArenaContract } from "../src/features/missions-b4/contract/types";

const ROOT = join(import.meta.dirname, "..");
const FEATURE = join(ROOT, "src", "features", "missions-b4");
const contract = JSON.parse(readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8")) as AhosArenaContract;
const fa = JSON.parse(readFileSync(join(ROOT, "src", "i18n", "fa.json"), "utf8"));
const walk = (d: string): string[] => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : [p]; });

test("contract: example validates, every section DEMO + paper-only; bad input rejected", () => {
  assert.ok(validateContract(contract));
  for (const k of ["scienceRadar", "selfDebug", "weeklyExam", "skillMarket", "newsCenter"] as const) assert.equal(contract[k].demo, true);
  assert.equal(contract.executionMode, "PAPER_ONLY");
  assert.equal(contract.realTrading, false);
  for (const bad of [null, undefined, 3, "x", [], {}, { ...contract, newsCenter: null }]) assert.equal(validateContract(bad), null);
  assert.equal(validateNewsCenter(5 as never), null);
  const s = readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8");
  assert.equal(/\d{6,}:[A-Za-z0-9_-]{20,}/.test(s), false);
});

test("calm view: <= 7 highlights, rest hidden, every page", () => {
  const radar = buildScienceRadar(contract.scienceRadar, true);
  const debug = buildSelfDebug(contract.selfDebug, true);
  const exam = buildWeeklyExam(contract.weeklyExam, true);
  const sk = buildSkillMarket(contract.skillMarket, true);
  const news = buildNewsCenter(contract.newsCenter, true);
  for (const h of [radar.highlights, debug.highlights, exam.highlights, sk.highlights, news.highlights]) {
    const c = capHighlights(h);
    assert.ok(c.shown.length <= CALM_MAX);
    assert.equal(c.shown.length + c.hidden, h.length);
  }
  assert.equal(capHighlights(radar.highlights).hidden, 1); // 8 radar items
});

test("DEMO never LIVE and never counted", () => {
  const all = [
    ...buildScienceRadar(contract.scienceRadar, true).highlights, ...buildSelfDebug(contract.selfDebug, true).highlights,
    ...buildWeeklyExam(contract.weeklyExam, true).highlights, ...buildSkillMarket(contract.skillMarket, true).highlights,
    ...buildNewsCenter(contract.newsCenter, true).highlights,
  ];
  assert.ok(all.every((h) => h.status === "DEMO"));
  assert.equal(buildScienceRadar(contract.scienceRadar, true).counts, null);
  assert.equal(buildSelfDebug(contract.selfDebug, true).counts, null);
  assert.equal(buildSkillMarket(contract.skillMarket, true).counts, null);
  assert.equal(buildNewsCenter(contract.newsCenter, true).counts, null);
  assert.equal(buildWeeklyExam(contract.weeklyExam, true).countedRuns, null);
  assert.equal(buildWeeklyExam(contract.weeklyExam, true).adequate, false);
});

test("weekly-exam: below minSampleSize no aggregate; missing numbers are '-' not 0", () => {
  const real = { ...contract.weeklyExam, demo: false, runs: contract.weeklyExam.runs.slice(0, 2).map((r) => ({ ...r, demo: false })) };
  const v = buildWeeklyExam(real, false);
  assert.equal(v.countedRuns, 2);
  assert.equal(v.adequate, false);
  assert.equal(buildWeeklyExam({ ...real, minSampleSize: 2 }, false).adequate, true);
  const missing = buildWeeklyExam(contract.weeklyExam, true).highlights.find((h) => h.id === "we-02");
  assert.equal(missing?.detail, "- / - | -");
});

test("skill-market: REVIEWED/REJECTED without reason => UNREVIEWED; never 'safe'", () => {
  assert.deepEqual(effectiveReview({ reviewState: "REVIEWED", reason: null }), { state: "UNREVIEWED", missingReason: true });
  assert.deepEqual(effectiveReview({ reviewState: "REJECTED", reason: "  " }), { state: "UNREVIEWED", missingReason: true });
  assert.deepEqual(effectiveReview({ reviewState: "REVIEWED", reason: "x" }), { state: "REVIEWED", missingReason: false });
  assert.deepEqual(effectiveReview({ reviewState: "UNREVIEWED", reason: null }), { state: "UNREVIEWED", missingReason: false });
});

test("news freshness: no time => UNKNOWN; future => UNKNOWN; stale by threshold", () => {
  const g = "2026-10-16T12:00:00+03:30";
  assert.equal(newsFreshness({ time: null }, g, 60), "UNKNOWN");
  assert.equal(newsFreshness({ time: "2026-10-16T11:30:00+03:30" }, null, 60), "UNKNOWN");
  assert.equal(newsFreshness({ time: "2026-10-16T12:30:00+03:30" }, g, 60), "UNKNOWN");
  assert.equal(newsFreshness({ time: "2026-10-16T11:30:00+03:30" }, g, 60), "LIVE");
  assert.equal(newsFreshness({ time: "2026-10-16T09:00:00+03:30" }, g, 60), "STALE");
  assert.equal(newsFreshness({ time: "nope" }, g, 60), "UNKNOWN");
});

test("real soak runlog parser: only ok=false rows, malformed skipped, paths/secrets cleaned", () => {
  const text = [
    JSON.stringify({ ts: "2026-10-15T20:00:00Z", kind: "cycle", ok: true, cycle: 1 }),
    "{not json",
    JSON.stringify({ ts: "2026-10-15T21:10:08Z", kind: "tier_gate", ok: false, error: "ModuleNotFoundError: No module named 'numpy'", traceback: "a\nFile \"C:\\Users\\bob\\x.py\", line 1\nModuleNotFoundError: x" }),
    JSON.stringify({ ts: "2026-10-15T22:00:00Z", kind: "cycle", ok: true, ledger_error: "token=abc123secret" }),
    JSON.stringify({ kind: "cycle", ok: true }),
  ].join("\n");
  const p = parseSoakRunlog(text);
  assert.equal(p.rows, 4);
  assert.equal(p.skipped, 1);
  assert.equal(p.incidents.length, 2);
  assert.equal(p.lastTs, "2026-10-15T22:00:00Z");
  assert.equal(p.incidents[0].demo, false);
  assert.equal(p.incidents[0].status, "UNKNOWN");
  assert.ok(!JSON.stringify(p.incidents).includes("bob"));
  assert.ok(!JSON.stringify(p.incidents).includes("abc123secret"));
  const v = buildSelfDebug({ kind: "selfDebug", executionMode: "PAPER_ONLY", realTrading: false, source: "x", generatedAt: p.lastTs, incidents: p.incidents }, false);
  assert.deepEqual(v.counts, { total: 2, open: 0, diagnosed: 0, unknown: 2 });
  assert.equal(parseSoakRunlog("").rows, 0);
});

test("clean(): redacts secrets and user paths, clamps", () => {
  assert.ok(!clean("C:\\Users\\alice\\proj api_key=ZZZ").includes("alice"));
  assert.ok(clean("x".repeat(500), 50).length <= 50);
});

test("no trade/approve/install controls and no forbidden verbs in b4 sources", () => {
  const files = [...walk(FEATURE), ...walk(join(ROOT, "app", "arena", "science-radar")), ...walk(join(ROOT, "app", "arena", "self-debug")), ...walk(join(ROOT, "app", "arena", "weekly-exam")), ...walk(join(ROOT, "app", "arena", "skill-market")), ...walk(join(ROOT, "app", "arena", "news-center"))].filter((f) => /\.(tsx|ts)$/.test(f) && !f.includes("contract"));
  for (const f of files) {
    const src = readFileSync(f, "utf8");
    assert.equal(/<button|<input|<form|onClick|onSubmit|fetch\(|writeFile|appendFile|unlink/.test(src), false, f);
    assert.equal(findForbiddenControl(src), null, f);
  }
});

test("i18n: every tr key used by b4 pages exists in fa.json; min font 12px; RTL frame", () => {
  const used = new Set<string>();
  for (const f of walk(join(FEATURE, "components"))) for (const m of readFileSync(f, "utf8").matchAll(/\bt\("([^"]+)"\)/g)) used.add(m[1]);
  for (const k of used) if (!k.startsWith("ui.noData")) {
    const v = k.split(".").reduce<unknown>((o, p) => (o as Record<string, unknown> | undefined)?.[p], k.startsWith("ui.") && !fa.missionsB4.ui?.[k.slice(3)] ? fa.missionsB2 : fa.missionsB4);
    assert.equal(typeof v, "string", `missing fa key ${k}`);
  }
  for (const p of ["science-radar", "self-debug", "weekly-exam", "skill-market", "news-center"]) assert.equal(typeof fa.missionsB4.page[p].title, "string");
  const css = readFileSync(join(ROOT, "src", "features", "missions-b2", "styles.css"), "utf8");
  for (const m of css.matchAll(/font-size:\s*(\d+)px/g)) assert.ok(Number(m[1]) >= 12);
  assert.ok(readFileSync(join(ROOT, "src", "features", "missions-b2", "components", "PageFrame.tsx"), "utf8").includes('dir="rtl"'));
});
