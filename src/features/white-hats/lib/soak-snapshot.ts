/**
 * Map M13_SOAK artifacts → WhiteHatsSnapshot (read-only, PAPER_ONLY).
 * Missing fields stay null/empty — never invented.
 */
import { parseVerdict } from "../../missions-b5/lib/model";
import type {
  Breaker,
  Inspector,
  TimelineEvent,
  Verdict,
  WhiteHatsSnapshot,
} from "../types";

const STALE_HOURS = 26;

function freshOf(iso: string | null, nowMs: number): "LIVE" | "STALE" | "UNKNOWN" {
  if (!iso) return "UNKNOWN";
  const t = Date.parse(iso);
  if (!Number.isFinite(t) || t > nowMs) return "UNKNOWN";
  const h = (nowMs - t) / 3_600_000;
  return h > STALE_HOURS ? "STALE" : "LIVE";
}

function mapVerdict(token: string | null): Verdict {
  if (!token) return "UNKNOWN";
  if (["CLEAN", "PASS", "PASSED", "OK"].includes(token)) return "CLEAN";
  if (["HALT", "HALTED", "BLOCKED"].includes(token)) return "BLOCKED";
  if (["DISCREPANCY", "FAIL", "FAILED", "CONFLICT", "TAMPERED"].includes(token)) return "FINDING";
  return "UNKNOWN";
}

export function buildSoakWhiteHatsSnapshot(input: {
  soak: Record<string, unknown>;
  judgeText: string | null;
  reconcileText: string | null;
  generatedAt: string | null;
  sourceLabel: string;
}): WhiteHatsSnapshot {
  const now = Date.now();
  const gen = input.generatedAt;
  const fresh = freshOf(gen, now);
  const lastCycle = (input.soak.last_cycle ?? {}) as Record<string, unknown>;
  const ledger = (input.soak.ledger_state ?? {}) as Record<string, unknown>;
  const br = (ledger.breaker ?? {}) as Record<string, unknown>;
  const m42 = (input.soak.last_m42_reconcile ?? {}) as Record<string, unknown>;
  const witness = (lastCycle.witness_state as string) ?? (ledger.witness as Record<string, unknown> | undefined)?.state;

  const judgeTok = parseVerdict(input.judgeText);
  const reconTok = parseVerdict(input.reconcileText);
  const judgeV = mapVerdict(judgeTok);
  const reconV = mapVerdict(reconTok);

  const inspectors: Inspector[] = [
    {
      id: "insp-m42-reconcile",
      kind: "paper-invariant",
      title: "M42 ledger reconcile",
      status: reconV === "CLEAN" && fresh === "LIVE" ? "LIVE" : reconV === "CLEAN" ? fresh : "UNKNOWN",
      lastRunAt: (m42.ts as string) ?? gen,
      passes: reconV === "CLEAN" ? 1 : 0,
      failures: reconV === "FINDING" ? 1 : 0,
      note: reconTok ? `verdict ${reconTok}` : "no reconcile verdict parsed",
      demo: false,
    },
    {
      id: "insp-gold-witness",
      kind: "two-source-price",
      title: "Gold witness (2-source)",
      status: witness === "VERIFIED" && fresh === "LIVE" ? "LIVE" : witness === "VERIFIED" ? fresh : "UNKNOWN",
      lastRunAt: (lastCycle.ts as string) ?? null,
      passes: witness === "VERIFIED" ? 1 : 0,
      failures: witness === "UNRESOLVED" || witness === "CONFLICT" ? 1 : 0,
      note: String(lastCycle.witness_reason ?? "").slice(0, 120) || undefined,
      demo: false,
    },
    {
      id: "insp-nightly-judge",
      kind: "data-sanity",
      title: "Nightly soak judge",
      status: judgeV === "CLEAN" && fresh === "LIVE" ? "LIVE" : judgeV === "CLEAN" ? fresh : "UNKNOWN",
      lastRunAt: gen,
      passes: judgeV === "CLEAN" ? 1 : 0,
      failures: judgeV === "FINDING" ? 1 : 0,
      demo: false,
    },
  ];

  const breaker: Breaker = {
    state: br.state === "ARMED" ? "ARMED" : br.state === "TRIPPED" ? "TRIPPED" : "UNKNOWN",
    updatedAt: (lastCycle.ts as string) ?? gen,
    limits: [
      {
        key: "drawdown",
        label: "Drawdown",
        unit: "%",
        current: Number(br.drawdown_pct ?? ledger.drawdown_pct ?? 0) || 0,
        limit: 100,
      },
      {
        key: "exposure",
        label: "Open exposure",
        unit: "%",
        current: Number(br.open_exposure_pct ?? 0) || 0,
        limit: 100,
      },
    ],
    demo: false,
  };

  const headHash = String(m42.head_hash ?? "").slice(0, 16);
  const timelines: Record<string, TimelineEvent[]> = {
    default: [
      {
        id: "tl-judge-latest",
        kind: "judge",
        at: gen,
        actor: "M13 soak judge",
        title: judgeTok ? `Judge ${judgeTok}` : "Judge (unparsed)",
        detail: input.sourceLabel,
        verdict: judgeV,
        demo: false,
      },
    ],
  };

  return {
    schemaVersion: 1,
    sourceId: input.sourceLabel,
    executionMode: "PAPER_ONLY",
    realTrading: false,
    fetchedAt: gen,
    freshness: fresh,
    demo: false,
    decisions: [],
    inspectors,
    findings: [],
    breaker,
    canary: null,
    timelines,
    evidence: headHash
      ? {
          "ev-m42-head": {
            id: "ev-m42-head",
            kind: "ledger-head",
            hash: headHash,
            capturedAt: (m42.ts as string) ?? gen,
            sourceId: "M42 reconcile",
            excerpt: "hash prefix only; full chain on disk",
            demo: false,
          },
        }
      : {},
  };
}
