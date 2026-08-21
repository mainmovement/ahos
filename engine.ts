import { db } from "@/db";
import {
  councilReports,
  cycles,
  expertVotes,
  findings,
  lessons,
  marketSnapshots,
  newsItems,
  observations,
  opportunities,
  outcomes,
  paperPositions,
  predictions,
  providerSnapshots,
  securityReports,
  systemState,
  tokens,
  watchlist,
} from "@/db/schema";
import { and, eq, isNull } from "drizzle-orm";
import { processOpportunityAlerts } from "./alerts";
import { collectNews } from "./news";
import { collectMarket, enrichPairs, fetchSecurity, mergePairs } from "./providers";
import { rankOpportunities, scoreToken } from "./scoring";
import type { Envelope, PairObservation, ScoredOpportunity } from "./types";

/** Base interval; stays continuous until stop. */
const INTERVAL_MS = 70_000;
/** Max concurrent security probes — speed without flooding GoPlus/RugCheck. */
const SECURITY_CONCURRENCY = 4;
const SECURITY_INSPECT_CAP = 10;
const CANDIDATE_CAP = 32;

type DaemonMem = {
  timer: ReturnType<typeof setInterval> | null;
  running: boolean;
  cycling: boolean;
  lastCycleId: number | null;
};

const g = globalThis as typeof globalThis & { __ahosDaemon?: DaemonMem };

function mem(): DaemonMem {
  if (!g.__ahosDaemon) {
    g.__ahosDaemon = { timer: null, running: false, cycling: false, lastCycleId: null };
  }
  return g.__ahosDaemon;
}

export async function ensureState() {
  const rows = await db.select().from(systemState).limit(1);
  if (!rows.length) {
    await db.insert(systemState).values({ id: 1, running: false, executionMode: "PAPER_ONLY" });
  }
}

export async function getState() {
  await ensureState();
  const rows = await db.select().from(systemState).limit(1);
  return rows[0];
}

export async function startEngine() {
  await ensureState();
  await db
    .update(systemState)
    .set({ running: true, startedAt: new Date(), stoppedAt: null, lastError: null, updatedAt: new Date() })
    .where(eq(systemState.id, 1));
  const m = mem();
  m.running = true;
  if (m.timer) clearInterval(m.timer);
  void runCycle("start");
  m.timer = setInterval(() => {
    if (mem().running) void runCycle("interval");
  }, INTERVAL_MS);
  return getState();
}

export async function stopEngine() {
  const m = mem();
  m.running = false;
  if (m.timer) {
    clearInterval(m.timer);
    m.timer = null;
  }
  await ensureState();
  await db
    .update(systemState)
    .set({ running: false, stoppedAt: new Date(), updatedAt: new Date() })
    .where(eq(systemState.id, 1));
  return getState();
}

export async function restoreDaemonIfNeeded() {
  const state = await getState();
  if (state.running && !mem().timer) {
    mem().running = true;
    mem().timer = setInterval(() => {
      if (mem().running) void runCycle("restore");
    }, INTERVAL_MS);
  }
}

/** Bounded parallel map for security — faster cycles, honest failures. */
async function mapPool<T, R>(items: T[], concurrency: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      results[idx] = await fn(items[idx]);
    }
  }
  const n = Math.min(concurrency, Math.max(1, items.length));
  await Promise.all(Array.from({ length: n }, () => worker()));
  return results;
}

export async function runCycle(reason: string) {
  const m = mem();
  if (m.cycling) return { skipped: true as const, reason: "already-running" };
  m.cycling = true;
  const started = Date.now();
  const [cycle] = await db
    .insert(cycles)
    .values({ status: "RUNNING", notesFa: `چرخه ${reason}` })
    .returning();

  try {
    const [market, news] = await Promise.all([collectMarket(), collectNews()]);
    let pairs = mergePairs(market.pairs);
    pairs = mergePairs(await enrichPairs(pairs));
    pairs = pickCandidates(pairs);

    await persistProviders(cycle.id, [...market.envelopes, ...news.envelopes], market.blocked);

    const btc = pickAsset(market.assets, "BTC");
    const eth = pickAsset(market.assets, "ETH");
    const sol = pickAsset(market.assets, "SOL");
    const regime = inferRegime(market.global.fearGreed, btc?.change24h ?? null);

    await db.insert(marketSnapshots).values({
      cycleId: cycle.id,
      regime,
      fearGreed: market.global.fearGreed,
      fearGreedLabel: market.global.fearGreedLabel,
      btcPrice: btc?.priceUsd ?? null,
      btcChange24h: btc?.change24h ?? null,
      ethPrice: eth?.priceUsd ?? null,
      ethChange24h: eth?.change24h ?? null,
      solPrice: sol?.priceUsd ?? null,
      solChange24h: sol?.change24h ?? null,
      totalMcap: market.global.totalMcap,
      mcapChange24h: market.global.mcapChange24h,
      btcDominance: market.global.btcDominance,
      defiTvl: market.global.defiTvl,
      payload: {
        mempoolFee: market.global.mempoolFee,
        btcHash: market.global.btcHash,
        assetCount: market.assets.length,
        pairCount: pairs.length,
      },
      provenance: {
        sources: [...new Set(market.envelopes.filter((e) => e.status === "SUCCESS").map((e) => e.provider))],
      },
    });

    for (const story of news.stories) {
      await db
        .insert(newsItems)
        .values({
          fingerprint: story.fingerprint,
          source: story.source,
          sourceUrl: story.sourceUrl,
          titleOriginal: story.titleOriginal,
          titleFa: story.titleFa,
          summaryFa: story.summaryFa,
          publishedAt: story.publishedAt ? new Date(story.publishedAt) : null,
          importance: story.importance,
          category: story.category,
          sentiment: story.sentiment,
          relatedTokens: story.relatedTokens,
          relatedChains: story.relatedChains,
          impact: story.impact,
          provenance: { engine: "rss+glossary/MyMemory" },
        })
        .onConflictDoNothing();
    }

    for (const token of pairs) {
      await db
        .insert(tokens)
        .values({
          key: token.tokenKey,
          symbol: token.symbol,
          name: token.name,
          chain: token.chain,
          address: token.address,
          pairAddress: token.pairAddress,
          dexId: token.dexId,
          url: token.url,
          imageUrl: token.imageUrl,
        })
        .onConflictDoNothing();
      await db
        .update(tokens)
        .set({ lastSeenAt: new Date(), name: token.name, url: token.url, imageUrl: token.imageUrl })
        .where(eq(tokens.key, token.tokenKey));

      await db.insert(observations).values({
        cycleId: cycle.id,
        tokenKey: token.tokenKey,
        priceUsd: token.priceUsd,
        liquidityUsd: token.liquidityUsd,
        volume24h: token.volume24h,
        fdv: token.fdv,
        marketCap: token.marketCap,
        priceChange5m: token.priceChange5m,
        priceChange1h: token.priceChange1h,
        priceChange6h: token.priceChange6h,
        priceChange24h: token.priceChange24h,
        buys24h: token.buys24h,
        sells24h: token.sells24h,
        pairCreatedAt: token.pairCreatedAt ? new Date(token.pairCreatedAt) : null,
        boostActive: token.boostActive,
        paidPromotion: token.paidPromotion,
        source: token.source,
        raw: { labels: token.labels },
      });
    }

    const inspect = pairs.slice(0, SECURITY_INSPECT_CAP);
    const securityMap = new Map<string, Awaited<ReturnType<typeof fetchSecurity>>>();
    const secResults = await mapPool(inspect, SECURITY_CONCURRENCY, async (token) => {
      const sec = await fetchSecurity(token);
      return { tokenKey: token.tokenKey, sec };
    });
    for (const { tokenKey, sec } of secResults) {
      securityMap.set(tokenKey, sec);
      await db.insert(securityReports).values({
        tokenKey,
        provider: sec.provider,
        status: sec.status,
        honeypot: sec.honeypot,
        sellable: sec.sellable,
        mintable: sec.mintable,
        freezeable: sec.freezeable,
        ownership: sec.ownership,
        summaryFa: sec.summaryFa,
        payload: { flags: sec.flags, raw: sec.raw },
      });
    }

    const scored: ScoredOpportunity[] = [];
    for (const token of pairs) {
      const hits = news.stories.filter(
        (n) =>
          n.relatedTokens.includes(token.symbol) ||
          n.titleOriginal.toUpperCase().includes(token.symbol) ||
          n.titleFa.includes(token.symbol),
      );
      const negativeNews = hits.some((n) => n.sentiment === "NEG" || n.category.includes("هک"));
      const opp = scoreToken({
        token,
        security: securityMap.get(token.tokenKey) ?? null,
        fearGreed: market.global.fearGreed,
        newsHits: hits.length,
        negativeNews,
      });
      scored.push(opp);
    }

    const ranked = rankOpportunities(scored).slice(0, 40);
    for (const opp of ranked) {
      const [row] = await db
        .insert(opportunities)
        .values({
          cycleId: cycle.id,
          tokenKey: opp.token.tokenKey,
          symbol: opp.token.symbol,
          name: opp.token.name,
          chain: opp.token.chain,
          address: opp.token.address,
          decision: opp.decision,
          rankScore: opp.rankScore,
          confidence: opp.confidence,
          securityStatus: opp.securityStatus,
          evidenceCoverage: opp.evidenceCoverage,
          reasonsFa: opp.reasonsFa,
          risksFa: opp.risksFa,
          unknownsFa: opp.unknownsFa,
          invalidationFa: opp.invalidationFa,
          missingFa: opp.missingFa,
          councilVerdict: opp.councilVerdict,
          disagreement: opp.disagreement,
          payload: {
            source: opp.token.source,
            priceUsd: opp.token.priceUsd,
            liquidityUsd: opp.token.liquidityUsd,
            volume24h: opp.token.volume24h,
            priceChange24h: opp.token.priceChange24h,
            url: opp.token.url,
            paidPromotion: opp.token.paidPromotion,
            teamTally: tally(opp.votes),
          },
        })
        .returning();

      const sampleVotes = sampleTeamVotes(opp.votes);
      if (sampleVotes.length) {
        await db.insert(expertVotes).values(
          sampleVotes.map((v) => ({
            cycleId: cycle.id,
            tokenKey: opp.token.tokenKey,
            expertId: v.expertId,
            teamId: v.teamId,
            expertNameFa: v.expertNameFa,
            vote: v.vote,
            confidence: v.confidence,
            reasonFa: v.reasonFa,
            uncertaintyFa: v.uncertaintyFa,
          })),
        );
      }
      await db.insert(councilReports).values({
        cycleId: cycle.id,
        tokenKey: opp.token.tokenKey,
        verdict: opp.councilVerdict,
        agreeCount: opp.votes.filter((v) => v.vote === "WATCH").length,
        rejectCount: opp.votes.filter((v) => v.vote === "REJECT").length,
        abstainCount: opp.votes.filter((v) => v.vote === "ABSTAIN" || v.vote === "UNKNOWN").length,
        watchCount: opp.votes.filter((v) => v.vote === "WATCH").length,
        summaryFa: `${opp.token.symbol}: ${opp.councilVerdict}. اختلاف=${opp.disagreement ? "بله" : "کم"}.`,
        disagreementFa: [...new Set(opp.votes.map((v) => v.vote))],
      });

      if (opp.decision === "WATCH" && opp.token.priceUsd != null) {
        await db.insert(predictions).values({
          cycleId: cycle.id,
          tokenKey: opp.token.tokenKey,
          symbol: opp.token.symbol,
          decision: opp.decision,
          rankScore: opp.rankScore,
          confidence: opp.confidence,
          horizonMin: 240,
          entryPrice: opp.token.priceUsd,
          evidence: { opportunityId: row.id, coverage: opp.evidenceCoverage },
          source: "local",
        });
      }
    }

    // W45: critical opportunity alerts → web state + optional Telegram (env secrets only)
    let alertMeta: { count: number; telegramOk: number } = { count: 0, telegramOk: 0 };
    try {
      const alertResult = await processOpportunityAlerts(ranked);
      alertMeta = {
        count: alertResult.emitted.length,
        telegramOk: alertResult.telegram.filter((t) => t.ok).length,
      };
    } catch {
      /* alert path must never fail the cycle */
    }

    await markPaperPrices(pairs);
    await resolvePredictions(pairs);
    await writeFindings(cycle.id, market.envelopes, news.envelopes, ranked);

    const unknownShare =
      ranked.length === 0
        ? 1
        : ranked.filter((o) => o.decision === "INSUFFICIENT_EVIDENCE" || o.confidence === "UNKNOWN").length /
          ranked.length;

    const durationMs = Date.now() - started;
    await db
      .update(cycles)
      .set({
        status: "SUCCESS",
        finishedAt: new Date(),
        durationMs,
        tokenCount: pairs.length,
        newsCount: news.stories.length,
        opportunityCount: ranked.length,
        unknownShare,
        notesFa: `چرخه کامل. توکن=${pairs.length} خبر=${news.stories.length} فرصت=${ranked.length} هشدار=${alertMeta.count} زمان=${durationMs}ms`,
        details: {
          reason,
          securityInspected: inspect.length,
          parallelSecurity: SECURITY_CONCURRENCY,
          alerts: alertMeta,
        },
      })
      .where(eq(cycles.id, cycle.id));

    const prev = await getState();
    await db
      .update(systemState)
      .set({
        lastCycleAt: new Date(),
        lastCycleStatus: "SUCCESS",
        cycleCount: (prev.cycleCount || 0) + 1,
        lastError: null,
        updatedAt: new Date(),
      })
      .where(eq(systemState.id, 1));

    m.lastCycleId = cycle.id;
    return { skipped: false as const, cycleId: cycle.id, durationMs, alerts: alertMeta };
  } catch (error) {
    const message = error instanceof Error ? error.message : "UNKNOWN";
    await db
      .update(cycles)
      .set({
        status: "CODE_FAILURE",
        finishedAt: new Date(),
        durationMs: Date.now() - started,
        notesFa: `شکست چرخه: ${message}`,
      })
      .where(eq(cycles.id, cycle.id));
    await db
      .update(systemState)
      .set({ lastCycleStatus: "CODE_FAILURE", lastError: message, lastCycleAt: new Date(), updatedAt: new Date() })
      .where(eq(systemState.id, 1));
    return { skipped: false as const, error: message };
  } finally {
    m.cycling = false;
  }
}

function pickAsset(assets: { symbol: string; priceUsd: number | null; change24h: number | null }[], symbol: string) {
  return assets.find((a) => a.symbol === symbol && a.priceUsd != null);
}

function inferRegime(fg: number | null, btcChange: number | null): string {
  if (fg == null && btcChange == null) return "UNKNOWN";
  if ((fg ?? 50) >= 75) return "EXTREME_GREED";
  if ((fg ?? 50) <= 25) return "EXTREME_FEAR";
  if ((btcChange ?? 0) > 3) return "RISK_ON";
  if ((btcChange ?? 0) < -3) return "RISK_OFF";
  return "RANGE";
}

function pickCandidates(pairs: PairObservation[]): PairObservation[] {
  const scored = pairs.map((p) => {
    let w = 0;
    if (p.liquidityUsd != null) w += Math.min(p.liquidityUsd / 40_000, 3.5);
    if (p.volume24h != null) w += Math.min(p.volume24h / 60_000, 3);
    if (p.source.includes("GeckoTerminal")) w += 0.5;
    if (p.source.includes("DexScreener")) w += 0.45;
    if (p.source.includes("Pump.fun")) w += 0.25;
    if (p.source.includes(",") || p.source.includes("+")) w += 0.8;
    if (p.address) w += 0.35;
    if (p.pairCreatedAt) w += 0.2;
    if (p.paidPromotion) w -= 1.5;
    if ((p.priceChange24h ?? 0) > 200 && (p.liquidityUsd ?? 0) < 20_000) w -= 1.2;
    return { p, w };
  });
  scored.sort((a, b) => b.w - a.w);
  const uniq: PairObservation[] = [];
  const seen = new Set<string>();
  for (const row of scored) {
    if (seen.has(row.p.tokenKey)) continue;
    seen.add(row.p.tokenKey);
    uniq.push(row.p);
    if (uniq.length >= CANDIDATE_CAP) break;
  }
  return uniq;
}

async function persistProviders(
  cycleId: number,
  envelopes: Envelope<unknown>[],
  blocked: Array<{ provider: string; status: string; reasonFa: string }>,
) {
  const rows = [
    ...envelopes.map((e) => ({
      cycleId,
      provider: e.provider,
      category: e.category,
      status: e.status,
      latencyMs: e.latencyMs,
      itemCount: e.itemCount,
      messageFa: e.messageFa,
      messageEn: e.messageEn,
      provenance: { url: e.url, fetchedAt: e.fetchedAt },
    })),
    ...blocked.map((b) => ({
      cycleId,
      provider: b.provider,
      category: "blocked",
      status: b.status,
      latencyMs: 0,
      itemCount: 0,
      messageFa: b.reasonFa,
      messageEn: b.status,
      provenance: { declared: true },
    })),
  ];
  if (rows.length) await db.insert(providerSnapshots).values(rows);
}

function tally(votes: ScoredOpportunity["votes"]) {
  const teams: Record<string, Record<string, number>> = {};
  for (const v of votes) {
    teams[v.teamId] ||= {};
    teams[v.teamId][v.vote] = (teams[v.teamId][v.vote] || 0) + 1;
  }
  return teams;
}

function sampleTeamVotes(votes: ScoredOpportunity["votes"]) {
  const out: typeof votes = [];
  const byTeam = new Map<string, typeof votes>();
  for (const v of votes) {
    const list = byTeam.get(v.teamId) || [];
    list.push(v);
    byTeam.set(v.teamId, list);
  }
  for (const list of byTeam.values()) {
    const reject = list.find((v) => v.vote === "REJECT");
    const abstain = list.find((v) => v.vote === "ABSTAIN");
    const watch = list.find((v) => v.vote === "WATCH");
    for (const v of [reject, abstain, watch]) if (v) out.push(v);
  }
  return out;
}

async function markPaperPrices(pairs: PairObservation[]) {
  const open = await db.select().from(paperPositions).where(eq(paperPositions.status, "OPEN"));
  const watched = await db.select().from(watchlist).where(eq(watchlist.active, true));
  for (const pos of open) {
    const p = pairs.find((x) => x.tokenKey === pos.tokenKey || x.symbol === pos.symbol);
    if (!p || p.priceUsd == null || pos.entryPrice == null) continue;
    const ret = (p.priceUsd - pos.entryPrice) / pos.entryPrice;
    const maxF = Math.max(pos.maxFavorable ?? 0, ret);
    const maxA = Math.min(pos.maxAdverse ?? 0, ret);
    await db
      .update(paperPositions)
      .set({ lastPrice: p.priceUsd, maxFavorable: maxF, maxAdverse: maxA })
      .where(eq(paperPositions.id, pos.id));
  }
  for (const w of watched) {
    await db.update(watchlist).set({ updatedAt: new Date() }).where(eq(watchlist.id, w.id));
  }
}

async function resolvePredictions(pairs: PairObservation[]) {
  const open = await db
    .select()
    .from(predictions)
    .where(and(isNull(predictions.resolvedAt), eq(predictions.source, "local")))
    .limit(40);
  const now = Date.now();
  for (const pred of open) {
    const ageMin = (now - pred.createdAt.getTime()) / 60000;
    if (ageMin < pred.horizonMin) continue;
    const p = pairs.find((x) => x.tokenKey === pred.tokenKey);
    if (!p || p.priceUsd == null || pred.entryPrice == null) {
      await db.insert(outcomes).values({
        predictionId: pred.id,
        tokenKey: pred.tokenKey,
        horizonMin: pred.horizonMin,
        startPrice: pred.entryPrice,
        endPrice: null,
        hit: "UNKNOWN",
        errorClass: "INSUFFICIENT_EVIDENCE",
        lessonFa: "در پایان افق قیمت واقعی برای مقایسه نبود — نتیجه جعل نشد.",
      });
      await db.update(predictions).set({ resolvedAt: new Date() }).where(eq(predictions.id, pred.id));
      continue;
    }
    const ret = (p.priceUsd - pred.entryPrice) / pred.entryPrice;
    const hit = ret >= 0.08 ? "YES" : ret <= -0.12 ? "NO" : "UNKNOWN";
    const errorClass = hit === "NO" ? "FALSE_POSITIVE" : hit === "YES" ? "NONE" : "INSUFFICIENT_EVIDENCE";
    const lessonFa =
      hit === "YES"
        ? `${pred.symbol}: اگر کاغذی خریده می‌شد تا افق ${pred.horizonMin}د حدود ${Math.round(ret * 100)}٪ جلو می‌رفت. این یک outcome است نه توصیه.`
        : hit === "NO"
          ? `${pred.symbol}: پایش WATCH در این افق نامساعد بود (${Math.round(ret * 100)}٪). درس: مومنتوم بدون امنیت/نقدینگی کافی را بالا نیاور.`
          : `${pred.symbol}: حرکت داخل باند افق بود — برای طبقه‌بندی خطا شواهد ناکافی است.`;
    await db.insert(outcomes).values({
      predictionId: pred.id,
      tokenKey: pred.tokenKey,
      horizonMin: pred.horizonMin,
      startPrice: pred.entryPrice,
      endPrice: p.priceUsd,
      maxFavorable: ret > 0 ? ret : 0,
      maxAdverse: ret < 0 ? ret : 0,
      hit,
      errorClass,
      lessonFa,
    });
    await db.insert(lessons).values({
      titleFa: `درس افق ${pred.horizonMin}د برای ${pred.symbol}`,
      bodyFa: lessonFa,
      errorClass,
      tokenKey: pred.tokenKey,
    });
    await db.update(predictions).set({ resolvedAt: new Date() }).where(eq(predictions.id, pred.id));
  }
}

async function writeFindings(
  cycleId: number,
  marketEnv: Envelope<unknown>[],
  newsEnv: Envelope<unknown>[],
  ranked: ScoredOpportunity[],
) {
  const down = [...marketEnv, ...newsEnv].filter((e) => e.status === "DOWN");
  if (down.length >= 5) {
    await db.insert(findings).values({
      findingId: `F-DOWN-${cycleId}`,
      severity: "MED",
      titleFa: "چندین پروایدر DOWN شدند",
      evidenceFa: down.slice(0, 8).map((d) => `${d.provider}:${d.status}`).join("، "),
      confidence: "HIGH",
      status: "OPEN",
    });
  }
  const unknownSec = ranked.filter((r) => r.securityStatus === "UNKNOWN").length;
  if (ranked.length && unknownSec / ranked.length > 0.7) {
    await db.insert(findings).values({
      findingId: `F-SEC-${cycleId}`,
      severity: "HIGH",
      titleFa: "سهم امنیت UNKNOWN بالاست",
      evidenceFa: `${unknownSec} از ${ranked.length} فرصت بدون امنیت SUCCESS. UNKNOWN ≠ SAFE.`,
      confidence: "HIGH",
      status: "OPEN",
    });
  }
  const watchN = ranked.filter((r) => r.decision === "WATCH").length;
  const rejectN = ranked.filter((r) => r.decision === "REJECT").length;
  if (ranked.length >= 5 && rejectN > watchN * 2) {
    await db.insert(findings).values({
      findingId: `F-HYPER-${cycleId}`,
      severity: "LOW",
      titleFa: "فیلتر ضدهایپ فعال — ردها بیشتر از پایش",
      evidenceFa: `WATCH=${watchN} REJECT=${rejectN}. سیستم در حال رد فرصت‌های پرریسک است.`,
      confidence: "MED",
      status: "OPEN",
    });
  }
}

export async function addWatch(input: {
  tokenKey: string;
  symbol: string;
  chain: string;
  address?: string | null;
  thesisFa?: string;
}) {
  await db
    .insert(watchlist)
    .values({
      tokenKey: input.tokenKey,
      symbol: input.symbol,
      chain: input.chain,
      address: input.address ?? null,
      thesisFa: input.thesisFa ?? "پایش کاغذی به درخواست کاربر",
      invalidationFa: "اگر امنیت YES honeypot شود یا نقدینگی فرو بریزد.",
      active: true,
    })
    .onConflictDoNothing();
  await db
    .update(watchlist)
    .set({ active: true, thesisFa: input.thesisFa ?? "پایش کاغذی به درخواست کاربر", updatedAt: new Date() })
    .where(eq(watchlist.tokenKey, input.tokenKey));
}

export async function addPaper(input: {
  tokenKey: string;
  symbol: string;
  chain: string;
  address?: string | null;
  quantity?: number | null;
  entryPrice?: number | null;
  thesisFa?: string;
  targetPrice?: number | null;
}) {
  const [row] = await db
    .insert(paperPositions)
    .values({
      tokenKey: input.tokenKey,
      symbol: input.symbol,
      chain: input.chain,
      address: input.address ?? null,
      quantity: input.quantity ?? null,
      entryPrice: input.entryPrice ?? null,
      lastPrice: input.entryPrice ?? null,
      thesisFa: input.thesisFa ?? "موقعیت کاغذی — خرید واقعی انجام نشد",
      invalidationFa: "ابطال اگر قیمت ورود نامعتبر شود یا امنیت رد شود",
      targetPrice: input.targetPrice ?? null,
      status: "OPEN",
    })
    .returning();
  return row;
}
