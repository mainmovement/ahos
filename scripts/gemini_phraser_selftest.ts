/**
 * Phase 6: Gemini phraser (ReplyPhraser) with a fake helper runner.
 * No network, no Python, no key. Run: npm run test:gemini-phraser
 * Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { GeminiPhraser, cleanModelText, getDefaultPhraser, helperEnv, type HelperRequest, type HelperResult } from "../gemini_phraser.ts";
import { finalizeReply, phrasedHtml, type GroundedDraft } from "../response_composer.ts";
import { bullet, line, title } from "../reply_format.ts";

const FOOTER = "تصمیم نهایی با کاربر است.";
const draft: GroundedDraft = {
  intent: "market",
  footer: FOOTER,
  blocks: [title("📊 وضعیت بازار"), bullet("بیت‌کوین: ۶۴٬۲۰۰ دلار"), bullet("اتریوم: ۳٬۱۰۰ دلار"), line("داده کافی نیست")],
};

function okRes(text: string, model = "gemini-flash-lite-latest"): HelperResult {
  return { ok: true, text, model, status: "READY", reason_code: "OK", latency_ms: 900 };
}
function badRes(status: string, reason: string): HelperResult {
  return { ok: false, text: null, model: null, status, reason_code: reason, latency_ms: 50 };
}
function fakeRunner(results: (HelperResult | null | "throw")[]) {
  const calls: HelperRequest[] = [];
  const runner = async (req: HelperRequest) => {
    calls.push(req);
    const r = results.shift();
    if (r === "throw") throw new Error("boom");
    return r ?? null;
  };
  return { runner, calls };
}

describe("GeminiPhraser", () => {
  it("sends only the footer-less draft text + style; appends the footer itself", async () => {
    const { runner, calls } = fakeRunner([okRes("بازار امروز\n• بیت‌کوین: ۶۴٬۲۰۰ دلار\n• اتریوم: ۳٬۱۰۰ دلار\nداده کافی نیست")]);
    const p = new GeminiPhraser({ runner });
    const out = await finalizeReply(draft, p);
    assert.equal(out.composer, "gemini");
    assert.equal(calls.length, 1);
    assert.ok(!calls[0].draft.includes(FOOTER));
    assert.ok(calls[0].draft.includes("۶۴٬۲۰۰"));
    assert.deepEqual(calls[0].models, ["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]);
    assert.ok(out.plain.endsWith(`— ${FOOTER}`));
    assert.equal(out.plain.split(FOOTER).length - 1, 1);
    assert.ok(out.html.startsWith("<b>بازار امروز</b>"));
    assert.ok(out.html.endsWith(`<i>— ${FOOTER}</i>`));
  });

  it("model text with a new number is rejected by the composer (deterministic fallback)", async () => {
    const { runner } = fakeRunner([okRes("بیت‌کوین ۷۰٬۰۰۰ دلار")]);
    const out = await finalizeReply(draft, new GeminiPhraser({ runner }));
    assert.equal(out.composer, "deterministic");
    assert.match(out.phraserRejected ?? "", /^NEW_NUMBER/);
  });

  it("strips a model-written footer, markdown bold/headers; HTML from model is escaped", async () => {
    const t = cleanModelText(`## عنوان\n**بیت‌کوین** بالا\n- مورد\n${FOOTER}`, FOOTER);
    assert.equal(t, "عنوان\nبیت‌کوین بالا\n• مورد");
    const { runner } = fakeRunner([okRes(`بازار\n• <script>x</script> آرام\n— ${FOOTER}`)]);
    const out = await finalizeReply(draft, new GeminiPhraser({ runner }));
    assert.equal(out.composer, "gemini");
    assert.ok(!out.html.includes("<script>"));
    assert.ok(out.html.includes("&lt;script&gt;"));
  });

  it("locked drafts and drafts with links are never sent", async () => {
    const { runner, calls } = fakeRunner([okRes("x"), okRes("y")]);
    const p = new GeminiPhraser({ runner });
    assert.equal((await finalizeReply({ ...draft, locked: true }, p)).composer, "deterministic");
    const news: GroundedDraft = { ...draft, blocks: [title("اخبار"), bullet("خبر", { label: "منبع", url: "https://example.com/a" })] };
    assert.equal((await finalizeReply(news, p)).composer, "deterministic");
    assert.equal(p.stats.lastReason, "SKIPPED_HAS_LINKS");
    assert.equal(calls.length, 0);
  });

  it("3 consecutive transient failures open the breaker for 60s, then it retries", async () => {
    let now = 1_000_000;
    const { runner, calls } = fakeRunner([badRes("UNAVAILABLE", "HTTP_503"), null, "throw", okRes("بازار\n• آرام")]);
    const p = new GeminiPhraser({ runner, now: () => now });
    for (let i = 0; i < 3; i++) assert.equal((await finalizeReply(draft, p)).composer, "deterministic");
    assert.ok(p.isOpen());
    assert.equal((await finalizeReply(draft, p)).phraserRejected, "NO_OUTPUT");
    assert.equal(calls.length, 3);
    now += 60_001;
    assert.equal((await finalizeReply(draft, p)).composer, "gemini");
    assert.equal(p.stats.consecutiveFailures, 0);
  });

  for (const [status, reason] of [["AUTH_FAILED", "HTTP_401"], ["QUOTA_EXHAUSTED", "HTTP_429"], ["AUTH_FAILED", "NO_CREDENTIAL"], ["UNAVAILABLE", "NOT_WINDOWS"]]) {
    it(`${status}/${reason} opens the breaker for 10 minutes after one failure`, async () => {
      let now = 5_000;
      const { runner, calls } = fakeRunner([badRes(status, reason)]);
      const p = new GeminiPhraser({ runner, now: () => now });
      await finalizeReply(draft, p);
      now += 599_000;
      assert.ok(p.isOpen());
      await finalizeReply(draft, p);
      assert.equal(calls.length, 1);
      now += 2_000;
      assert.ok(!p.isOpen());
    });
  }

  it("helper env carries no DB/web/telegram secrets and forces UTF-8", () => {
    const env = helperEnv({ PATH: "p", SystemRoot: "C:\\Windows", DATABASE_URL: "postgres://x", AHOS_WEB_API_TOKEN: "t", TELEGRAM_BOT_TOKEN: "b", HTTPS_PROXY: "http://proxy" });
    assert.equal(env.DATABASE_URL, undefined);
    assert.equal(env.AHOS_WEB_API_TOKEN, undefined);
    assert.equal(env.TELEGRAM_BOT_TOKEN, undefined);
    assert.equal(env.PYTHONIOENCODING, "utf-8");
    assert.equal(env.PYTHONUTF8, "1");
    assert.equal(env.HTTPS_PROXY, "http://proxy");
  });

  it("AHOS_PHRASER=off disables the phraser", () => {
    assert.equal(getDefaultPhraser({ AHOS_PHRASER: "off" }), null);
  });

  it("phrasedHtml only bolds a short title when a body follows", () => {
    assert.equal(phrasedHtml(`فقط یک خط\n\n— ${FOOTER}`, FOOTER), `فقط یک خط\n\n<i>— ${FOOTER}</i>`);
    assert.ok(phrasedHtml(`عنوان\nبدنه\n\n— ${FOOTER}`, FOOTER).startsWith("<b>عنوان</b>\n"));
  });
});
