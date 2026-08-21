import { runCouncil, type CouncilResult } from "./council";
import type {
  Confidence,
  Decision,
  PairObservation,
  ScoredOpportunity,
  SecurityAssessment,
} from "./types";

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

  if (token.liquidityUsd != null) {
    if (token.liquidityUsd >= 50000) reasonsFa.push(`نقدینگی مشاهده‌شده ${Math.round(token.liquidityUsd)} دلار.`);
    else risksFa.push(`نقدینگی فقط ${Math.round(token.liquidityUsd)} دلار است.`);
  } else {
    unknownsFa.push("نقدینگی UNKNOWN است و صفر فرض نشد.");
    missingFa.push("liquidityUsd");
  }
  if (token.volume24h != null) reasonsFa.push(`حجم ۲۴ساعته ${Math.round(token.volume24h)} دلار از منبع ${token.source}.`);
  else missingFa.push("volume24h");
  if (token.paidPromotion) {
    risksFa.push("تبلیغ پولی DexScreener Boost مشاهده شد — ویرالیتی ارگانیک نیست.");
  }
  if (security?.honeypot === "YES") risksFa.push("هانی‌پات: YES");
  if (!security || security.status !== "SUCCESS") {
    unknownsFa.push("امنیت قرارداد SUCCESS نیست — SAFE ساخته نشد.");
    missingFa.push("security");
  } else if (security.flags.length) {
    risksFa.push(`پرچم امنیت: ${security.flags.join("، ")}`);
  }
  if (token.priceUsd == null) missingFa.push("priceUsd");
  if (token.address == null) missingFa.push("contract");
  if (opts.newsHits === 0) unknownsFa.push("خبر اختصاصی توکن پیدا نشد.");
  if (opts.negativeNews) risksFa.push("خبر منفی مرتبط در چرخه فعلی.");

  const council: CouncilResult = runCouncil({
    token,
    security,
    fearGreed: opts.fearGreed,
    newsHits: opts.newsHits,
    negativeNews: opts.negativeNews,
    paidPromo: token.paidPromotion,
  });

  let decision: Decision = "INSUFFICIENT_EVIDENCE";
  if (security?.honeypot === "YES" || security?.sellable === "NO") {
    decision = "REJECT";
  } else if (token.paidPromotion && (token.liquidityUsd ?? 0) < 25000) {
    decision = "REJECT";
  } else if (council.verdict === "REJECT") {
    decision = "REJECT";
  } else if (coverage < 0.35) {
    decision = "INSUFFICIENT_EVIDENCE";
  } else if (council.verdict === "WATCH") {
    decision = "WATCH";
  } else if (council.verdict === "DISAGREEMENT") {
    decision = "ABSTAIN";
  } else {
    decision = "ABSTAIN";
  }

  // Anti-hype: never promote high change as best.
  const liqScore = token.liquidityUsd != null ? Math.min(Math.log10(Math.max(token.liquidityUsd, 1)) / 6, 1) : null;
  const volScore = token.volume24h != null ? Math.min(Math.log10(Math.max(token.volume24h, 1)) / 7, 1) : null;
  const secScore = security?.honeypot === "YES" ? 0 : security?.status === "SUCCESS" ? 0.6 : null;
  const promoPenalty = token.paidPromotion ? 0.35 : 0;
  const momPenalty = (token.priceChange24h ?? 0) > 120 ? 0.25 : 0;
  const parts = [liqScore, volScore, secScore, coverage].filter((x): x is number => x != null);
  const rankScore =
    parts.length >= 2
      ? Math.max(0, parts.reduce((a, b) => a + b, 0) / parts.length - promoPenalty - momPenalty)
      : null;

  const confidence: Confidence =
    coverage >= 0.7 && decision === "REJECT" ? "HIGH" : coverage >= 0.55 ? "MED" : coverage >= 0.35 ? "LOW" : "UNKNOWN";

  const invalidationFa =
    decision === "REJECT"
      ? "این کاندید هم‌اکنون رد است مگر شواهد امنیتی و نقدینگی جدید خلاف آن را ثابت کند."
      : "ابطال پایش: اگر نقدینگی بیش از ۴۰٪ سقوط کند، هانی‌پات YES شود، یا خبر هک بیاید.";

  return {
    token,
    decision,
    rankScore,
    confidence,
    securityStatus: security?.honeypot === "YES" ? "HONEYPOT" : security?.status === "SUCCESS" ? "OBSERVED" : "UNKNOWN",
    evidenceCoverage: coverage,
    reasonsFa: reasonsFa.length ? reasonsFa : ["دلیل مثبت کافی ثبت نشد."],
    risksFa: risksFa.length ? risksFa : ["ریسک نامشخص — یعنی evidencen ناقص، نه بی‌ریسک."],
    unknownsFa,
    invalidationFa,
    missingFa,
    councilVerdict: council.verdict,
    disagreement: council.disagreement,
    votes: council.votes,
    security,
  };
}

export function rankOpportunities(list: ScoredOpportunity[]): ScoredOpportunity[] {
  const order: Record<string, number> = {
    WATCH: 0,
    ABSTAIN: 1,
    INSUFFICIENT_EVIDENCE: 2,
    UNKNOWN: 3,
    REJECT: 4,
    PAPER_CANDIDATE: 0,
  };
  return [...list].sort((a, b) => {
    // Rejected never rise above watch even with higher numeric score (anti-hype).
    const d = (order[a.decision] ?? 9) - (order[b.decision] ?? 9);
    if (d !== 0) return d;
    const cov = b.evidenceCoverage - a.evidenceCoverage;
    if (Math.abs(cov) > 0.02) return cov;
    const rs = (b.rankScore ?? -1) - (a.rankScore ?? -1);
    return rs;
  });
}
