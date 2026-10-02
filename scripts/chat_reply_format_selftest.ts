/**
 * Phase 5: chat / Telegram reply presentation (snapshot-style, escaping, length,
 * no internal jargon, no fabricated numbers).
 * Run: npm run test:chat-reply-format
 * Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  engineNoticeRelevant,
  generalBlocks,
  greetingBlocks,
  helpBlocks,
  isNewsRequest,
  isStopLossQuestion,
  marketBlocks,
  newsBlocks,
  oppBlocks,
  stopLossBlocks,
  whyBlocks,
  whyCanonicalBlocks,
  type Opp,
  type Snap,
} from "../chat_replies.ts";
import { detectControlCommand, gateChatControl } from "../chat_control_gate.ts";
import {
  TELEGRAM_MAX_CHARS,
  blocksFromText,
  bullet,
  escapeHtml,
  isMostlyPersian,
  renderPlain,
  renderTelegramHtml,
  safeUrl,
  title,
} from "../reply_format.ts";
import {
  RESPONSE_STYLE_FA,
  composeDeterministic,
  finalizeReply,
  validatePhrased,
  type ReplyPhraser,
} from "../response_composer.ts";

const FOOTER = "تصمیم نهایی با کاربر است.";
const NOW = new Date("2026-10-02T12:30:00Z");
const fa = (n: number, d = 0) => new Intl.NumberFormat("fa-IR", { maximumFractionDigits: d }).format(n);

const MESSY_NEWS = {
  source: "The Block",
  sourceUrl: "https://www.theblock.co/post/1",
  titleOriginal: "Bitcoin ETF inflows surge as traders eye Fed",
  titleFa: "بیت‌کوین صندوق ETF inflows جهش as معامله‌گران eye Fed",
  summaryFa: "منبع: The Block. Spot bitcoin ETFs saw... طبقه‌بندی شواهدی: عمومی رمزارز. اهمیت: UNKNOWN. حس خبر: UNKNOWN.",
  importance: "UNKNOWN",
  relatedTokens: ["BTC"],
  relatedChains: [],
};
const CLEAN_NEWS = {
  source: "CoinDesk",
  sourceUrl: "https://www.coindesk.com/x",
  titleOriginal: "Solana mainnet upgrade",
  titleFa: "ارتقاء مین‌نت سولانا انجام شد",
  summaryFa: "طبقه‌بندی شواهدی: عمومی رمزارز. اهمیت: UNKNOWN.",
  importance: "UNKNOWN",
  relatedTokens: ["SOL"],
  relatedChains: ["solana"],
};
const EVIL_NEWS = {
  source: "<b>evil</b> & co",
  sourceUrl: "javascript:alert(1)",
  titleOriginal: "<script>alert('x')</script> & <i>",
  titleFa: "<script>alert('x')</script> & <i>",
  summaryFa: "",
  importance: "UNKNOWN",
  relatedTokens: [],
  relatedChains: [],
};

const OPP = {
  tokenKey: "solana:Abc",
  symbol: "PEPE",
  chain: "solana",
  decision: "WATCH",
  confidence: "LOW",
  securityStatus: "UNKNOWN",
  securityState: "UNKNOWN",
  identityState: "UNKNOWN",
  councilVerdict: "WATCH",
  disagreement: true,
  reasonsFa: ["حجم معاملات بالا رفته"],
  risksFa: ["نقدینگی کم"],
  unknownsFa: ["نقش کیف پول"],
  missingFa: [],
  invalidationFa: "اگر نقدینگی زیر ۱۰ هزار دلار برود",
} as unknown as Opp;

function snap(over: Partial<Record<string, unknown>> = {}): Snap {
  return {
    market: {
      regime: "RANGE",
      fearGreed: 52,
      fearGreedLabel: "Neutral",
      btcPrice: 65432.1,
      btcChange24h: -1.25,
      ethPrice: 2510.5,
      ethChange24h: 0.5,
      solPrice: 150.25,
      solChange24h: 2.75,
      totalMcap: 2.3e12,
      mcapChange24h: 0.1,
      btcDominance: 54.3,
      defiTvl: 9e10,
      payload: {},
      createdAt: "2026-10-02T12:10:00Z",
    },
    news: [MESSY_NEWS, CLEAN_NEWS],
    opportunities: [OPP],
    canonicalDecisions: [],
    canonicalReadModel: { status: "AVAILABLE" },
    council: [],
    lessons: [],
    watchlist: [],
    paper: [],
    health: { dimensions: [] },
    state: { running: false, cycleCount: 0, lastCycleStatus: null },
    ...over,
  } as unknown as Snap;
}

const JARGON = [/GM-\d/i, /canonical/i, /کانونیکال/, /\bUNKNOWN\b/, /INSUFFICIENT_EVIDENCE/, /SOURCE_UNAVAILABLE/, /wallet_role/];
function assertClean(text: string, label: string) {
  for (const re of JARGON) assert.ok(!re.test(text), `${label}: jargon ${re} in:\n${text}`);
  assert.ok(!/فهمیدم چی گفتی/.test(text), `${label}: filler`);
  assert.ok(!/طبقه‌بندی شواهدی/.test(text), `${label}: news classification dump`);
}
function both(blocks: ReturnType<typeof helpBlocks>) {
  return { plain: renderPlain(blocks, FOOTER), html: renderTelegramHtml(blocks, FOOTER) };
}
function balanced(html: string) {
  for (const t of ["b", "i", "a"]) {
    const open = (html.match(new RegExp(`<${t}[ >]`, "g")) || []).length;
    const close = (html.match(new RegExp(`</${t}>`, "g")) || []).length;
    assert.equal(open, close, `unbalanced <${t}> in ${html}`);
  }
}
function footerOnce(text: string) {
  assert.equal(text.split(FOOTER).length - 1, 1, "footer must appear exactly once");
}

describe("intent helpers", () => {
  it("'بازار چه خبر؟' is a market question, not news", () => assert.equal(isNewsRequest("بازار چه خبر؟"), false));
  for (const t of ["اخبار", "اخبار سولانا", "خبر جدید چیه؟", "news", "تیترهای امروز"]) {
    it(`news request: ${t}`, () => assert.equal(isNewsRequest(t), true));
  }
  for (const t of ["stop loss چند هست؟", "stop loss چنده؟", "stoploss PEPE", "حد ضرر PEPE", "توقف ضرر چقدره", "استاپ لاس"]) {
    it(`stop-loss question (never a control command): ${t}`, () => {
      assert.equal(isStopLossQuestion(t), true);
      assert.equal(detectControlCommand(t), null);
    });
  }
  it("engine notice only where relevant", () => {
    assert.equal(engineNoticeRelevant("market", "بازار چه خبر؟"), false);
    assert.equal(engineNoticeRelevant("news", "اخبار"), false);
    assert.equal(engineNoticeRelevant("stop_loss", "stop loss چند هست؟"), false);
    assert.equal(engineNoticeRelevant("general", "سلام دنیا"), false);
    assert.equal(engineNoticeRelevant("help", "راهنما"), true);
    assert.equal(engineNoticeRelevant("opportunities", "فرصت‌ها"), true);
    assert.equal(engineNoticeRelevant("why", "چرا موتور خاموشه؟"), true);
  });
});

describe("/start help", () => {
  const { plain, html } = both(helpBlocks());
  it("no internal jargon, footer once, bold heading", () => {
    assertClean(plain, "help");
    assertClean(html, "help-html");
    footerOnce(plain);
    footerOnce(html);
    assert.match(html, /^<b>🤖 راهنمای AHOS<\/b>/);
    balanced(html);
  });
  it("snapshot", () => {
    assert.equal(
      plain,
      [
        "🤖 راهنمای AHOS",
        "می‌توانی این‌ها را بپرسی:",
        "• «بازار چه خبر؟» — قیمت و حال بیت‌کوین، اتریوم و سولانا",
        "• «فرصت‌ها» — توکن‌های در حال پایش",
        "• «اخبار» یا «اخبار سولانا» — تیترهای اخیر",
        "• «چرا PEPE؟» — دلیل حکم یک توکن",
        "• «PEPE را زیر نظر بگیر» — افزودن به واچ‌لیست",
        "• «وضعیت سیستم» · «شورا» · «درس‌ها»",
        "",
        "ℹ️ روشن/خاموش کردن موتور و ثبت خرید کاغذی فقط از داشبورد محلی انجام می‌شود.",
        "",
        `— ${FOOTER}`,
      ].join("\n"),
    );
  });
  it("greeting is short and jargon-free", () => {
    const g = renderPlain(greetingBlocks(3), FOOTER);
    assertClean(g, "greeting");
    assert.ok(g.includes(fa(3)));
    assert.ok(!/[۰-۹]/.test(renderPlain(greetingBlocks(null))), "no count invented when unavailable");
  });
});

describe("market reply", () => {
  const blocks = marketBlocks(snap(), NOW);
  const { plain, html } = both(blocks);
  it("BTC/ETH/SOL prices first, taken from the snapshot", () => {
    const lines = plain.split("\n");
    assert.equal(lines[0], "📊 وضعیت بازار");
    assert.ok(lines[1].startsWith("• بیت‌کوین: ") && lines[1].includes(fa(65432)));
    assert.ok(lines[2].startsWith("• اتریوم: ") && lines[2].includes(fa(2510.5, 0)));
    assert.ok(lines[3].startsWith("• سولانا: ") && lines[3].includes(fa(150.25, 0)));
    assert.ok(plain.includes("حال بازار: خنثی (نوسان در محدوده)"));
    assert.ok(plain.includes(`شاخص ترس و طمع: ${fa(52)} از ۱۰۰ (خنثی)`));
    assert.ok(plain.includes("آخرین به‌روزرسانی: ۲۰ دقیقه پیش"));
  });
  it("news only as ≤3 Persian headlines, no English summary dump", () => {
    assert.ok(plain.includes("📰 تیترهای اخیر"));
    assert.ok(plain.includes("ارتقاء مین‌نت سولانا انجام شد"));
    assert.ok(!plain.includes("inflows"), "half-translated title must not appear");
    assert.ok(!plain.includes("Spot bitcoin ETFs"));
    assertClean(plain, "market");
    footerOnce(plain);
    balanced(html);
  });
  it("missing data stays honest: no invented numbers", () => {
    const empty = snap({
      market: {
        regime: "UNKNOWN", fearGreed: null, fearGreedLabel: null, btcPrice: null, btcChange24h: null,
        ethPrice: null, ethChange24h: null, solPrice: null, solChange24h: null, totalMcap: null,
        mcapChange24h: null, btcDominance: null, defiTvl: null, payload: {}, createdAt: null,
      },
      news: [],
    });
    const p = renderPlain(marketBlocks(empty, NOW), FOOTER);
    assert.ok(!/[0-9۰-۹]/.test(p), `no digits may appear when data is missing:\n${p}`);
    assert.ok(p.includes("نامشخص"));
    assert.ok(p.includes("داده کافی نیست"));
    assertClean(p, "market-empty");
    const none = renderPlain(marketBlocks(snap({ market: null }), NOW));
    assert.ok(none.includes("داده کافی نیست") && !/[0-9۰-۹]/.test(none));
  });
  it("stale snapshot is flagged", () => {
    const old = snap();
    (old.market as unknown as { createdAt: string }).createdAt = "2026-10-02T08:00:00Z";
    assert.ok(renderPlain(marketBlocks(old, NOW)).includes("ممکن است قدیمی باشد"));
  });
});

describe("news reply", () => {
  it("≤5 items, one line each, source link, no summary/importance dump", () => {
    const many = Array.from({ length: 9 }, (_, i) => ({ ...CLEAN_NEWS, titleFa: `خبر شماره ${i} درباره بازار` }));
    const p = renderPlain(newsBlocks(snap({ news: many }), "اخبار"), FOOTER);
    assert.equal((p.match(/^• /gm) || []).length, 5);
    assert.ok(!/اهمیت|منبع:|طبقه‌بندی/.test(p));
    assertClean(p, "news");
    const h = renderTelegramHtml(newsBlocks(snap({ news: many }), "اخبار"), FOOTER);
    assert.ok(h.includes('<a href="https://www.coindesk.com/x">CoinDesk</a>'));
    balanced(h);
  });
  it("half-translated titles fall back to the original, with one note", () => {
    const p = renderPlain(newsBlocks(snap(), "اخبار"));
    assert.ok(p.includes(MESSY_NEWS.titleOriginal));
    assert.ok(!p.includes(MESSY_NEWS.titleFa));
    assert.equal(p.split("به زبان اصلی آمده‌اند").length - 1, 1);
  });
  it("escapes untrusted titles/sources and drops non-http links", () => {
    const h = renderTelegramHtml(newsBlocks(snap({ news: [EVIL_NEWS] }), "اخبار"), FOOTER);
    assert.ok(!h.includes("<script>"));
    assert.ok(h.includes("&lt;script&gt;"));
    assert.ok(!h.includes("javascript:"));
    assert.ok(h.includes("&lt;b&gt;evil&lt;/b&gt; &amp; co"));
    balanced(h);
  });
  it("empty filter result is a short honest line", () => {
    const p = renderPlain(newsBlocks(snap({ news: [] }), "اخبار سولانا"));
    assert.ok(p.startsWith("📰 اخبار سولانا"));
    assert.ok(p.includes("خبری مطابق درخواستت ثبت نشده"));
  });
});

describe("stop loss / general / refusal", () => {
  it("stop loss without token: asks which token, invents no number", () => {
    const p = renderPlain(stopLossBlocks(null), FOOTER);
    assert.ok(p.includes("برای کدام توکن"));
    assert.ok(!/[0-9۰-۹]/.test(p));
    assertClean(p, "stoploss");
  });
  it("stop loss with token: shows recorded invalidation only", () => {
    const p = renderPlain(stopLossBlocks(OPP));
    assert.ok(p.includes("PEPE") && p.includes(OPP.invalidationFa as string));
    assert.ok(p.includes("حدس نمی‌زنم"));
  });
  it("general fallback has no filler, no counts of zero, no raw news", () => {
    const p = renderPlain(generalBlocks(0), FOOTER);
    assertClean(p, "general");
    assert.ok(!/[0-9۰-۹]/.test(p));
    assert.ok(!p.includes("0 حکم"));
    assert.ok(renderPlain(generalBlocks(2)).includes(`${fa(2)} فرصت خرید کاغذی`));
  });
  it("refusal is short, jargon-free and still refuses", () => {
    for (const intent of ["start", "stop", "paper_buy"]) {
      const d = gateChatControl({ intent, text: intent, channelClaimed: "telegram" });
      assert.equal(d.allowed, false);
      const p = renderPlain(blocksFromText(d.replyFa ?? ""), FOOTER);
      assertClean(p, `refusal-${intent}`);
      footerOnce(p);
      assert.ok(p.length < 260, `refusal too long (${p.length})`);
      assert.match(p, /^⛔ /);
    }
  });
});

describe("opportunities / why", () => {
  it("watch list shows Persian labels, single disclaimer note", () => {
    const p = renderPlain(oppBlocks(snap()), FOOTER);
    assert.ok(p.includes("در حال پایش (خرید نیست)"));
    assert.ok(p.includes("PEPE (solana) — پایش"));
    assertClean(p, "opp");
    footerOnce(p);
  });
  it("why reply is sectioned and keeps unknowns as one note", () => {
    const p = renderPlain(whyBlocks(OPP), FOOTER);
    assert.ok(p.startsWith("🔎 PEPE (solana)"));
    assert.ok(p.includes("دلایل") && p.includes("ریسک‌ها"));
    assert.ok(p.includes("داده ناقص: نقش کیف پول"));
    assertClean(p, "why");
  });
  it("system decision view without internal words", () => {
    const p = renderPlain(
      whyCanonicalBlocks({
        tokenKey: "k", symbol: "WIF", chain: "solana", address: null, outcome: "MONITOR_ONLY",
        identityState: null, securityState: "PASS", confidence: "MED", opportunityScore: null,
        paperAllowed: false, isPositive: false, monitoringOnly: true, primaryReason: null,
      }),
    );
    assert.ok(p.includes("فقط پایش"));
    assertClean(p, "why-canon");
  });
});

describe("rendering safety", () => {
  it("escapeHtml / safeUrl", () => {
    assert.equal(escapeHtml(`<a href="x">&</a>`), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;");
    assert.equal(safeUrl("javascript:alert(1)"), null);
    assert.equal(safeUrl("https://ok.example/a?b=1"), "https://ok.example/a?b=1");
    assert.equal(safeUrl('https://x"><script>'), null);
  });
  it("Telegram 4096 limit: huge replies are cut at whole blocks, HTML stays balanced", () => {
    const blocks = [title("big"), ...Array.from({ length: 400 }, (_, i) => bullet(`<b>آیتم ${i}</b> ${"x".repeat(40)}`, { label: "src&", url: "https://e.x/" + i }))];
    const h = renderTelegramHtml(blocks, FOOTER);
    const p = renderPlain(blocks, FOOTER);
    assert.ok(h.length <= TELEGRAM_MAX_CHARS, `html ${h.length}`);
    assert.ok(p.length <= TELEGRAM_MAX_CHARS, `plain ${p.length}`);
    balanced(h);
    footerOnce(h);
    footerOnce(p);
    assert.ok(h.includes("…"));
  });
  it("isMostlyPersian", () => {
    assert.equal(isMostlyPersian("ارتقاء مین‌نت سولانا"), true);
    assert.equal(isMostlyPersian(MESSY_NEWS.titleFa), false);
    assert.equal(isMostlyPersian("ok"), false);
  });
});

describe("shared response composer + phraser seam (no LLM configured)", () => {
  const draft = { intent: "market", blocks: marketBlocks(snap(), NOW), footer: FOOTER };
  const det = composeDeterministic(draft);
  const fake = (plain: string | null, opts: { throws?: boolean } = {}): ReplyPhraser => ({
    name: "fake-llm",
    async phrase() {
      if (opts.throws) throw new Error("provider down");
      return plain === null ? null : { plain };
    },
  });
  it("without a phraser the deterministic draft is final (both surfaces get the same text)", async () => {
    const out = await finalizeReply(draft);
    assert.equal(out.composer, "deterministic");
    assert.equal(out.plain, renderPlain(draft.blocks, FOOTER));
    assert.equal(out.html, renderTelegramHtml(draft.blocks, FOOTER));
  });
  it("locked drafts (refusals) are never rephrased", async () => {
    const locked = { intent: "stop", blocks: blocksFromText("⛔ x"), footer: FOOTER, locked: true };
    const out = await finalizeReply(locked, fake(`hi\n${FOOTER}`));
    assert.equal(out.composer, "deterministic");
  });
  it("phraser output with a new number is rejected → deterministic fallback", async () => {
    const out = await finalizeReply(draft, fake(`بیت‌کوین ۹۹٬۹۹۹ دلار\n${FOOTER}`));
    assert.equal(out.composer, "deterministic");
    assert.match(out.phraserRejected ?? "", /^NEW_NUMBER/);
    assert.equal(out.plain, det.plain);
  });
  it("jargon, missing/duplicate footer, empty, error → fallback", async () => {
    assert.match(validatePhrased(det.plain, `GM-04 ok\n${FOOTER}`, FOOTER) ?? "", /^JARGON/);
    assert.equal(validatePhrased(det.plain, "بدون پانویس", FOOTER), "FOOTER_NOT_EXACTLY_ONCE");
    assert.equal(validatePhrased(det.plain, `${FOOTER} ${FOOTER}`, FOOTER), "FOOTER_NOT_EXACTLY_ONCE");
    assert.equal(validatePhrased(det.plain, "  ", FOOTER), "EMPTY");
    assert.equal((await finalizeReply(draft, fake(null))).phraserRejected, "NO_OUTPUT");
    assert.equal((await finalizeReply(draft, fake("x", { throws: true }))).phraserRejected, "PHRASER_ERROR");
  });
  it("grounded rephrasing is accepted and its HTML is escaped (untrusted)", async () => {
    const out = await finalizeReply(draft, fake(`بازار آرام است؛ بیت‌کوین حدود ${fa(65432)} دلار <b>است</b>.\n${FOOTER}`));
    assert.equal(out.composer, "fake-llm");
    assert.ok(out.html.includes("&lt;b&gt;"));
    assert.ok(!out.html.includes("<b>"));
  });
  it("style guide forbids invented numbers and jargon", () => {
    assert.ok(RESPONSE_STYLE_FA.some((r) => r.includes("عدد")));
    assert.ok(RESPONSE_STYLE_FA.some((r) => r.includes("GM-xx")));
  });
});
