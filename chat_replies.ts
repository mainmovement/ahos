/**
 * Presentation-only reply builders for chat / Telegram (Phase 5).
 * Pure: no DB, no network, no decisions. Every value shown comes from the
 * snapshot passed in; missing values render as «نامشخص» / «داده کافی نیست».
 * Internal ids (GM-xx, canonical, raw enum codes) are kept out of user text.
 */
import type { CanonicalDecisionView } from "./canonical_read_model";
import { faNumber, faPct, faUsd } from "./persian";
import { bullet, faAge, gap, isMostlyPersian, line, note, title, type ReplyBlock } from "./reply_format";
import type { commandSnapshot } from "./snapshot";

export type Snap = Awaited<ReturnType<typeof commandSnapshot>>;
export type Opp = Snap["opportunities"][number];

/** "بازار چه خبر؟" is a market question; explicit news words make it a news request. */
export function isNewsRequest(text: string): boolean {
  return /(اخبار|news|تیتر)/i.test(text) || (/خبر/.test(text) && !/بازار/.test(text));
}

export function isStopLossQuestion(text: string): boolean {
  return /(stop[\s_-]*loss|استاپ[\s\u200c]*لاس|حد[\s\u200c]*(?:ضرر|زیان)|توقف[\s\u200c]*ضرر)/i.test(text);
}

export const ENGINE_OFF_NOTE = "موتور خاموش است و داده‌ها به‌روز نمی‌شوند. روشن کردن فقط از داشبورد محلی.";

export function engineNoticeRelevant(intent: string, text: string): boolean {
  if (intent === "help" || intent === "greeting" || intent === "health" || intent === "opportunities" || intent === "price") return true;
  return /(موتور|engine)/i.test(text);
}

const DECISION_FA: Record<string, string> = {
  BUY: "خرید (کاغذی)",
  WATCH: "پایش",
  MONITOR_ONLY: "فقط پایش",
  NO_TRADE: "بدون معامله",
  REJECT: "رد",
};
const CONFIDENCE_FA: Record<string, string> = { HIGH: "بالا", MED: "متوسط", MEDIUM: "متوسط", LOW: "پایین" };
const STATE_FA: Record<string, string> = {
  PASS: "تأیید شده",
  SAFE: "تأیید شده",
  FAIL: "رد شده",
  WARN: "هشدار",
  UNKNOWN: "نامشخص",
  VERIFIED: "تأیید شده",
};
export const REGIME_FA: Record<string, string> = {
  EXTREME_GREED: "طمع شدید",
  EXTREME_FEAR: "ترس شدید",
  RISK_ON: "ریسک‌پذیر (رو به رشد)",
  RISK_OFF: "ریسک‌گریز (رو به افت)",
  RANGE: "خنثی (نوسان در محدوده)",
  UNKNOWN: "نامشخص",
};
export const FEAR_GREED_FA: Record<string, string> = {
  "extreme fear": "ترس شدید",
  fear: "ترس",
  neutral: "خنثی",
  greed: "طمع",
  "extreme greed": "طمع شدید",
};

export function decisionFa(v: string | null | undefined): string {
  const k = String(v ?? "").toUpperCase();
  return DECISION_FA[k] ?? (k ? k : "نامشخص");
}
export function confidenceFa(v: string | null | undefined): string {
  const k = String(v ?? "").toUpperCase();
  return CONFIDENCE_FA[k] ?? (k && k !== "UNKNOWN" ? k : "نامشخص");
}
export function stateFa(v: string | null | undefined): string {
  const k = String(v ?? "").toUpperCase();
  return STATE_FA[k] ?? (k ? k : "نامشخص");
}
export function priceFa(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "نامشخص";
  return `${faNumber(n, n < 1 ? 6 : n < 100 ? 2 : 0)} دلار`;
}

export function newsTitle(n: { titleFa?: string | null; titleOriginal?: string | null }): { text: string; persian: boolean } {
  const fa = String(n.titleFa ?? "").trim();
  if (fa && isMostlyPersian(fa)) return { text: fa, persian: true };
  const orig = String(n.titleOriginal ?? "").trim();
  return { text: orig || fa || "بدون عنوان", persian: false };
}

/** `n` = tokens currently under system review, or null when the read model is unavailable. */
export function greetingBlocks(n: number | null): ReplyBlock[] {
  return [
    title("سلام! 👋 من AHOS هستم"),
    line("دستیار تحلیل بازار رمزارز — فقط معامله کاغذی، بدون خرید واقعی."),
    n === null ? gap() : line(`الان ${faNumber(n, 0)} توکن در فهرست پایش سیستم است.`),
    line("برای دیدن کارهایی که می‌توانم انجام بدهم «راهنما» را بفرست."),
  ];
}

export function helpBlocks(): ReplyBlock[] {
  return [
    title("🤖 راهنمای AHOS"),
    line("می‌توانی این‌ها را بپرسی:"),
    bullet("«بازار چه خبر؟» — قیمت و حال بیت‌کوین، اتریوم و سولانا"),
    bullet("«قیمت بیت‌کوین چنده؟» — آخرین قیمت ثبت‌شده با زمان به‌روزرسانی"),
    bullet("«فرصت‌ها» — توکن‌های در حال پایش"),
    bullet("«اخبار» یا «اخبار سولانا» — تیترهای اخیر"),
    bullet("«چرا PEPE؟» — دلیل حکم یک توکن"),
    bullet("«PEPE را زیر نظر بگیر» — افزودن به واچ‌لیست"),
    bullet("«وضعیت سیستم» · «شورا» · «درس‌ها»"),
    gap(),
    note("روشن/خاموش کردن موتور و ثبت خرید کاغذی فقط از داشبورد محلی انجام می‌شود."),
  ];
}

export function marketBlocks(snap: Snap, now: Date = new Date()): ReplyBlock[] {
  const m = snap.market;
  if (!m) return [title("📊 وضعیت بازار"), line("هنوز داده‌ای از بازار ثبت نشده (داده کافی نیست).")];
  const asset = (name: string, price: number | null, chg: number | null) =>
    bullet(`${name}: ${priceFa(price)}${price != null && chg != null && Number.isFinite(chg) ? ` (${faPct(chg)} در ۲۴ ساعت)` : ""}`);
  const out: ReplyBlock[] = [
    title("📊 وضعیت بازار"),
    asset("بیت‌کوین", m.btcPrice, m.btcChange24h),
    asset("اتریوم", m.ethPrice, m.ethChange24h),
    asset("سولانا", m.solPrice, m.solChange24h),
    gap(),
    line(`حال بازار: ${REGIME_FA[String(m.regime ?? "UNKNOWN")] ?? "نامشخص"}`),
  ];
  if (m.fearGreed != null && Number.isFinite(m.fearGreed)) {
    const label = FEAR_GREED_FA[String(m.fearGreedLabel ?? "").toLowerCase()];
    out.push(line(`شاخص ترس و طمع: ${faNumber(m.fearGreed, 0)} از ۱۰۰${label ? ` (${label})` : ""}`));
  }
  const macro: string[] = [];
  if (m.totalMcap != null && Number.isFinite(m.totalMcap)) macro.push(`ارزش کل بازار ${faUsd(m.totalMcap)}`);
  if (m.btcDominance != null && Number.isFinite(m.btcDominance)) macro.push(`سهم بیت‌کوین ${faNumber(m.btcDominance, 1)}٪`);
  if (macro.length) out.push(line(macro.join(" · ")));
  const missing = [m.btcPrice, m.ethPrice, m.solPrice].some((p) => p == null || !Number.isFinite(p));
  const age = faAge(m.createdAt as unknown as string | Date | null, now);
  const stale = m.createdAt ? now.getTime() - new Date(m.createdAt as unknown as string).getTime() > 60 * 60 * 1000 : true;
  out.push(gap());
  if (missing) out.push(note("برخی قیمت‌ها در دسترس نبود (داده کافی نیست)."));
  out.push(note(age ? `آخرین به‌روزرسانی: ${age}${stale ? " — ممکن است قدیمی باشد" : ""}` : "زمان به‌روزرسانی نامشخص است."));
  const headlines = snap.news.map((n) => ({ n, t: newsTitle(n) })).filter((x) => x.t.persian).slice(0, 3);
  if (headlines.length) {
    out.push(gap(), title("📰 تیترهای اخیر"), ...headlines.map((x) => bullet(x.t.text)));
  }
  return out;
}

export function oppBlocks(snap: Snap): ReplyBlock[] {
  const status = snap.canonicalReadModel?.status;
  if (status && status !== "AVAILABLE") {
    return [title("🎯 فرصت‌ها"), line("داده تصمیم‌های سیستم الان در دسترس نیست؛ فرصتی نمایش داده نمی‌شود.")];
  }
  const canon = snap.canonicalDecisions ?? [];
  const canonBuys = canon.filter((d) => d.outcome === "BUY");
  const canonWatch = canon.filter((d) => d.outcome === "WATCH" || d.outcome === "MONITOR_ONLY" || d.outcome === "NO_TRADE");
  const buys = snap.opportunities.filter((o) => o.decision === "BUY");
  const watch = snap.opportunities.filter((o) => o.decision === "WATCH" || o.decision === "MONITOR_ONLY");
  const rejected =
    snap.opportunities.filter((o) => o.decision === "REJECT").length ||
    canon.filter((d) => d.outcome === "REJECT").length;
  const rejectedLine = rejected ? note(`${faNumber(rejected, 0)} توکن به دلیل ریسک رد شدند.`) : gap();
  if (!snap.opportunities.length && !canon.length) {
    return [title("🎯 فرصت‌ها"), line("فعلاً فرصتی ثبت نشده.")];
  }
  if (canonBuys.length) {
    return [
      title("🎯 فرصت‌های خرید (فقط کاغذی)"),
      ...canonBuys.slice(0, 5).map((d) =>
        bullet(`${d.symbol || "نامشخص"} (${d.chain || "نامشخص"}) — اطمینان: ${confidenceFa(d.confidence)} · امنیت: ${stateFa(d.securityState)}`),
      ),
      rejectedLine,
      note("فقط کاغذی — توصیه خرید واقعی نیست."),
    ];
  }
  if (!buys.length && !watch.length && !canonWatch.length) {
    return [title("🎯 فرصت‌ها"), line("فعلاً فرصت خریدی وجود ندارد."), rejectedLine];
  }
  if (canonWatch.length && !buys.length) {
    return [
      title("👀 در حال پایش (خرید نیست)"),
      ...canonWatch.slice(0, 5).map((d) =>
        bullet(`${d.symbol || "نامشخص"} (${d.chain || "نامشخص"}) — ${decisionFa(d.outcome)} · امنیت: ${stateFa(d.securityState)}`),
      ),
      rejectedLine,
    ];
  }
  const list = (buys.length ? buys : watch).slice(0, 5);
  return [
    title(buys.length ? "🎯 فرصت‌های خرید (فقط کاغذی)" : "👀 در حال پایش (خرید نیست)"),
    ...list.map((o) =>
      bullet(`${o.symbol} (${o.chain}) — ${decisionFa(o.decision)} · اطمینان: ${confidenceFa(o.confidence)} · امنیت: ${stateFa(o.securityState)}`),
    ),
    rejectedLine,
  ];
}

export function newsBlocks(snap: Snap, text: string): ReplyBlock[] {
  let items = snap.news;
  let heading = "📰 اخبار اخیر";
  if (/solana|سولانا/i.test(text)) {
    heading = "📰 اخبار سولانا";
    items = items.filter(
      (n) => n.relatedChains?.includes("solana") || /سولانا|solana/i.test(`${n.titleFa} ${n.titleOriginal}`),
    );
  }
  if (/bitcoin|بیت/i.test(text)) {
    heading = "📰 اخبار بیت‌کوین";
    items = items.filter(
      (n) => n.relatedTokens?.includes("BTC") || /بیت‌کوین|bitcoin/i.test(`${n.titleFa} ${n.titleOriginal}`),
    );
  }
  const top = items.slice(0, 5);
  if (!top.length) return [title(heading), line("فعلاً خبری مطابق درخواستت ثبت نشده.")];
  const rows = top.map((n) => ({ n, t: newsTitle(n) }));
  const out: ReplyBlock[] = [
    title(heading),
    ...rows.map(({ n, t }) => bullet(t.text, n.sourceUrl ? { label: n.source, url: n.sourceUrl } : { label: n.source, url: "" })),
  ];
  if (rows.some((r) => !r.t.persian)) out.push(gap(), note("تیترهایی که ترجمه کامل نداشتند به زبان اصلی آمده‌اند."));
  return out;
}

export function stopLossBlocks(hit: Opp | null): ReplyBlock[] {
  if (hit) {
    return [
      title(`🛑 حد ضرر — ${hit.symbol}`),
      line("عدد مشخصی برای حد ضرر این توکن در داده‌های من ثبت نشده و آن را حدس نمی‌زنم."),
      hit.invalidationFa ? bullet(`شرط ابطال تحلیل: ${hit.invalidationFa}`) : bullet("شرط ابطال هم ثبت نشده (داده کافی نیست)."),
    ];
  }
  return [
    title("🛑 حد ضرر"),
    line("برای کدام توکن؟ نماد را بنویس، مثلاً «حد ضرر PEPE»."),
    line("سیستم برای هر فرصت یک «شرط ابطال» ثبت می‌کند؛ عدد حد ضرر را از خودم نمی‌سازم."),
  ];
}

export function healthBlocks(snap: Snap): ReplyBlock[] {
  return [
    title("🩺 وضعیت سیستم"),
    ...snap.health.dimensions.map((d) => bullet(`${d.nameFa}: ${d.status} — ${d.evidenceFa}`)),
    gap(),
    line(`تعداد چرخه‌ها: ${faNumber(snap.state.cycleCount, 0)} · آخرین وضعیت: ${snap.state.lastCycleStatus ?? "نامشخص"}`),
  ];
}

export function councilBlocks(snap: Snap, hit: Opp | null): ReplyBlock[] {
  if (!snap.council.length) return [line("هنوز گزارشی از شورا ثبت نشده.")];
  const c =
    (hit && snap.council.find((x) => x.tokenKey === hit.tokenKey)) || snap.council[0];
  return [
    title(`🧑‍⚖️ نظر شورا — ${hit?.symbol || c.tokenKey}`),
    bullet(`حکم: ${decisionFa(c.verdict)}`),
    bullet(`آرا: پایش ${faNumber(c.watchCount, 0)} · رد ${faNumber(c.rejectCount, 0)} · ممتنع ${faNumber(c.abstainCount, 0)}`),
    c.summaryFa ? line(c.summaryFa) : gap(),
  ];
}

export function learningBlocks(snap: Snap): ReplyBlock[] {
  if (!snap.lessons.length) {
    return [line("هنوز درسی ثبت نشده؛ پیش‌بینی‌ها باید به افق زمانی‌شان برسند تا نتیجه واقعی ساخته شود.")];
  }
  return [title("📚 درس‌های ثبت‌شده"), ...snap.lessons.slice(0, 5).map((l) => bullet(`${l.titleFa}: ${l.bodyFa}`))];
}

export function watchBlocks(snap: Snap): ReplyBlock[] {
  if (!snap.watchlist.length) return [line("واچ‌لیست خالی است. مثلاً بنویس «PEPE را زیر نظر بگیر».")];
  return [title("👀 واچ‌لیست"), ...snap.watchlist.map((w) => bullet(`${w.symbol} (${w.chain}) — ${w.thesisFa || "بدون توضیح"}`))];
}

export function paperBlocks(snap: Snap): ReplyBlock[] {
  const open = snap.paper.filter((p) => p.status === "OPEN");
  if (!open.length) return [line("موقعیت کاغذی بازی وجود ندارد.")];
  return [
    title("📄 موقعیت‌های کاغذی باز"),
    ...open.map((p) => {
      const pnl = p.entryPrice && p.lastPrice ? faPct(((p.lastPrice - p.entryPrice) / p.entryPrice) * 100) : "نامشخص";
      return bullet(`${p.symbol} — ورود ${priceFa(p.entryPrice)} · آخرین ${priceFa(p.lastPrice)} · بازده ${pnl}`);
    }),
  ];
}

export function whyCanonicalBlocks(d: CanonicalDecisionView): ReplyBlock[] {
  return [
    title(`🔎 ${d.symbol || "نامشخص"} (${d.chain || "نامشخص"})`),
    bullet(`حکم سیستم: ${decisionFa(d.outcome)} · اطمینان: ${confidenceFa(d.confidence)}`),
    bullet(`هویت: ${stateFa(d.identityState)} · امنیت: ${stateFa(d.securityState)}`),
    d.primaryReason ? bullet(`دلیل اصلی: ${d.primaryReason}`) : bullet("دلیل تکمیلی ثبت نشده."),
    d.monitoringOnly ? note("فقط پایش — فرصت یا ثبت کاغذی نیست.") : note("فقط کاغذی — توصیه خرید واقعی نیست."),
  ];
}

export function whyBlocks(o: Opp): ReplyBlock[] {
  const reasons = (o.reasonsFa || []).filter(Boolean).slice(0, 3);
  const risks = (o.risksFa || []).filter(Boolean).slice(0, 3);
  const gaps = [...(o.unknownsFa || []), ...(o.missingFa || [])].filter(Boolean).slice(0, 4);
  const out: ReplyBlock[] = [
    title(`🔎 ${o.symbol} (${o.chain})`),
    bullet(`حکم: ${decisionFa(o.decision)} · اطمینان: ${confidenceFa(o.confidence)}`),
    bullet(`امنیت: ${stateFa(o.securityStatus)} · شورا: ${decisionFa(o.councilVerdict)}${o.disagreement ? " (با اختلاف نظر)" : ""}`),
  ];
  if (reasons.length) out.push(gap(), title("دلایل"), ...reasons.map((r) => bullet(r)));
  if (risks.length) out.push(gap(), title("ریسک‌ها"), ...risks.map((r) => bullet(r)));
  if (gaps.length) out.push(gap(), note(`داده ناقص: ${gaps.join("، ")}`));
  if (o.invalidationFa) out.push(line(`شرط ابطال: ${o.invalidationFa}`));
  out.push(note("فقط کاغذی — توصیه خرید واقعی نیست."));
  return out;
}

const ASSET_FA: Record<string, string> = { BTC: "بیت‌کوین", ETH: "اتریوم", SOL: "سولانا" };

/**
 * Phase 7: price question. Only the last recorded market snapshot is used
 * (BTC/ETH/SOL); freshness is always shown; a missing value is said honestly.
 * `asset` null + `ticker` = a symbol whose price the system does not record.
 */
export function priceBlocks(snap: Snap, asset: "BTC" | "ETH" | "SOL" | null, ticker: string | null, now: Date = new Date()): ReplyBlock[] {
  if (!asset) {
    const sym = ticker || "این نماد";
    return [
      title(`💰 قیمت ${sym}`),
      line(`قیمت ${sym} در داده‌های سیستم ثبت نمی‌شود و آن را حدس نمی‌زنم.`),
      line("سیستم فقط قیمت بیت‌کوین، اتریوم و سولانا را ثبت می‌کند."),
      ticker ? bullet(`«چرا ${ticker}؟» — اگر در فهرست پایش باشد، تحلیل سیستم را نشان می‌دهد.`) : gap(),
    ];
  }
  const name = ASSET_FA[asset];
  const m = snap.market;
  if (!m) return [title(`💰 قیمت ${name}`), line("هنوز داده‌ای از بازار ثبت نشده (داده کافی نیست). عددی حدس نمی‌زنم.")];
  const price = asset === "BTC" ? m.btcPrice : asset === "ETH" ? m.ethPrice : m.solPrice;
  const chg = asset === "BTC" ? m.btcChange24h : asset === "ETH" ? m.ethChange24h : m.solChange24h;
  const createdAt = m.createdAt as unknown as string | Date | null;
  const age = faAge(createdAt, now);
  const ageMs = createdAt ? now.getTime() - new Date(createdAt).getTime() : NaN;
  const stale = !Number.isFinite(ageMs) || ageMs > 60 * 60 * 1000;
  if (price == null || !Number.isFinite(price)) {
    return [
      title(`💰 قیمت ${name}`),
      line(`قیمت ${name} در آخرین داده ثبت‌شده موجود نیست (داده کافی نیست). عددی حدس نمی‌زنم.`),
      note(age ? `آخرین به‌روزرسانی بازار: ${age}` : "زمان به‌روزرسانی نامشخص است."),
    ];
  }
  const out: ReplyBlock[] = [
    title(`💰 قیمت ${name}`),
    line(`${name}: ${priceFa(price)}${chg != null && Number.isFinite(chg) ? ` (${faPct(chg)} در ۲۴ ساعت)` : ""}`),
    gap(),
    note(
      age
        ? `آخرین به‌روزرسانی: ${age}${stale ? " — این قیمت لحظه‌ای نیست و ممکن است قدیمی باشد" : ""}`
        : "زمان به‌روزرسانی نامشخص است؛ این قیمت ممکن است قدیمی باشد.",
    ),
  ];
  return out;
}

/**
 * Phase 7: trading-signal / futures-advice requests (leverage, long/short,
 * take-profit + stop-loss, "pick me a coin"). PAPER_ONLY: no signal, no coin pick.
 */
export function tradeSignalBlocks(): ReplyBlock[] {
  return [
    title("🙏 سیگنال معاملاتی نمی‌دهم"),
    line("AHOS فقط برای تحلیل و معامله کاغذی است؛ پیشنهاد اهرم یا درصد فیوچرز، لانگ/شورت، حد سود و حد ضرر نمی‌دهم و ارزی را برای سود معرفی نمی‌کنم."),
    gap(),
    line("کاری که می‌توانم بکنم:"),
    bullet("«فرصت‌ها» — توکن‌هایی که سیستم بررسی کرده، همراه با نکات ریسک"),
    bullet("«چرا <نماد>؟» — دلیل حکم سیستم برای یک توکن، مثلاً «چرا PEPE؟»"),
    bullet("«قیمت بیت‌کوین چنده؟» — آخرین قیمت ثبت‌شده"),
    gap(),
    note("معامله با اهرم ریسک از دست رفتن کل سرمایه را دارد."),
  ];
}

export function thanksBlocks(): ReplyBlock[] {
  return [line("خواهش می‌کنم 🙏 اگر سؤال دیگری داری بپرس؛ مثلاً «بازار چه خبر؟» یا «فرصت‌ها».")];
}

/** Fallback for unrecognised questions. `buyCount` = system BUY decisions (paper only). */
export function generalBlocks(buyCount: number): ReplyBlock[] {
  return [
    line("این سؤال را دقیق متوجه نشدم. یکی از این‌ها را امتحان کن:"),
    bullet("«بازار چه خبر؟»"),
    bullet("«فرصت‌ها»"),
    bullet("«اخبار»"),
    bullet("«چرا PEPE؟»"),
    buyCount ? note(`${faNumber(buyCount, 0)} فرصت خرید کاغذی ثبت شده — «فرصت‌ها» را بفرست.`) : gap(),
  ];
}
