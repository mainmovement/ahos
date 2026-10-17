// Batch 14: real paper/replay loaders. Run: npm run test:real-paper
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, utimesSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { parseJudgeMd, parseLessons, parseReplaySummary, parseSoakStatus, parseTradesCsv, replayAge } from "../src/features/real-paper/lib/model.ts";
import { equityImagePath, loadLatestJudge, loadReplaySummary, loadReplayTrades, loadSoakLedger } from "../src/features/real-paper/lib/data.server.ts";

const NOW = Date.parse("2026-10-17T01:00:00Z");
const soak = (ts: string | null, over: Record<string, unknown> = {}) => ({
  soak: "M13-GOLD-PAPER", paper_only: true, cycle_interval_sec: 900, cycles_ok: 16, cycles_failed: 0,
  last_cycle: { ts, cycle: 492, witness_state: "UNRESOLVED", witness_reason: "insufficient_independent_sources", position_open: true, breaker: { state: "ARMED" } },
  last_tier_gate: { tier: "T0", trades: 3, day: "2026-10-17", ready_for_owner_review: false },
  last_m42_reconcile: { verdict: "CLEAN", entries: 498, day: "2026-10-17" },
  ledger_state: { equity_usd: 10000.818481471944, bankroll_usd: 10000, closed_trades: 4, settled_trades: 3, cumulative_realized_pnl_usd: 0.8184814719436417, price_usd: null,
    position: { entry_price: 4177.8, exec_price: 4181.97, notional_usd: 1000, qty_oz: 0.239, entry_ts: 1792156653.5, cycle: 452 },
    witness: { state: "UNRESOLVED", reason: "x", quotes: [{ provider_id: "goldapi_spot", instrument: "spot", price_usd: 4166.1, observed_at: 1792197669 }] }, breaker: { state: "ARMED" } },
  ...over,
});
const RESULTS = `# AHOS REPLAY
> **REPLAY — NOT LIVE.** paper-only
## Summary
| Market | Buy&hold Sharpe / total / MaxDD | Best baseline (Sharpe) | Council Sharpe | Lab pick Sharpe / PF / total / trades | Verdict (lab · quant) |
|---|---|---|---|---|---|
| Gold daily | 0.86 / 264% / -25% | TREND 0.62 | 0.16 | 0.55 / 2.76 / 43% / 17 | **NO PROVEN EDGE · NO PROVEN EDGE** |
| Oil daily | 0.36 / 79% / -84% | TREND 0.33 | -0.08 | 0.25 / 1.57 / 31% / 18 | **NO PROVEN EDGE · NO PROVEN EDGE** |

next`;
const CSV = "label,market,system,entry_date,exit_date,entry_px,exit_px,size,ret_net,exit_kind,entry_regime,period\nREPLAY_NOT_LIVE,gold,LAB_PICK,2002-01-23,2002-03-08,1,2,1,0.1,SIGNAL,UP,TRAIN\nREPLAY_NOT_LIVE,gold,LAB_PICK,2018-01-23,2018-03-08,1,2,1,0.1,SIGNAL,UP,TEST\n";

test("soak: fresh paper ledger is LIVE with real numbers copied, unrealized UNKNOWN", () => {
  const v = parseSoakStatus(soak("2026-10-17T00:41:19Z"), NOW)!;
  assert.equal(v.status, "LIVE");
  assert.equal(v.equityUsd, 10000.818481471944);
  assert.equal(v.closedTrades, 4);
  assert.equal(v.position?.qtyOz, 0.239);
  assert.equal(v.unrealized, "UNKNOWN");
  assert.equal(v.witnessState, "UNRESOLVED");
  assert.equal(v.tier?.tier, "T0");
  assert.equal(v.paperOnly, true);
});
test("soak: stale keeps its age; no timestamp is UNKNOWN; non-paper is UNKNOWN", () => {
  const stale = parseSoakStatus(soak("2026-10-16T00:41:19Z"), NOW)!;
  assert.equal(stale.status, "STALE");
  assert.equal(stale.ageMin, 1459);
  assert.equal(parseSoakStatus(soak(null), NOW)!.status, "UNKNOWN");
  assert.equal(parseSoakStatus(soak("2026-10-17T00:41:19Z", { paper_only: false }), NOW)!.status, "UNKNOWN");
  assert.equal(parseSoakStatus(soak("garbage"), NOW)!.status, "UNKNOWN");
});
test("soak: missing numbers stay null (never 0); malformed shapes return null", () => {
  const v = parseSoakStatus({ soak: "S", paper_only: true, last_cycle: { ts: "2026-10-17T00:55:00Z" } }, NOW)!;
  assert.equal(v.equityUsd, null); assert.equal(v.closedTrades, null); assert.equal(v.position, null); assert.equal(v.positionOpen, null);
  assert.equal(parseSoakStatus(null, NOW), null); assert.equal(parseSoakStatus([], NOW), null); assert.equal(parseSoakStatus({ soak: "S" }, NOW), null); assert.equal(parseSoakStatus({ paper_only: true }, NOW), null);
});
test("judge md parses only stated numbers", () => {
  const j = parseJudgeMd("**Verdict: CLEAN**\n- ledger entries: 491\n- closed trades: 4 (3 settled, 1 invalidated)\n- wins / losses: 1 / 2\n- cycles with no corroborated price: 43\n")!;
  assert.deepEqual([j.verdict, j.closed, j.settled, j.invalidated, j.wins, j.losses, j.noPriceCycles], ["CLEAN", 4, 3, 1, 1, 2, 43]);
  assert.equal(parseJudgeMd("nothing here"), null); assert.equal(parseJudgeMd(null), null);
});
test("replay summary: verbatim cells, verdict only when every row says so", () => {
  const r = parseReplaySummary(RESULTS)!;
  assert.equal(r.rows.length, 2); assert.equal(r.labelledNotLive, true); assert.equal(r.edge, "NO_PROVEN_EDGE");
  assert.equal(r.rows[0].buyHold, "0.86 / 264% / -25%"); assert.equal(r.rows[1].labPick, "0.25 / 1.57 / 31% / 18");
  const mixed = parseReplaySummary(RESULTS.replace("**NO PROVEN EDGE · NO PROVEN EDGE** |\n| Oil", "**EDGE FOUND** |\n| Oil"))!;
  assert.equal(mixed.edge, "UNKNOWN");
  assert.equal(parseReplaySummary("# x\nno table"), null); assert.equal(parseReplaySummary(""), null); assert.equal(parseReplaySummary(null), null);
});
test("trades csv: counts only; malformed => null", () => {
  const s = parseTradesCsv(CSV)!;
  assert.equal(s.rows, 2); assert.equal(s.byPeriod.TEST, 1); assert.deepEqual(s.labels, ["REPLAY_NOT_LIVE"]); assert.equal(s.firstEntry, "2002-01-23");
  assert.equal(parseTradesCsv("a,b\n1,2"), null); assert.equal(parseTradesCsv(CSV + "short,row\n"), null); assert.equal(parseTradesCsv(""), null);
});
test("lessons + replay age (never LIVE)", () => {
  assert.deepEqual(parseLessons("# T\n## a\n## b\n"), { title: "T", sections: 2 });
  assert.equal(parseLessons(" "), null);
  assert.equal(replayAge("2026-10-16T00:00:00Z", NOW).status, "STALE");
  assert.equal(replayAge("2026-10-16T00:00:00Z", NOW).ageHours, 25);
  assert.equal(replayAge(null, NOW).status, "UNKNOWN");
});
test("fs loaders: missing / malformed / ok / stale", () => {
  const dir = mkdtempSync(join(tmpdir(), "rp14-"));
  try {
    const f = join(dir, "soak_status.json");
    assert.equal(loadSoakLedger(NOW, f).state, "missing");
    writeFileSync(f, "{not json");
    assert.equal(loadSoakLedger(NOW, f).state, "malformed");
    writeFileSync(f, JSON.stringify(soak("2026-10-17T00:41:19Z")));
    const ok = loadSoakLedger(NOW, f);
    assert.equal(ok.state, "ok"); if (ok.state === "ok") { assert.equal(ok.value.status, "LIVE"); assert.ok(ok.mtimeIso); }
    const st = loadSoakLedger(NOW + 3 * 3600_000, f);
    assert.equal(st.state === "ok" && st.value.status, "STALE");
    assert.equal(loadLatestJudge(f).state, "missing");
    writeFileSync(join(dir, "2026-10-16_judge.md"), "**Verdict: CLEAN**\n- closed trades: 1 (1 settled, 0 invalidated)\n");
    writeFileSync(join(dir, "2026-10-17_judge.md"), "garbage");
    assert.equal(loadLatestJudge(f).state, "malformed");
    mkdirSync(join(dir, "out", "gold"), { recursive: true });
    assert.equal(loadReplaySummary(dir).state, "missing");
    writeFileSync(join(dir, "results.md"), "# nothing");
    assert.equal(loadReplaySummary(dir).state, "malformed");
    writeFileSync(join(dir, "results.md"), RESULTS);
    utimesSync(join(dir, "results.md"), new Date("2026-10-16T00:00:00Z"), new Date("2026-10-16T00:00:00Z"));
    assert.equal(loadReplaySummary(dir).state, "ok");
    assert.equal(loadReplayTrades("gold", dir).state, "missing");
    writeFileSync(join(dir, "out", "gold", "trades.csv"), CSV);
    assert.equal(loadReplayTrades("gold", dir).state, "ok");
    writeFileSync(join(dir, "out", "gold", "trades.csv"), "x\ny,z");
    assert.equal(loadReplayTrades("gold", dir).state, "malformed");
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
test("equity route whitelist rejects traversal", () => {
  assert.ok(equityImagePath("gold", "/r")?.endsWith("equity_gold.png"));
  assert.equal(equityImagePath("../../secret", "/r"), null);
  assert.equal(equityImagePath("gold.png", "/r"), null);
});
