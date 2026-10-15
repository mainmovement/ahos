/**
 * MOCK — "Kian" assistant responder.
 *
 * Deterministic, rule-based intent matching over the mock datasets. It never
 * claims live data, never recommends a real trade, and answers UNKNOWN when it
 * has no evidence. Replace with the real `/api/chat` (ConversationResponse in
 * the AHOS repo `types.ts`).
 */
import type { ChatMessage, Localized } from "@/lib/api/types";
import { mockAgents } from "./agents";
import { mockInstruments } from "./markets";
import { mockNews } from "./news";
import { mockPaperAccount } from "./paper";
import { mockSecurity } from "./security";
import { mockSystem } from "./system";
import { mockOpportunities } from "./tokens";
import { mockEarth } from "./org";

type Locale = "fa" | "en";

const FINAL_LINE: Localized = { fa: "تصمیم نهایی با کاربر است.", en: "The final decision is yours." };
const DEMO_LINE: Localized = {
  fa: "همه اعداد این پاسخ از داده نمایشی (DEMO) هستند، نه بازار زنده.",
  en: "All figures in this answer come from DEMO data, not a live market.",
};

const ASSETS: { id: string; keys: string[] }[] = [
  { id: "btc", keys: ["بیت", "btc", "bitcoin"] },
  { id: "eth", keys: ["اتریوم", "اتر", "eth", "ethereum"] },
  { id: "sol", keys: ["سولانا", "sol", "solana"] },
  { id: "xau", keys: ["طلا", "gold", "xau"] },
  { id: "brent", keys: ["نفت", "برنت", "oil", "brent"] },
  { id: "usdirt", keys: ["دلار", "usd", "dollar"] },
  { id: "spx", keys: ["s&p", "اس‌اند‌پی", "spx", "سهام آمریکا"] },
];

function has(text: string, keys: string[]): boolean {
  return keys.some((k) => text.includes(k));
}

function fmt(n: number, d = 2): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: Math.min(d, 2) > 0 && Math.abs(n) < 10 ? Math.min(d, 2) : 0 });
}

export function mockKianReply(input: string, locale: Locale, now = Date.now()): ChatMessage {
  const text = input.trim().toLowerCase();
  const fa = locale === "fa";
  const l = (v: Localized) => v[locale];
  const id = `kian-${now.toString(36)}`;
  const at = new Date(now).toISOString();

  // 1. Trade-execution requests — refuse, paper only.
  if (has(text, ["بخرم", "بفروشم", "خرید کن", "بخر", "بفروش", "buy", "sell", "long ", "short "])) {
    return {
      id,
      role: "assistant",
      at,
      intent: "trade_request",
      text: fa
        ? "من توصیه خرید یا فروش نمی‌دهم و هیچ معامله واقعی انجام نمی‌شود — AHOS فقط کاغذی (PAPER_ONLY) است. می‌توانم شواهد، ریسک‌ها و ناشناخته‌های یک دارایی را کنار هم بگذارم تا خودتان تصمیم بگیرید."
        : "I don't give buy/sell advice and no real trade can be executed — AHOS is PAPER_ONLY. I can lay out the evidence, risks and unknowns for an asset so you can decide.",
      evidence: [{ label: "mode=PAPER_ONLY", source: "governance/C2", status: "DEMO" }],
      uncertainty: [l(FINAL_LINE)],
      followups: fa ? ["شواهد سولانا چیست؟", "ریسک حساب کاغذی", "فرصت‌های WATCH"] : ["Evidence on Solana?", "Paper account risk", "WATCH opportunities"],
    };
  }

  // 2. Price questions.
  const asset = ASSETS.find((a) => has(text, a.keys));
  if (asset && (has(text, ["قیمت", "price", "چند", "how much", "نرخ"]) || text.length < 24)) {
    const inst = mockInstruments(now).find((i) => i.id === asset.id);
    if (inst && inst.price !== null) {
      const name = l(inst.name);
      const chg = inst.change24h ?? 0;
      const dir = chg >= 0 ? (fa ? "افزایش" : "up") : fa ? "کاهش" : "down";
      return {
        id,
        role: "assistant",
        at,
        intent: "price",
        text: fa
          ? `${name}: ${fmt(inst.price, inst.decimals)} ${inst.quote} — ${dir} ${fmt(Math.abs(chg))}٪ در ۲۴ ساعت. وضعیت داده: ${inst.status}. ${l(DEMO_LINE)}`
          : `${name}: ${fmt(inst.price, inst.decimals)} ${inst.quote} — ${dir} ${fmt(Math.abs(chg))}% over 24h. Data status: ${inst.status}. ${l(DEMO_LINE)}`,
        evidence: [{ label: `${inst.symbol} ${fmt(inst.price, inst.decimals)}`, source: inst.source, status: inst.status }],
        uncertainty: inst.status === "STALE" ? [fa ? "این مقدار کهنه است؛ به آخرین زمان دریافت توجه کنید." : "This value is stale; check the retrieval time."] : [],
        followups: fa ? ["روند ۷ روزه؟", "اخبار مرتبط", "وضعیت منابع داده"] : ["7-day trend?", "Related news", "Data source health"],
      };
    }
    return {
      id,
      role: "assistant",
      at,
      intent: "price",
      text: fa ? "برای این دارایی مقدار معتبری ندارم — UNKNOWN. منبع آن در دسترس نیست." : "I have no valid value for this asset — UNKNOWN. Its source is unavailable.",
      evidence: [{ label: asset.id.toUpperCase(), source: inst?.source ?? "unknown", status: inst?.status ?? "UNKNOWN" }],
      followups: [],
    };
  }

  // 3. Opportunities.
  if (has(text, ["فرصت", "opportunit", "watch", "پایش", "نامزد"])) {
    const rows = mockOpportunities(now).rows.filter((r) => r.outcome === "WATCH" || r.outcome === "PAPER_CANDIDATE");
    const list = rows
      .slice(0, 4)
      .map((r) => `• ${r.symbol} (${r.chain}) — ${r.outcome}, ${fa ? "امتیاز" : "score"} ${r.score ?? "—"}: ${l(r.primaryReason)}`)
      .join("\n");
    return {
      id,
      role: "assistant",
      at,
      intent: "opportunities",
      text: fa
        ? `این‌ها تصمیم‌های مرجع کانونی پایتون هستند (من تصمیم نمی‌سازم):\n${list}\n${l(DEMO_LINE)}`
        : `These are decisions from the Python canonical authority (I don't create decisions):\n${list}\n${l(DEMO_LINE)}`,
      evidence: rows.slice(0, 4).map((r) => ({ label: `${r.symbol}: ${r.outcome}`, source: "canonical-read-model (mock)", status: r.status })),
      uncertainty: [l(FINAL_LINE)],
      followups: fa ? ["چرا AEROX نامزد کاغذی است؟", "ردشده‌های امروز", "ریسک حساب کاغذی"] : ["Why is AEROX a paper candidate?", "Today's rejections", "Paper account risk"],
    };
  }

  // 4. Paper account / risk.
  if (has(text, ["ریسک", "risk", "کاغذی", "paper", "سبد", "portfolio", "پرتفو", "سود", "pnl"])) {
    const p = mockPaperAccount(now);
    const warn = p.limits.filter((x) => x.state !== "ok").map((x) => l(x.label));
    return {
      id,
      role: "assistant",
      at,
      intent: "paper_risk",
      text: fa
        ? `حساب کاغذی: ارزش ${fmt(p.equity)} دلار، سود/زیان امروز +${fmt(p.pnlDayPct)}٪، ${p.positions.length} موقعیت باز. محدودیت‌های نزدیک به سقف: ${warn.join("، ") || "هیچ"}. ${l(DEMO_LINE)}`
        : `Paper account: equity $${fmt(p.equity)}, today +${fmt(p.pnlDayPct)}%, ${p.positions.length} open positions. Limits near cap: ${warn.join(", ") || "none"}. ${l(DEMO_LINE)}`,
      evidence: [{ label: "paper_account", source: "mock/paper", status: "DEMO" }],
      uncertainty: [fa ? "یک موقعیت (BRENT) قیمت لحظه‌ای ندارد و STALE است." : "One position (BRENT) has no mark price and is STALE."],
      followups: fa ? ["موقعیت‌های باز", "حد ضرر SOL", "عملکرد ۹۰ روزه"] : ["Open positions", "SOL stop level", "90-day performance"],
    };
  }

  // 5. Security.
  if (has(text, ["امنیت", "هانی", "کلاهبردار", "security", "scam", "honeypot", "rug"])) {
    const s = mockSecurity(now);
    return {
      id,
      role: "assistant",
      at,
      intent: "security",
      text: fa
        ? `دروازه امنیت: ${s.gateCounts.PASS} عبور، ${s.gateCounts.REJECT} رد، ${s.gateCounts.INCOMPLETE} ناقص، ${s.gateCounts.STALE} کهنه. آخرین رد: PEPE2 (هانی‌پات، مالیات فروش ۹۹٪). یادآوری: ناقص یا UNKNOWN به معنی امن نیست.`
        : `Security gate: ${s.gateCounts.PASS} PASS, ${s.gateCounts.REJECT} REJECT, ${s.gateCounts.INCOMPLETE} INCOMPLETE, ${s.gateCounts.STALE} STALE. Latest reject: PEPE2 (honeypot, 99% sell tax). Reminder: INCOMPLETE or UNKNOWN does not mean safe.`,
      evidence: [
        { label: "gate counts", source: "mock/security", status: "DEMO" },
        { label: "GoPlus", source: "provider", status: "DEMO" },
      ],
      followups: fa ? ["دامنه‌های فیشینگ", "وضعیت GoPlus", "توکن‌های ناقص"] : ["Phishing domains", "GoPlus status", "Incomplete tokens"],
    };
  }

  // 6. News.
  if (has(text, ["خبر", "اخبار", "news", "headline"])) {
    const n = mockNews(now);
    const verified = n.items.filter((i) => i.verification === "VERIFIED").slice(0, 3);
    const conflicting = n.items.filter((i) => i.verification === "CONFLICTING").length;
    return {
      id,
      role: "assistant",
      at,
      intent: "news",
      text: fa
        ? `خبرهای تأییدشده:\n${verified.map((i) => `• ${l(i.title)} (${i.source})`).join("\n")}\n${conflicting} خبر متناقض در صف تأیید است و تا رفع تناقض به‌عنوان واقعیت گزارش نمی‌شود.`
        : `Verified headlines:\n${verified.map((i) => `• ${l(i.title)} (${i.source})`).join("\n")}\n${conflicting} conflicting stories are held in verification and are not reported as fact.`,
      evidence: verified.map((i) => ({ label: i.source, source: "mock/news", status: i.status })),
      followups: fa ? ["خبرهای متناقض", "منابع کم‌اعتبار", "خط لوله خبر"] : ["Conflicting stories", "Low-reliability sources", "News pipeline"],
    };
  }

  // 7. Agents.
  if (has(text, ["عامل", "agent", "ایجنت"])) {
    const a = mockAgents(now).agents;
    const count = (s: string) => a.filter((x) => x.runtime === s).length;
    return {
      id,
      role: "assistant",
      at,
      intent: "agents",
      text: fa
        ? `${a.length} عامل ثبت شده: ${count("running")} در حال اجرا، ${count("idle")} بیکار، ${count("blocked")} مسدود، ${count("failed")} ناموفق، ${count("registered")} فقط ثبت‌شده، ${count("planned")} برنامه‌ریزی‌شده. ۱۹ نقش نقشه سازمانی هنوز عملیاتی نیستند.`
        : `${a.length} agents on record: ${count("running")} running, ${count("idle")} idle, ${count("blocked")} blocked, ${count("failed")} failed, ${count("registered")} registered-only, ${count("planned")} planned. The 19 organizational roles are not operational yet.`,
      evidence: [{ label: "PLANNED_19_AGENT_MAP", source: "docs/agents", status: "DEMO" }],
      followups: fa ? ["چرا لبه تلگرام ناموفق است؟", "کار فعلی تحلیلگر پژوهش", "عامل‌های مسدود"] : ["Why did Telegram edge fail?", "Research analyst's current task", "Blocked agents"],
    };
  }

  // 8. System health.
  if (has(text, ["سیستم", "سلامت", "وضعیت", "system", "health", "status", "uptime"])) {
    const s = mockSystem(now);
    const bad = s.services.filter((x) => x.state !== "UP").map((x) => `${l(x.name)}: ${x.state}`);
    return {
      id,
      role: "assistant",
      at,
      intent: "system",
      text: fa
        ? `حالت: PAPER_ONLY. یکپارچگی Lane A: ${s.laneA.state}. سرویس‌های غیرسالم: ${bad.join("، ")}. طبقه‌بندی پروژه: ${s.classification} (OPERATOR_READY هنوز تأیید نشده).`
        : `Mode: PAPER_ONLY. Lane A integrity: ${s.laneA.state}. Unhealthy services: ${bad.join(", ")}. Project classification: ${s.classification} (OPERATOR_READY not verified).`,
      evidence: [{ label: "system overview", source: "mock/system", status: "DEMO" }],
      followups: fa ? ["سلامت منابع داده", "خطاهای باز", "زمان کارکرد"] : ["Provider health", "Open errors", "Uptime"],
    };
  }

  // 9. Iran.
  if (has(text, ["ایران", "تهران", "iran", "tehran", "بورس تهران"])) {
    const e = mockEarth(now).iran;
    const lines = e.indicators.map((i) => `• ${l(i.label)}: ${i.value === null ? "UNKNOWN" : fmt(i.value, i.decimals)} ${i.value === null ? "" : l(i.unit)} [${i.status}]`).join("\n");
    return {
      id,
      role: "assistant",
      at,
      intent: "iran",
      text: (fa ? "نمای ایران:\n" : "Iran view:\n") + lines,
      evidence: e.indicators.slice(0, 3).map((i) => ({ label: l(i.label), source: i.source, status: i.status })),
      uncertainty: [fa ? "صادرات نفت ایران منبع عمومی قابل اتکا ندارد — UNAVAILABLE." : "Iran oil exports have no reliable public source — UNAVAILABLE."],
      followups: fa ? ["شاخص کل بورس", "قیمت سکه", "نمایش ایران روی کره"] : ["TEDPIX", "Coin price", "Show Iran on the globe"],
    };
  }

  // 10. Greeting.
  if (has(text, ["سلام", "درود", "hello", "hi", "hey"]) || text.length === 0) {
    return {
      id,
      role: "assistant",
      at,
      intent: "greeting",
      text: fa
        ? "سلام مهرداد، من کیان هستم. می‌توانم درباره قیمت‌ها، فرصت‌های بررسی‌شده، ریسک حساب کاغذی، امنیت، اخبار و وضعیت سامانه پاسخ بدهم — همیشه همراه با منبع و وضعیت داده."
        : "Hi Mehrdad, I'm Kian. I can answer about prices, reviewed opportunities, paper-account risk, security, news and system status — always with source and data status.",
      followups: fa ? ["قیمت بیت‌کوین", "فرصت‌های WATCH", "وضعیت سیستم"] : ["Bitcoin price", "WATCH opportunities", "System status"],
    };
  }

  // 11. Honest fallback.
  return {
    id,
    role: "assistant",
    at,
    intent: "unknown",
    text: fa
      ? "برای این پرسش شواهدی در دسترس ندارم — UNKNOWN. حدس نمی‌زنم. می‌توانید درباره قیمت، فرصت‌ها، ریسک، امنیت، اخبار، عامل‌ها یا وضعیت سیستم بپرسید."
      : "I have no evidence available for that — UNKNOWN. I won't guess. Ask about prices, opportunities, risk, security, news, agents or system status.",
    uncertainty: [fa ? "نبود داده ≠ پاسخ منفی" : "Absence of data ≠ negative answer"],
    followups: fa ? ["قیمت طلا", "اخبار امروز", "عامل‌ها"] : ["Gold price", "Today's news", "Agents"],
  };
}

export function mockChatSeed(locale: Locale, now = Date.now()): ChatMessage[] {
  const greet = mockKianReply("سلام", locale, now - 60_000);
  return [{ ...greet, id: "seed-1" }];
}
