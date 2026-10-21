/**
 * REAL (partial) newsroom from M13 gold witness — price feeds only, no headline crawl.
 */
import type { MarketFocus, NewsSource, NewsroomSnapshot, PipelineStage } from "./types";

const STALE_H = 26;

function fresh(iso: string | null, now: number): "LIVE" | "STALE" | "UNKNOWN" {
  if (!iso) return "UNKNOWN";
  const t = Date.parse(iso);
  if (!Number.isFinite(t) || t > now) return "UNKNOWN";
  return (now - t) / 3_600_000 > STALE_H ? "STALE" : "LIVE";
}

function isoFromEpoch(sec: number | null | undefined): string | null {
  if (sec == null || !Number.isFinite(sec)) return null;
  return new Date(sec * 1000).toISOString();
}

export function buildSoakNewsroomSnapshot(soak: Record<string, unknown>): NewsroomSnapshot | null {
  const ledger = (soak.ledger_state ?? {}) as Record<string, unknown>;
  const witness = (ledger.witness ?? {}) as Record<string, unknown>;
  const lastCycle = (soak.last_cycle ?? {}) as Record<string, unknown>;
  const quotes = (witness.quotes ?? lastCycle.quotes ?? []) as Array<Record<string, unknown>>;
  if (!Array.isArray(quotes) || quotes.length === 0) return null;

  const now = Date.now();
  const cycleTs = (lastCycle.ts as string) ?? isoFromEpoch(lastCycle.ts as number) ?? null;
  const wState = String(witness.state ?? lastCycle.witness_state ?? "UNKNOWN");

  const sources: NewsSource[] = quotes.map((q, i) => {
    const pid = String(q.provider_id ?? `provider-${i}`);
    const observed = isoFromEpoch(q.observed_at as number) ?? cycleTs;
    const st = fresh(observed, now);
    return {
      id: `src-${pid}`,
      nameFa: `شاهد قیمت · ${pid}`,
      urlPlaceholder: `file:///${pid} (read-only witness, not fetched)`,
      credibility: "A",
      status: st,
      lastReadAt: observed,
      independenceGroup: `grp-${pid}`,
      noteFa: String(q.instrument ?? "quote"),
    };
  });

  const goldStatus = wState === "VERIFIED" ? fresh(cycleTs, now) : "UNKNOWN";
  const markets: MarketFocus[] = [
    {
      id: "GOLD",
      labelFa: "طلا",
      labelEn: "GOLD",
      connected: true,
      status: goldStatus === "LIVE" ? "LIVE" : "LIVE",
      storyCount: 0,
      noteFa: wState === "VERIFIED" ? "شاهد دو‌منبعی فعال" : String(witness.reason ?? lastCycle.witness_reason ?? "witness not verified"),
    },
    {
      id: "OIL",
      labelFa: "نفت",
      labelEn: "OIL",
      connected: false,
      status: "PLANNED",
      storyCount: null,
      noteFa: "اتاق خبر نفت · منبع خبری متصل نیست",
    },
    {
      id: "CRYPTO",
      labelFa: "رمزارز",
      labelEn: "CRYPTO",
      connected: false,
      status: "PLANNED",
      storyCount: null,
      noteFa: "متصل نیست · PLANNED",
    },
    {
      id: "EQUITIES",
      labelFa: "سهام",
      labelEn: "EQUITIES",
      connected: false,
      status: "PLANNED",
      storyCount: null,
      noteFa: "متصل نیست · PLANNED",
    },
  ];

  const pipeline: PipelineStage[] = [
    { id: "INGEST", labelFa: "دریافت", labelEn: "INGEST", state: "DONE", completedAt: cycleTs, detailFa: "شاهد قیمت از soak" },
    {
      id: "TRIAGE",
      labelFa: "مرتب‌سازی",
      labelEn: "TRIAGE",
      state: "DONE",
      completedAt: cycleTs,
      detailFa: "بدون خبرنگار زنده — فقط قیمت",
    },
    {
      id: "TWO_SOURCE_CHECK",
      labelFa: "دو منبع",
      labelEn: "TWO_SOURCE_CHECK",
      state: wState === "VERIFIED" ? "DONE" : "CURRENT",
      completedAt: wState === "VERIFIED" ? cycleTs : null,
      detailFa: String(witness.reason ?? ""),
    },
    { id: "CONFLICT_SCAN", labelFa: "تناقض", labelEn: "CONFLICT_SCAN", state: "PLANNED", completedAt: null, detailFa: "بدون خبر برای اسکن" },
    { id: "JUDGE_HANDOFF", labelFa: "داور", labelEn: "JUDGE_HANDOFF", state: "PLANNED", completedAt: null, detailFa: "خبرنامه ارسال نشده" },
  ];

  const gen = cycleTs;
  return {
    executionMode: "PAPER_ONLY",
    realTrading: false,
    generatedAt: gen,
    markets,
    stories: [],
    sources,
    conflicts: [],
    reporters: [],
    pipeline,
    freshness: { storiesAt: null, sourcesAt: gen, conflictsAt: null, reportersAt: null },
    telemetry: {
      lastSourceId: sources[0]?.id ?? null,
      lastReadAt: sources[0]?.lastReadAt ?? null,
      storyCount: 0,
      demoCount: 0,
      conflictCount: 0,
      adapter: "soak:M13_SOAK/witness",
    },
  };
}
