/**
 * Phase 7: intent router regression (realistic Persian phrasings) + price /
 * trade-signal / thanks replies. Run: npm run test:chat-intent
 * The reject/why predicates are read from chat.ts so this tests the same router
 * chat.ts uses. Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import { detectMajorAsset, isPriceQuestion, isThanksOnly, isTradeSignalRequest, routeIntent, stripGreeting } from "../chat_intent.ts";
import { gateChatControl } from "../chat_control_gate.ts";
import { priceBlocks, thanksBlocks, tradeSignalBlocks, type Snap } from "../chat_replies.ts";
import { renderPlain } from "../reply_format.ts";
import { validatePhrased } from "../response_composer.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const chatSrc = readFileSync(join(ROOT, "chat.ts"), "utf8");
function predicateFromChat(name: string): (t: string) => boolean {
  const m = chatSrc.match(new RegExp(`${name}: \\(t\\) => /(.+?)/i\\.test\\(t\\)`));
  assert.ok(m, `predicate ${name} not found in chat.ts`);
  const re = new RegExp(m[1], "i");
  return (t: string) => re.test(t);
}
const P = { isReject: predicateFromChat("isReject"), isWhy: predicateFromChat("isWhy") };
const route = (t: string) => routeIntent(t, P);

const OWNER_PRICE = "قیمت بیت کویین الان چقدر هست؟";
const OWNER_FUTURES =
  "یک ارز بسیار عالی و سوده بهم معرفی کن اسمش و اینکه چند درصد فیوچرز بزنم . لانگ یا سل ؟ حد ضرر ؟ حد سود رو هم بگو";

const CASES: Array<[string, string]> = [
  // owner-reported misses (17:29–17:30 Tehran)
  [OWNER_PRICE, "price"],
  [OWNER_FUTURES, "trade_signal"],
  // price
  ["قیمت بیت کوین چنده؟", "price"],
  ["بیتکوین الان چنده", "price"],
  ["قیمت بیت‌کوین", "price"],
  ["BTC چنده؟", "price"],
  ["bitcoin price?", "price"],
  ["قیمت اتریوم چقدره؟", "price"],
  ["ETH چند دلاره؟", "price"],
  ["سولانا چند شده؟", "price"],
  ["قیمت PEPE چنده؟", "price"],
  ["سلام، قیمت بیت کوین چقدره؟", "price"],
  // market
  ["بازار چه خبر؟", "market"],
  ["وضعیت بازار چطوره؟", "market"],
  ["بیت کوین", "market"],
  // news
  ["اخبار", "news"],
  ["آخرین اخبار سولانا", "news"],
  ["تیترهای امروز رو بگو", "news"],
  // opportunities
  ["فرصت‌ها", "opportunities"],
  ["الان چی بخرم؟", "opportunities"],
  ["بهترین توکن‌های امروز کدومن؟", "opportunities"],
  ["یه ارز خوب معرفی کن", "opportunities"],
  // why-token
  ["چرا PEPE؟", "why"],
  ["دلیل حکم WIF چیه؟", "why"],
  ["چرا رد شد؟", "reject"],
  // stop-loss for a specific token
  ["حد ضرر PEPE چنده؟", "stop_loss"],
  ["استاپ لاس WIF رو کجا بذارم؟", "stop_loss"],
  // trade-signal variants
  ["با چه اهرمی لانگ بگیرم؟", "trade_signal"],
  ["BTC رو شورت کنم یا لانگ؟", "trade_signal"],
  ["یه سیگنال فیوچرز بده", "trade_signal"],
  ["حد سود و حد ضرر اتریوم رو بگو", "trade_signal"],
  ["چند درصد بزنم؟ لوریج چند باشه", "trade_signal"],
  // greetings / thanks / help
  ["سلام", "greeting"],
  ["سلام خوبی؟", "greeting"],
  ["درود", "greeting"],
  ["مرسی", "thanks"],
  ["خیلی ممنون 🙏", "thanks"],
  ["دمت گرم", "thanks"],
  ["راهنما", "help"],
  // watchlist view vs add
  ["واچ‌لیست رو نشون بده", "watchlist"],
  ["PEPE را زیر نظر بگیر", "watch_add"],
  // GM-04 control still detected first (whole message)
  ["توقف", "stop"],
  ["stop loss", "stop_loss"],
];

describe("intent router regression (Persian phrasings)", () => {
  for (const [text, want] of CASES) {
    it(`${want} ← ${text}`, () => assert.equal(route(text), want));
  }
});

describe("helpers", () => {
  it("spelling variants of major assets", () => {
    for (const t of ["بیت کوین", "بیتکوین", "بیت کویین", "بیت‌کوین", "BTC", "bitcoin", "بيت كوين"]) assert.equal(detectMajorAsset(t), "BTC", t);
    for (const t of ["اتریوم", "ETH", "ethereum"]) assert.equal(detectMajorAsset(t), "ETH", t);
    for (const t of ["سولانا", "SOL"]) assert.equal(detectMajorAsset(t), "SOL", t);
    assert.equal(detectMajorAsset("سلام"), null);
  });
  it("price needs an asset or ticker; trade signal beats stop-loss", () => {
    assert.equal(isPriceQuestion("قیمت‌ها چطوره؟"), false);
    assert.equal(isTradeSignalRequest(OWNER_FUTURES), true);
    assert.equal(isTradeSignalRequest("حد ضرر PEPE چنده؟"), false);
    assert.equal(isTradeSignalRequest("سلام"), false); // «سل» inside «سلام» is not "sell"
  });
  it("thanks-only vs thanks + question; greeting stripping", () => {
    assert.equal(isThanksOnly("ممنون، حالا قیمت اتریوم چنده؟"), false);
    assert.equal(route("ممنون، حالا قیمت اتریوم چنده؟"), "price");
    assert.equal(stripGreeting("سلام، اخبار"), "اخبار");
  });
  it("owner messages never reach GM-04 control (no action, no audit capability)", () => {
    for (const t of [OWNER_PRICE, OWNER_FUTURES]) {
      const g = gateChatControl({ intent: route(t), text: t, channelClaimed: "telegram", userId: "u" });
      assert.equal(g.controlled, false, t);
    }
    const g = gateChatControl({ intent: route("سلام توقف"), text: "سلام توقف", channelClaimed: "telegram", userId: "u" });
    assert.equal(g.controlled, true, "greeting prefix must not hide a control command");
  });
});

const FOOTER = "تصمیم نهایی با کاربر است.";
const NOW = new Date("2026-10-02T14:00:00Z");
function snap(market: Record<string, unknown> | null): Snap {
  return { market, news: [], opportunities: [], canonicalDecisions: [] } as unknown as Snap;
}
const MARKET = { btcPrice: 79732.4, btcChange24h: 0.15, ethPrice: 2507, ethChange24h: 0.17, solPrice: null, solChange24h: null, createdAt: "2026-10-02T13:50:00Z" };

describe("replies", () => {
  it("fresh BTC price with change and update time, no stale warning", () => {
    const t = renderPlain(priceBlocks(snap(MARKET), "BTC", null, NOW), FOOTER);
    assert.match(t, /قیمت بیت‌کوین/);
    assert.match(t, /۷۹٬۷۳۲ دلار/);
    assert.match(t, /آخرین به‌روزرسانی/);
    assert.ok(!/قدیمی/.test(t));
  });
  it("stale price is flagged as not live", () => {
    const t = renderPlain(priceBlocks(snap({ ...MARKET, createdAt: "2026-08-28T10:00:00Z" }), "BTC", null, NOW));
    assert.match(t, /لحظه‌ای نیست/);
  });
  it("missing price / no market / unknown time → honest, no invented digits", () => {
    const sol = renderPlain(priceBlocks(snap(MARKET), "SOL", null, NOW));
    assert.match(sol, /داده کافی نیست/);
    assert.ok(!/[۰-۹0-9]{3}/.test(sol.split("آخرین")[0]), sol);
    const none = renderPlain(priceBlocks(snap(null), "ETH", null, NOW));
    assert.ok(!/[۰-۹0-9]/.test(none), none);
    const noTime = renderPlain(priceBlocks(snap({ ...MARKET, createdAt: null }), "BTC", null, NOW));
    assert.match(noTime, /نامشخص/);
    const pepe = renderPlain(priceBlocks(snap(MARKET), null, "PEPE", NOW));
    assert.match(pepe, /ثبت نمی‌شود/);
    assert.ok(!/[۰-۹0-9]/.test(pepe), pepe);
  });
  it("trade-signal reply: PAPER_ONLY, no coin pick, no numbers, offers فرصت‌ها and چرا", () => {
    const t = renderPlain(tradeSignalBlocks(), FOOTER);
    assert.ok(!/[۰-۹0-9]/.test(t), t);
    assert.match(t, /فرصت‌ها/);
    assert.match(t, /چرا/);
    assert.match(t, /کاغذی/);
    assert.ok(!/GM-\d|canonical|UNKNOWN/i.test(t));
    assert.ok(t.length < 700);
    assert.equal(validatePhrased(t, t, FOOTER), null);
  });
  it("thanks reply is short", () => {
    assert.ok(renderPlain(thanksBlocks()).length < 120);
  });
});
