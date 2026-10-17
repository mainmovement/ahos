/**
 * AHOS Arena - batch 14 real read-only paper/replay bindings. Pure logic: no React, no fs, no net.
 * Asserted by scripts/real_paper_selftest.ts.
 * Truth rules: LIVE needs a fresh timestamp; STALE keeps its age; no timestamp => UNKNOWN; missing numbers stay null
 * (rendered "-", never 0); replay is never live; nothing here computes or invents a number (values are copied from files).
 */
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { freshness, redact } from "@/src/features/missions-b2/lib/model";

export type Loaded<T> = { state: "ok"; value: T; mtimeIso: string | null } | { state: "missing" } | { state: "malformed" };
export const SOAK_MIN_STALE_MS = 30 * 60 * 1000;

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): string | null => (typeof v === "string" && v.length > 0 ? v : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const ageMin = (iso: string | null, nowMs: number): number | null => {
  const t = iso ? Date.parse(iso) : NaN;
  return Number.isFinite(t) ? Math.max(0, Math.round((nowMs - t) / 60000)) : null;
};
const epochIso = (s: unknown): string | null => {
  const n = num(s);
  return n === null || n <= 0 ? null : new Date(n * 1000).toISOString();
};

export interface WitnessQuote { provider: string; instrument: string | null; priceUsd: number | null; observedIso: string | null; ageMin: number | null }
export interface PaperPosition { entryPrice: number | null; execPrice: number | null; notionalUsd: number | null; qtyOz: number | null; entryIso: string | null; cycle: number | null }
export interface PaperLedgerView {
  soak: string;
  paperOnly: boolean;
  status: ChipStatus;
  lastCycleIso: string | null;
  ageMin: number | null;
  cycle: number | null;
  cyclesOk: number | null;
  cyclesFailed: number | null;
  equityUsd: number | null;
  bankrollUsd: number | null;
  cumulativeRealizedUsd: number | null;
  closedTrades: number | null;
  settledTrades: number | null;
  positionOpen: boolean | null;
  position: PaperPosition | null;
  /** unrealized PnL is only known when a corroborated price exists; the ledger says unpriced => UNKNOWN */
  unrealized: "UNKNOWN";
  witnessState: string | null;
  witnessReason: string | null;
  witnessQuotes: WitnessQuote[];
  breakerState: string | null;
  tier: { tier: string | null; trades: number | null; day: string | null; readyForOwnerReview: boolean | null; monthsOfData: number | null } | null;
  reconcile: { verdict: string | null; entries: number | null; day: string | null } | null;
}

/** REAL binding: reports/grok/M13_SOAK/soak_status.json. null when the shape is not recognisable. */
export function parseSoakStatus(raw: unknown, nowMs: number): PaperLedgerView | null {
  if (!isObj(raw) || typeof raw.soak !== "string") return null;
  const last = isObj(raw.last_cycle) ? raw.last_cycle : null;
  const led = isObj(raw.ledger_state) ? raw.ledger_state : null;
  if (!last && !led) return null;
  const lastTs = last ? str(last.ts) : null;
  const interval = num(raw.cycle_interval_sec);
  const staleMs = Math.max(SOAK_MIN_STALE_MS, interval === null ? 0 : interval * 2000);
  const paperOnly = raw.paper_only === true;
  const status: ChipStatus = paperOnly ? freshness("file", lastTs, nowMs, staleMs) : "UNKNOWN";
  const pos = led && isObj(led.position) ? led.position : null;
  const w = led && isObj(led.witness) ? led.witness : null;
  const quotes: WitnessQuote[] = w && Array.isArray(w.quotes)
    ? w.quotes.filter(isObj).map((q) => {
        const iso = epochIso(q.observed_at);
        return { provider: str(q.provider_id) ?? "-", instrument: str(q.instrument), priceUsd: num(q.price_usd), observedIso: iso, ageMin: ageMin(iso, nowMs) };
      })
    : [];
  const gate = isObj(raw.last_tier_gate) ? raw.last_tier_gate : null;
  const rec = isObj(raw.last_m42_reconcile) ? raw.last_m42_reconcile : null;
  const brk = led && isObj(led.breaker) ? str(led.breaker.state) : last && isObj(last.breaker) ? str(last.breaker.state) : null;
  const openFlag = last && typeof last.position_open === "boolean" ? last.position_open : pos ? true : led ? false : null;
  return {
    soak: raw.soak,
    paperOnly,
    status,
    lastCycleIso: lastTs,
    ageMin: ageMin(lastTs, nowMs),
    cycle: last ? num(last.cycle) : null,
    cyclesOk: num(raw.cycles_ok),
    cyclesFailed: num(raw.cycles_failed),
    equityUsd: led ? num(led.equity_usd) : last ? num(last.equity_usd) : null,
    bankrollUsd: led ? num(led.bankroll_usd) : null,
    cumulativeRealizedUsd: led ? num(led.cumulative_realized_pnl_usd) : null,
    closedTrades: led ? num(led.closed_trades) : null,
    settledTrades: led ? num(led.settled_trades) : null,
    positionOpen: openFlag,
    position: pos ? { entryPrice: num(pos.entry_price), execPrice: num(pos.exec_price), notionalUsd: num(pos.notional_usd), qtyOz: num(pos.qty_oz), entryIso: epochIso(pos.entry_ts), cycle: num(pos.cycle) } : null,
    unrealized: "UNKNOWN",
    witnessState: w ? str(w.state) : last ? str(last.witness_state) : null,
    witnessReason: redact(w ? str(w.reason) : last ? str(last.witness_reason) : null) || null,
    witnessQuotes: quotes,
    breakerState: brk,
    tier: gate ? { tier: str(gate.tier), trades: num(gate.trades), day: str(gate.day), readyForOwnerReview: typeof gate.ready_for_owner_review === "boolean" ? gate.ready_for_owner_review : null, monthsOfData: num(gate.months_of_data) } : null,
    reconcile: rec ? { verdict: str(rec.verdict), entries: num(rec.entries), day: str(rec.day) } : null,
  };
}

export interface JudgeView { verdict: string | null; closed: number | null; settled: number | null; invalidated: number | null; wins: number | null; losses: number | null; noPriceCycles: number | null; ledgerEntries: number | null }
/** Latest *_judge.md (M42 paper judge). Only copies numbers the file states. null when nothing matches. */
export function parseJudgeMd(text: string | null): JudgeView | null {
  if (!text) return null;
  const m = (re: RegExp) => text.match(re);
  const c = m(/closed trades:\s*(\d+)\s*\((\d+) settled,\s*(\d+) invalidated\)/i);
  const wl = m(/wins\s*\/\s*losses:\s*(\d+)\s*\/\s*(\d+)/i);
  const v = m(/\*\*Verdict:\s*([A-Z_]+)\*\*/);
  const np = m(/cycles with no corroborated price:\s*(\d+)/i);
  const le = m(/ledger entries:\s*(\d+)/i);
  if (!c && !wl && !v) return null;
  return {
    verdict: v ? v[1] : null,
    closed: c ? Number(c[1]) : null, settled: c ? Number(c[2]) : null, invalidated: c ? Number(c[3]) : null,
    wins: wl ? Number(wl[1]) : null, losses: wl ? Number(wl[2]) : null,
    noPriceCycles: np ? Number(np[1]) : null, ledgerEntries: le ? Number(le[1]) : null,
  };
}

/* ------------------------------------------------------------------ replay -- */

export interface ReplayRow { market: string; buyHold: string; bestBaseline: string; labPick: string; verdict: string; noProvenEdge: boolean }
export interface ReplaySummary { title: string | null; labelledNotLive: boolean; rows: ReplayRow[]; edge: "NO_PROVEN_EDGE" | "UNKNOWN" }
const cleanCell = (s: string): string => redact(s.replace(/\*\*/g, "").trim()).slice(0, 120);

/** Parses the "Summary - TEST, frozen pick vs passive" table of results.md. Copies cells verbatim; never recomputes. */
export function parseReplaySummary(text: string | null): ReplaySummary | null {
  if (!text || !text.trim()) return null;
  const lines = text.split(/\r?\n/);
  const title = lines.find((l) => /^#\s/.test(l))?.replace(/^#\s+/, "").trim() ?? null;
  const labelledNotLive = /REPLAY\s*[-\u2014]?\s*NOT LIVE/i.test(text);
  const hi = lines.findIndex((l) => /^\|\s*Market\s*\|/.test(l) && /Verdict/i.test(l));
  if (hi < 0) return null;
  const heads = lines[hi].split("|").slice(1, -1).map((h) => h.trim());
  const idx = (re: RegExp) => heads.findIndex((h) => re.test(h));
  const iBH = idx(/^Buy&hold/i), iBest = idx(/^Best baseline/i), iLab = idx(/^Lab pick/i), iV = idx(/^Verdict/i);
  if (iV < 0) return null;
  const rows: ReplayRow[] = [];
  for (let i = hi + 2; i < lines.length && lines[i].startsWith("|"); i++) {
    const cells = lines[i].split("|").slice(1, -1).map((c) => c.trim());
    if (cells.length !== heads.length || !cells[0]) continue;
    const verdict = cleanCell(cells[iV]);
    rows.push({
      market: cleanCell(cells[0]),
      buyHold: iBH >= 0 ? cleanCell(cells[iBH]) : "-",
      bestBaseline: iBest >= 0 ? cleanCell(cells[iBest]) : "-",
      labPick: iLab >= 0 ? cleanCell(cells[iLab]) : "-",
      verdict,
      noProvenEdge: verdict.length > 0 && verdict.split(/[\u00b7|]/).every((p) => /NO PROVEN EDGE/i.test(p)),
    });
  }
  if (rows.length === 0) return null;
  return { title: title ? redact(title) : null, labelledNotLive, rows, edge: rows.every((r) => r.noProvenEdge) ? "NO_PROVEN_EDGE" : "UNKNOWN" };
}

export interface TradesSummary { rows: number; byPeriod: Record<string, number>; bySystem: Record<string, number>; labels: string[]; firstEntry: string | null; lastExit: string | null }
/** out/<market>/trades.csv: counts only (no PnL aggregation, so nothing can read as green/red). null when malformed/empty. */
export function parseTradesCsv(text: string | null): TradesSummary | null {
  if (!text) return null;
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length < 2) return null;
  const head = lines[0].split(",").map((h) => h.trim());
  const iP = head.indexOf("period"), iS = head.indexOf("system"), iL = head.indexOf("label"), iE = head.indexOf("entry_date"), iX = head.indexOf("exit_date");
  if (iP < 0 || iS < 0 || iL < 0) return null;
  const out: TradesSummary = { rows: 0, byPeriod: {}, bySystem: {}, labels: [], firstEntry: null, lastExit: null };
  for (const l of lines.slice(1)) {
    const c = l.split(",");
    if (c.length !== head.length) return null;
    out.rows++;
    out.byPeriod[c[iP]] = (out.byPeriod[c[iP]] ?? 0) + 1;
    out.bySystem[c[iS]] = (out.bySystem[c[iS]] ?? 0) + 1;
    if (!out.labels.includes(c[iL])) out.labels.push(c[iL]);
    if (iE >= 0 && (out.firstEntry === null || c[iE] < out.firstEntry)) out.firstEntry = c[iE];
    if (iX >= 0 && (out.lastExit === null || c[iX] > out.lastExit)) out.lastExit = c[iX];
  }
  return out;
}

export interface LessonsSummary { title: string | null; sections: number }
export function parseLessons(text: string | null): LessonsSummary | null {
  if (!text || !text.trim()) return null;
  const lines = text.split(/\r?\n/);
  const title = lines.find((l) => /^#\s/.test(l))?.replace(/^#\s+/, "").trim() ?? null;
  return { title: title ? redact(title).slice(0, 160) : null, sections: lines.filter((l) => /^##\s/.test(l)).length };
}

/** Replay evidence is a file: status by file mtime (STALE keeps its age); never LIVE. */
export function replayAge(mtimeIso: string | null, nowMs: number): { status: ChipStatus; ageHours: number | null } {
  const a = ageMin(mtimeIso, nowMs);
  return { status: mtimeIso ? "STALE" : "UNKNOWN", ageHours: a === null ? null : Math.round((a / 60) * 10) / 10 };
}
