import type { NewsCenterSnapshot, NewsItem, NewsTopic } from "../contract/types";

const STALE_AFTER_MIN = 120;

function isoFromEpoch(sec: number | null | undefined): string | null {
  if (sec == null || !Number.isFinite(sec)) return null;
  return new Date(sec * 1000).toISOString();
}

function clip(s: string, max = 120): string {
  const t = s.trim();
  return t.length <= max ? t : `${t.slice(0, max - 1)}…`;
}

function topicForProvider(pid: string): NewsTopic {
  if (/oil|brent|wti/i.test(pid)) return "Oil";
  if (/gold|gc|xau/i.test(pid)) return "Gold";
  if (/macro|fred|cpi/i.test(pid)) return "Macro";
  return "Other";
}

/** Price-witness rows only — no headline crawl (M18.N calm center). */
export function buildNewsCenterFromSoak(
  status: Record<string, unknown>,
  generatedAt: string,
): NewsCenterSnapshot | null {
  const ledger = (status.ledger_state ?? {}) as Record<string, unknown>;
  const witness = (ledger.witness ?? {}) as Record<string, unknown>;
  const lastCycle = (status.last_cycle ?? {}) as Record<string, unknown>;
  const quotes = (witness.quotes ?? lastCycle.quotes) as Array<Record<string, unknown>> | undefined;
  const cycleTs = typeof lastCycle.ts === "string" ? lastCycle.ts : generatedAt;
  const items: NewsItem[] = [];

  if (Array.isArray(quotes)) {
    for (let i = 0; i < quotes.length; i++) {
      const q = quotes[i];
      const pid = String(q.provider_id ?? `provider-${i}`);
      const observed = isoFromEpoch(q.observed_at as number) ?? cycleTs;
      const price = q.price_usd;
      const priceBit = typeof price === "number" && Number.isFinite(price) ? ` · $${price.toFixed(2)}` : "";
      const inst = String(q.instrument ?? "quote");
      items.push({
        id: `NW-WIT-${pid}`,
        time: observed,
        sourceName: pid,
        topic: topicForProvider(pid),
        summary: clip(`شاهد قیمت ${inst} ثبت شد (M13، بدون خبر زنده)${priceBit}`),
        reliability: witness.state === "VERIFIED" ? "دو‌منبعی" : null,
        demo: false,
      });
    }
  }

  if (items.length === 0 && lastCycle && typeof lastCycle === "object") {
    const w = String(lastCycle.witness_state ?? "UNKNOWN");
    const reason = typeof lastCycle.witness_reason === "string" ? lastCycle.witness_reason : "";
    items.push({
      id: "NW-CYCLE",
      time: cycleTs,
      sourceName: "M13_SOAK",
      topic: "Gold",
      summary: clip(`چرخه soak: witness=${w}. ${reason}`),
      reliability: w === "VERIFIED" ? "دو‌منبعی" : null,
      demo: false,
    });
  }

  if (items.length === 0) return null;

  const gen =
    items.map((it) => it.time).filter((t): t is string => !!t).sort().at(-1) ?? generatedAt;

  return {
    kind: "newsCenter",
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "M13_SOAK soak_status.json · witness quotes",
    generatedAt: gen,
    demo: false,
    staleAfterMinutes: STALE_AFTER_MIN,
    items,
  };
}
