import { runCouncil, type CouncilResult } from "./council";
import type {
  Confidence,
  Decision,
  PairObservation,
  ScoredOpportunity,
  SecurityAssessment,
} from "./types";

/**
 * Evidence coverage — never treat missing fields as zero/safe.
 */
export function evidenceCoverage(token: PairObservation, security: SecurityAssessment | null): number {
  const fields: unknown[] = [
    token.priceUsd,
    token.liquidityUsd,
    token.volume24h,
    token.fdv,
    token.marketCap,
    token.priceChange24h,
    token.buys24h,
    token.sells24h,
    token.address,
    token.pairCreatedAt,
    security && security.status === "SUCCESS" ? true : null,
  ];
  const known = fields.filter((x) => x !== null && x !== undefined).length;
  return known / fields.length;
}

function pairAgeHours(token: PairObservation): number | null {
  if (!token.pairCreatedAt) return null;
  const t = new Date(token.pairCreatedAt).getTime();
  if (!Number.isFinite(t)) return null;
  return Math.max(0, (Date.now() - t) / 3_600_000);
}

function buySellImbalance(token: PairObservation): number | null {
  const b = token.buys24h;
  const s = token.sells24h;
  if (b == null || s == null) return null;
  const total = b + s;
  if (total <= 0) return null;
  return (b - s) / total; // +buy pressure, -sell pressure
}

function volLiqRatio(token: PairObservation): number | null {
  if (token.liquidityUsd == null || token.liquidityUsd <= 0 || token.volume24h == null) return null;
  return token.volume24h / token.liquidityUsd;
}

export function scoreToken(opts: {
  token: PairObservation;
  security: SecurityAssessment | null;
  fearGreed: number | null;
  newsHits: number;
  negativeNews: boolean;
}): ScoredOpportunity {
  const { token, security } = opts;
  const coverage = evidenceCoverage(token, security);
  const reasonsFa: string[] = [];
  const risksFa: string[] = [];
  const unknownsFa: string[] = [];
  const missingFa: string[] = [];
  const ageH = pairAgeHours(token);
  const imb = buySellImbalance(token);
  const vlr = volLiqRatio(token);

  // --- Market microstructure ---
  if (token.liquidityUsd != null) {
    if (token.liquidityUsd >= 100_000) reasonsFa.push(`نقدینگی قابل مشاهده ≈ ${Math.round(token.liquidityUsd).toLocaleString("en-US")} دلار.`);
    else if (token.liquidityUsd >= 25_000) reasonsFa.push(`نقدینگی متوسط ≈ ${Math.round(token.liquidityUsd).toLocaleString("en-US")} دلار.`);
    else risksFa.push(`نقدینگی نازک ≈ ${Math.round(token.liquidityUsd).toLocaleString("en-US")} دلار — ریسک خروج.`);
  } else {
    unknownsFa.push("نقدینگی UNKNOWN است و صفر فرض نشد.");
    missingFa.push("liquidityUsd");
  }

  if (token.volume24h != null) {
    reasonsFa.push(`حجم ۲۴س ≈ ${Math.round(token.volume24h).toLocaleString("en-US")} دلار (${token.source}).`);
  } else missingFa.push("volume24h");

  if (vlr != null) {
    if (vlr > 30) risksFa.push(`نسبت حجم/نقدینگی ${vlr.toFixed(1)} بسیار بالاست — احتمال واش‌ترید یا هیجان کاذب.`);
    else if (vlr > 12) risksFa.push(`نسبت حجم/نقدینگی ${vlr.toFixed(1)} بالاست — با احتیاط.`);
    else if (vlr >= 0.3 && vlr <= 8) reasonsFa.push(`نسبت حجم/نقدینگی ${vlr.toFixed(1)} در بازه معقول‌تر است.`);
  }

  if (imb != null) {
    if (imb < -0.35 && (token.sells24h ?? 0) > 30) risksFa.push(`فشار فروش مشهود (بازار خرید/فروش ${(imb * 100).toFixed(0)}٪ به نفع فروش).`);
    else if (imb > 0.35 && (token.buys24h ?? 0) > 30) reasonsFa.push(`فشار خرید نسبی مشاهده شد.`);
  } else if (token.buys24h == null || token.sells24h == null) {
    unknownsFa.push("جریان خرید/فروش ۲۴س UNKNOWN.");
  }

  if (ageH != null) {
    if (ageH < 2) risksFa.push(`استخر بسیار تازه (~${ageH.toFixed(1)} ساعت) — نویز لانچ بالا.`);
    else if (ageH < 24) risksFa.push(`استخر جوان (~${Math.round(ageH)} ساعت).`);
    else if (ageH >= 72) reasonsFa.push(`سن استخر ≈ ${Math.round(ageH / 24)} روز — کمی پایدارتر از لانچ لحظه‌ای.`);
  } else {
    unknownsFa.push("سن استخر UNKNOWN.");
    missingFa.push("pairCreatedAt");
  }

  // --- Anti-hype / paid promo ---
  if (token.paidPromotion) {
    risksFa.push("تبلیغ پولی (DexScreener Boost/Profile) — ویرالیتی ارگانیک نیست.");
  }
  const ch24 = token.priceChange24h;
  if (ch24 != null && ch24 > 100 && (token.liquidityUsd ?? 0) < 40_000) {
    risksFa.push(`جهش قیمت ${ch24.toFixed(0)}٪ با نقدینگی محدود — الگوی هایپ کلاسیک.`);
  }
  if (ch24 != null && ch24 > 200) {
    risksFa.push("مومنتوم افراطی ۲۴س — هرگز به‌تنهایی امتیاز مثبت نمی‌گیرد.");
  }

  // --- Security independent gate ---
  if (security?.honeypot === "YES") risksFa.push("هانی‌پات: YES");
  if (security?.sellable === "NO") risksFa.push("قابلیت فروش: NO");
  if (!security || security.status !== "SUCCESS") {
    unknownsFa.push("امنیت قرارداد SUCCESS نیست — SAFE ساخته نشد.");
    missingFa.push("security");
  } else if (security.flags.length) {
    risksFa.push(`پرچم امنیت: ${security.flags.slice(0, 6).join("، ")}`);
  } else {
    reasonsFa.push("GoPlus/RugCheck پرچم بحرانی گزارش نکرد (≠ SAFE کامل).");
  }

  if (token.priceUsd == null) missingFa.push("priceUsd");
  if (token.address == null) missingFa.push("contract");
  if (opts.newsHits === 0) unknownsFa.push("خبر اختصاصی توکن پیدا نشد.");
  if (opts.negativeNews) risksFa.push("خبر منفی مرتبط در چرخه فعلی.");

  // Multi-source discovery bonus (evidence, not hype)
  const multiSource = token.source.includes(",") || token.source.includes("+");
  if (multiSource) reasonsFa.push(`کشف چندمنبعی: ${token.source}.`);

  const council: CouncilResult = runCouncil({
    token,
    security,
    fearGreed: opts.fearGreed,
    newsHits: opts.newsHits,
    negativeNews: opts.negativeNews,
    paidPromo: token.paidPromotion,
  });

  // --- Decision (gates before rank) ---
  let decision: Decision = "INSUFFICIENT_EVIDENCE";
  if (security?.honeypot === "YES" || security?.sellable === "NO") {
    decision = "REJECT";
  } else if (token.paidPromotion && (token.liquidityUsd ?? 0) < 30_000) {
    decision = "REJECT";
  } else if (ch24 != null && ch24 > 150 && (token.liquidityUsd ?? 0) < 25_000) {
    decision = "REJECT";
  } else if (ageH != null && ageH < 1 && (token.liquidityUsd ?? 0) < 15_000) {
    decision = "REJECT";
  } else if (vlr != null && vlr > 40) {
    decision = "REJECT";
  } else if (council.verdict === "REJECT") {
    decision = "REJECT";
  } else if (coverage < 0.32) {
    decision = "INSUFFICIENT_EVIDENCE";
  } else if (council.verdict === "WATCH") {
    decision = "WATCH";
  } else if (council.verdict === "DISAGREEMENT") {
    decision = "ABSTAIN";
  } else {
    decision = "ABSTAIN";
  }

  // --- Multi-factor rank (anti highest-score-wins) ---
  const liqScore =
    token.liquidityUsd != null ? Math.min(Math.log10(Math.max(token.liquidityUsd, 1)) / 6.2, 1) : null;
  const volScore =
    token.volume24h != null ? Math.min(Math.log10(Math.max(token.volume24h, 1)) / 7.2, 1) : null;
  const secScore =
    security?.honeypot === "YES"
      ? 0
      : security?.status === "SUCCESS" && (security.flags?.length ?? 0) === 0
        ? 0.72
        : security?.status === "SUCCESS"
          ? 0.45
          : null;
  const ageScore =
    ageH == null ? null : ageH < 2 ? 0.15 : ageH < 24 ? 0.4 : ageH < 168 ? 0.7 : 0.85;
  const flowScore =
    imb == null ? null : Math.max(0, Math.min(1, 0.5 + imb * 0.5));
  const multiBonus = multiSource ? 0.08 : 0;
  const promoPenalty = token.paidPromotion ? 0.4 : 0;
  const momPenalty = ch24 != null && ch24 > 120 ? Math.min(0.35, (ch24 - 120) / 400) : 0;
  const vlrPenalty = vlr != null && vlr > 15 ? Math.min(0.3, (vlr - 15) / 50) : 0;

  const parts = [liqScore, volScore, secScore, coverage, ageScore, flowScore].filter(
    (x): x is number => x != null,
  );
  const rankScore =
    parts.length >= 2
      ? Math.max(
          0,
          Math.min(
            1,
            parts.reduce((a, b) => a + b, 0) / parts.length + multiBonus - promoPenalty - momPenalty - vlrPenalty,
          ),
        )
      : null;

  const confidence: Confidence =
    coverage >= 0.72 && (decision === "REJECT" || decision === "WATCH")
      ? "HIGH"
      : coverage >= 0.55
        ? "MED"
        : coverage >= 0.35
          ? "LOW"
          : "UNKNOWN";

  const invalidationFa =
    decision === "REJECT"
      ? "این کاندید هم‌اکنون رد است مگر شواهد امنیتی و نقدینگی جدید خلاف آن را ثابت کند."
      : "ابطال پایش: نقدینگی >۴۰٪ سقوط کند، هانی‌پات YES شود، فشار فروش شدید شود، یا خبر هک/راگ بیاید.";

  return {
    token,
    decision,
    rankScore,
    confidence,
    securityStatus:
      security?.honeypot === "YES"
        ? "HONEYPOT"
        : security?.status === "SUCCESS"
          ? "OBSERVED"
          : "UNKNOWN",
    evidenceCoverage: coverage,
    reasonsFa: reasonsFa.length ? reasonsFa : ["دلیل مثبت کافی ثبت نشد."],
    risksFa: risksFa.length ? risksFa : ["ریسک نامشخص — یعنی evidence ناقص، نه بی‌ریسک."],
    unknownsFa,
    invalidationFa,
    missingFa,
    councilVerdict: council.verdict,
    disagreement: council.disagreement,
    votes: council.votes,
    security,
  };
}

/**
 * Ranking: decision tier first (REJECT never rises above WATCH),
 * then evidence coverage, then multi-factor rankScore.
 * Anti-hype: numeric score alone never overrides security/liquidity gates.
 */
export function rankOpportunities(list: ScoredOpportunity[]): ScoredOpportunity[] {
  const order: Record<string, number> = {
    WATCH: 0,
    PAPER_CANDIDATE: 0,
    ABSTAIN: 1,
    INSUFFICIENT_EVIDENCE: 2,
    UNKNOWN: 3,
    REJECT: 4,
  };
  return [...list].sort((a, b) => {
    const d = (order[a.decision] ?? 9) - (order[b.decision] ?? 9);
    if (d !== 0) return d;
    const cov = b.evidenceCoverage - a.evidenceCoverage;
    if (Math.abs(cov) > 0.015) return cov;
    return (b.rankScore ?? -1) - (a.rankScore ?? -1);
  });
}
