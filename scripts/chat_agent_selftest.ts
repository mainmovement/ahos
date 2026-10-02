/**
 * Phase 7b: conversational agent (fake Gemini runner), read tools, number
 * validator, confirm-gated actions, memory redaction. No network, no DB, no key.
 * Run: npm run test:chat-agent   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ChatAgent,
  PROPOSE_TOOLS,
  READ_TOOLS,
  allowedNumbers,
  numericLiterals,
  runReadTool,
  systemPrompt,
  validateAgentAnswer,
  type ChatHelperRequest,
  type ChatHelperResult,
  type Part,
} from "../chat_agent.ts";
import {
  PendingActionStore,
  handleConfirmation,
  isOwner,
  parseConfirmation,
  propose,
  type ActionDeps,
  type AuditFn,
} from "../chat_actions.ts";
import { ConversationMemory, memoryKey, redactSecrets } from "../chat_memory.ts";
import { DevMissionStore } from "../dev_missions.ts";
import type { Snap } from "../chat_replies.ts";

import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
// Never touch the real audit log or the real dev-mission queue from a self-test.
const TMP = mkdtempSync(join(tmpdir(), "ahos-agent-"));
process.env.AHOS_CONTROL_AUDIT_PATH = join(TMP, "audit.jsonl");
process.env.AHOS_DEV_MISSIONS_PATH = join(TMP, "dev_missions.jsonl");

const FOOTER = "تصمیم نهایی با کاربر است.";
const NOW = new Date("2026-10-02T14:00:00Z");
const OWNER = { channel: "telegram", userId: "111" };
const STRANGER = { channel: "telegram", userId: "999" };
const DASH = { channel: "web", userId: null };
const ENV = { TELEGRAM_ADMIN_USER_IDS: "111", TELEGRAM_ALLOWED_CHAT_IDS: "" };

const SNAP = {
  market: {
    regime: "RANGE", fearGreed: 73, fearGreedLabel: "Greed",
    btcPrice: 79732.4, btcChange24h: 0.15, ethPrice: 2507, ethChange24h: 0.17, solPrice: 106.2, solChange24h: 1.91,
    totalMcap: 2.7e12, btcDominance: 59.2, createdAt: "2026-08-28T10:00:00Z",
  },
  news: [{ source: "CoinDesk", sourceUrl: "https://x", titleFa: "صندوق‌های بیت‌کوین ورودی داشتند", titleOriginal: "", publishedAt: "2026-10-02T12:00:00Z", relatedTokens: ["BTC"] }],
  opportunities: [
    { tokenKey: "sol:PEPE1", symbol: "PEPE", chain: "solana", address: "PEPE1", decision: "WATCH", confidence: "LOW", securityStatus: "PASS", reasonsFa: ["حجم بالا"], risksFa: ["نقدینگی کم"], unknownsFa: [], invalidationFa: "اگر نقدینگی کم شود", createdAt: "2026-10-02T13:00:00Z" },
  ],
  canonicalDecisions: [],
  canonicalReadModel: { status: "AVAILABLE" },
  state: { running: false, lastCycleAt: "2026-08-28T10:00:00Z", lastCycleStatus: "OK", cycleCount: 12 },
  paper: [], watchlist: [], health: { dimensions: [] },
} as unknown as Snap;

type Step = Part[] | { fail: string; status?: string };
function fakeRunner(steps: Step[]) {
  const calls: ChatHelperRequest[] = [];
  const runner = async (req: ChatHelperRequest): Promise<ChatHelperResult> => {
    calls.push(JSON.parse(JSON.stringify(req)));
    const s = steps.shift();
    if (!s) return { ok: false, parts: [], model: null, status: "UNAVAILABLE", reason_code: "NO_MORE", latency_ms: 1 };
    if (!Array.isArray(s)) return { ok: false, parts: [], model: null, status: s.status ?? "UNAVAILABLE", reason_code: s.fail, latency_ms: 1 };
    return { ok: true, parts: s, model: "gemini-flash-lite-latest", status: "READY", reason_code: "OK", latency_ms: 900 };
  };
  return { runner, calls };
}
const call = (name: string, args: Record<string, unknown> = {}): Part => ({ functionCall: { name, args }, thoughtSignature: "sig" });
const say = (text: string): Part => ({ text });

function input(text: string, store = new PendingActionStore(), identity = OWNER, history = [], missions?: DevMissionStore) {
  return { text, snap: SNAP, history, identity, store, missions: missions ?? new DevMissionStore(join(TMP, "missions.jsonl")), footer: FOOTER, now: NOW };
}

describe("read tools", () => {
  it("market has prices, Persian labels and staleness", () => {
    const m = runReadTool("get_market", {}, SNAP, NOW) as Record<string, unknown>;
    assert.equal(m.available, true);
    assert.equal(m.stale, true);
    assert.match(String(m.updatedAgoFa), /روز/);
    assert.equal((m.assets as Array<{ priceUsd: number }>)[0].priceUsd, 79732.4);
  });
  it("explain_token found / not found; no invented SL/TP", () => {
    const e = runReadTool("explain_token", { symbol: "pepe" }, SNAP, NOW) as Record<string, unknown>;
    assert.equal(e.found, true);
    assert.equal(e.invalidationFa, "اگر نقدینگی کم شود");
    assert.equal((runReadTool("explain_token", { symbol: "DOGE" }, SNAP, NOW) as { found: boolean }).found, false);
    const btc = runReadTool("explain_token", { symbol: "BTC" }, SNAP, NOW) as { isMajorAsset?: boolean; market?: { priceUsd: number } };
    assert.equal(btc.isMajorAsset, true);
    assert.equal(btc.market?.priceUsd, 79732.4);
  });
  it("registry is whitelisted: only read + propose tools; unknown tool is inert", () => {
    const names = [...READ_TOOLS, ...PROPOSE_TOOLS].map((t) => t.name);
    for (const n of names) assert.match(n, /^(get_|list_|explain_|propose_|submit_)/);
    assert.ok(!names.some((n) => /key|secret|token_set|constitution|authority|live|withdraw|transfer/i.test(n)));
    assert.deepEqual(runReadTool("delete_everything", {}, SNAP, NOW), { error: "UNKNOWN_TOOL" });
  });
});

describe("number validator", () => {
  it("normalizes Persian digits and separators", () => {
    assert.deepEqual(numericLiterals("۷۹٬۷۳۲ دلار و ۰٫۱۵٪"), ["79732", "0.15"]);
  });
  it("accepts tool numbers (rounded/scaled), rejects invented ones", () => {
    const src = [JSON.stringify(runReadTool("get_market", {}, SNAP, NOW))];
    assert.equal(validateAgentAnswer("بیت‌کوین ۷۹٬۷۳۲ دلار است (+۰٫۱۵٪)، ارزش کل ۲٫۷ تریلیون دلار.", src), null);
    assert.equal(validateAgentAnswer("بیت‌کوین حدود ۷۹٫۷ هزار دلار است.", src), null);
    assert.match(String(validateAgentAnswer("بیت‌کوین ۸۵٬۰۰۰ دلار است.", src)), /^NEW_NUMBER/);
    assert.equal(validateAgentAnswer("با اهرم ۲۰ لانگ بگیر", src), "TRADE_PICK");
    assert.equal(validateAgentAnswer("۳ فرصت داریم", src), null); // small counts allowed
    assert.ok(allowedNumbers(["2.7e12"]).size > 0);
  });
  it("rejects jargon and claims of execution", () => {
    assert.match(String(validateAgentAnswer("طبق GM-04 ...", [])), /^JARGON/);
    assert.equal(validateAgentAnswer("موتور را خاموش کردم.", []), "CLAIMS_EXECUTION");
  });
});

describe("agent loop", () => {
  it("free question → tool call → grounded Persian answer (thought signature echoed)", async () => {
    const { runner, calls } = fakeRunner([[call("get_market")], [say("بیت‌کوین الان ۷۹٬۷۳۲ دلار است؛ این داده قدیمی است.")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("قیمت بیت کویین الان چقدر هست؟"));
    assert.equal(r.ok, true);
    if (r.ok) {
      assert.deepEqual(r.toolsUsed, ["get_market"]);
      assert.match(r.plain, /۷۹٬۷۳۲/);
      assert.equal(r.locked, false);
    }
    assert.equal(calls.length, 2);
    const second = calls[1].contents;
    assert.equal(second[second.length - 2].parts[0].thoughtSignature, "sig");
    assert.ok(second[second.length - 1].parts[0].functionResponse);
    assert.match(calls[0].system, /PAPER_ONLY/);
  });
  it("invented number → VALIDATION failure (caller falls back)", async () => {
    const { runner, calls } = fakeRunner([[call("get_market")], [say("بیت‌کوین ۹۰٬۰۰۰ دلار است.")], [say("بیت‌کوین ۹۱٬۰۰۰ دلار است.")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("قیمت بیت کوین؟"));
    assert.equal(r.ok, false);
    if (!r.ok) assert.match(r.reason, /^VALIDATION:NEW_NUMBER/);
    assert.equal(calls.length, 3); // one corrective round, then give up
  });
  it("one corrective round: rejected draft → model retries with tool → accepted", async () => {
    const { runner, calls } = fakeRunner([[say("بیت‌کوین ۶۵ هزار دلار است")], [call("get_market")], [say("بیت‌کوین ۷۹٬۷۳۲ دلار است.")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("بازار چطوره؟"));
    assert.equal(r.ok, true);
    const fix = calls[1].contents[calls[1].contents.length - 1].parts[0].text ?? "";
    assert.match(fix, /پیام سیستم/);
    assert.match(fix, /عددی آوردی/);
  });
  it("tool output never carries raw English status codes", () => {
    const snap = { ...SNAP, canonicalReadModel: { status: "AVAILABLE" }, canonicalDecisions: [{ symbol: "GTA6", chain: "solana", outcome: "INSUFFICIENT_EVIDENCE", confidence: "UNKNOWN", securityState: "UNAVAILABLE", primaryReason: null }] } as unknown as Snap;
    const out = JSON.stringify(runReadTool("list_opportunities", {}, snap, NOW));
    assert.ok(!/INSUFFICIENT_EVIDENCE|UNAVAILABLE|UNKNOWN/.test(out), out);
    assert.match(out, /داده کافی نیست/);
  });
  it("answer without tools may not contain numbers it did not get", async () => {
    const { runner } = fakeRunner([[say("بیت‌کوین ۶۵ هزار دلار است")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("بیت کوین چنده"));
    assert.equal(r.ok, false);
  });
  it("multi-turn: history is sent; numbers from earlier assistant turns are allowed", async () => {
    const { runner, calls } = fakeRunner([[say("همان‌طور که گفتم ۷۹٬۷۳۲ دلار بود.")]]);
    const history = [
      { role: "user" as const, content: "قیمت بیت کوین", at: 1 },
      { role: "assistant" as const, content: "بیت‌کوین ۷۹٬۷۳۲ دلار", at: 2 },
    ];
    const r = await new ChatAgent({ runner, env: ENV }).run({ ...input("دوباره بگو"), history });
    assert.equal(r.ok, true);
    assert.equal(calls[0].contents.length, 3);
    assert.equal(calls[0].contents[1].role, "model");
  });
  it("provider failures: quota opens breaker for 10 min; 3 transient failures open 60 s", async () => {
    let t = 1_000_000;
    const q = fakeRunner([{ fail: "HTTP_429", status: "QUOTA_EXHAUSTED" }]);
    const a = new ChatAgent({ runner: q.runner, now: () => t, env: ENV });
    assert.equal((await a.run(input("سلام"))).ok, false);
    assert.ok(a.isOpen());
    t += 601_000;
    assert.ok(!a.isOpen());
    const f = fakeRunner([{ fail: "NETWORK" }, { fail: "NETWORK" }, { fail: "NETWORK" }]);
    const b = new ChatAgent({ runner: f.runner, now: () => t, env: ENV });
    for (let i = 0; i < 3; i++) await b.run(input("سلام"));
    assert.ok(b.isOpen());
    const r = await b.run(input("سلام"));
    assert.equal(!r.ok && r.reason, "CIRCUIT_OPEN");
  });
  it("trading-advice request: model may answer from tools; invented leverage numbers rejected", async () => {
    const bad = say("این فقط تحلیل کاغذی است، نه سیگنال شخصی. سیستم PEPE را در حالت پایش دارد. اهرم ۱۰ پیشنهاد می‌شود.");
    const { runner } = fakeRunner([[call("list_opportunities")], [bad], [bad]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("یک ارز سودده معرفی کن، چند درصد فیوچرز بزنم؟"));
    // «۱۰» is a small number (allowed), so this rests on the TRADE_PICK rule.
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "VALIDATION:TRADE_PICK");
    for (const bad of ["حد ضرر ۵٪ بگذار", "۲۰x لانگ", "اهرم: ۳", "take profit 2"]) assert.equal(validateAgentAnswer(bad, []), "TRADE_PICK", bad);
    assert.equal(validateAgentAnswer("اهرم ریسک را چند برابر می‌کند؛ حد ضرر را خودت تعیین کن.", []), null);
  });
  it("trading-advice request answered honestly from tools passes", async () => {
    const { runner } = fakeRunner([[call("list_opportunities")], [say("این فقط تحلیل کاغذی سیستم است، نه سیگنال شخصی. الان PEPE فقط در حالت پایش است و حکم خرید ندارد. عدد اهرم، حد سود یا حد ضرر پیشنهاد نمی‌کنم.")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("یک ارز سودده معرفی کن"));
    assert.equal(r.ok, true);
  });
});

describe("confirm-gated commands", () => {
  it("model proposal → locked confirmation text with code; nothing executed", async () => {
    const store = new PendingActionStore(() => 0);
    const { runner } = fakeRunner([[call("propose_engine_stop")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("موتور رو خاموش کن", store));
    assert.equal(r.ok, true);
    if (r.ok) {
      assert.equal(r.locked, true);
      assert.ok(r.proposal);
      assert.match(r.plain, new RegExp(`تایید ${r.proposal!.code}`));
      assert.match(r.plain, /هنوز اجرا نشده/);
    }
  });
  it("non-owner proposal is denied (no pending action)", async () => {
    const store = new PendingActionStore(() => 0);
    const { runner } = fakeRunner([[call("propose_engine_start")]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("موتور رو روشن کن", store, STRANGER));
    assert.equal(r.ok && r.proposal, undefined);
    assert.ok(r.ok && /فقط برای مالک/.test(r.plain));
  });
  it("paper buy for unknown token is not proposed", async () => {
    const store = new PendingActionStore(() => 0);
    const { runner } = fakeRunner([[call("propose_paper_buy", { symbol: "DOGE" })]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("DOGE بخر کاغذی", store));
    assert.ok(r.ok && !r.proposal && /در فهرست/.test(r.plain));
  });

  const audits: Array<{ decision: string; intent: string }> = [];
  const audit = ((p: { decision: string; intent: string }) => {
    audits.push({ decision: p.decision, intent: p.intent });
    return null;
  }) as unknown as AuditFn;
  function deps(log: string[], missions = new DevMissionStore(join(TMP, "missions.jsonl"))): ActionDeps {
    return {
      startEngine: async () => log.push("start"),
      stopEngine: async () => log.push("stop"),
      addWatch: async (i) => log.push(`watch:${i.symbol}`),
      paperBuy: async (p) => (log.push(`paper:${p.symbol}`), { ok: true, messageFa: "ثبت شد — فقط کاغذی." }),
      recordDevMission: async (i) => {
        const rec = missions.append({ summaryFa: i.summaryFa, channel: i.channel, userId: i.userId });
        return rec
          ? { ok: true, messageFa: `✅ ماموریت توسعه ثبت شد (شناسه ${rec.id}).` }
          : { ok: false, messageFa: "ماموریت توسعه ثبت نشد." };
      },
    };
  }

  it("confirm executes exactly once via injected dashboard-path deps; audited PROPOSED→CONFIRMED", async () => {
    let t = 0;
    const store = new PendingActionStore(() => t);
    const p = propose(store, "engine_stop", {}, OWNER, "خاموش کن", { env: ENV, audit });
    assert.ok(p.ok);
    const code = p.ok ? p.action.code : "";
    const log: string[] = [];
    const parsed = parseConfirmation(`تایید ${code.toLowerCase()}`)!;
    const r1 = await handleConfirmation(store, parsed, OWNER, "x", { env: ENV, audit, deps: deps(log) });
    assert.equal(r1.executed, true);
    const r2 = await handleConfirmation(store, parsed, OWNER, "x", { env: ENV, audit, deps: deps(log) });
    assert.equal(r2.executed, false);
    assert.deepEqual(log, ["stop"]);
    assert.deepEqual(audits.slice(-2).map((a) => a.decision), ["PROPOSED", "CONFIRMED"]);
    t += 1;
  });
  it("wrong identity, expiry, cancel, bare words never execute", async () => {
    let t = 0;
    const store = new PendingActionStore(() => t);
    const log: string[] = [];
    const p = propose(store, "engine_start", {}, OWNER, "روشن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    assert.equal((await handleConfirmation(store, { op: "confirm", code }, STRANGER, "x", { env: ENV, audit, deps: deps(log) })).executed, false);
    assert.equal((await handleConfirmation(store, { op: "confirm", code }, DASH, "x", { env: ENV, audit, deps: deps(log) })).executed, false);
    t += 5 * 60 * 1000 + 1;
    const exp = await handleConfirmation(store, { op: "confirm", code }, OWNER, "x", { env: ENV, audit, deps: deps(log) });
    assert.equal(exp.executed, false);
    assert.match(exp.replyFa, /منقضی/);
    const p2 = propose(store, "watch_add", { symbol: "PEPE", tokenKey: "k", chain: "solana" }, OWNER, "x", { env: ENV, audit });
    assert.ok(p2.ok);
    const c = await handleConfirmation(store, { op: "cancel", code: null }, OWNER, "لغو", { env: ENV, audit, deps: deps(log) });
    assert.match(c.replyFa, /لغو شد/);
    assert.deepEqual(log, []);
    for (const t2 of ["تایید", "stop loss", "تایید کن موتور رو", "توقف", "بله"]) assert.equal(parseConfirmation(t2), null, t2);
    assert.equal(parseConfirmation("لغو")?.op, "cancel");
  });
  it("owner identity rules", () => {
    assert.equal(isOwner(OWNER, ENV), true);
    assert.equal(isOwner(STRANGER, ENV), false);
    assert.equal(isOwner({ channel: "telegram", userId: "" }, ENV), false);
    assert.equal(isOwner({ channel: "telegram", userId: "111" }, {}), false); // empty allowlist → nobody
    assert.equal(isOwner(DASH, ENV), true);
    assert.equal(isOwner({ channel: "api", userId: null }, ENV), false);
  });
});

describe("dev missions (Phase 8)", () => {
  const seen: Array<{ decision: string; intent: string }> = [];
  const audit = ((p: { decision: string; intent: string }) => {
    seen.push({ decision: p.decision, intent: p.intent });
    return null;
  }) as unknown as AuditFn;
  function deps(_log: string[], missions: DevMissionStore): ActionDeps {
    return {
      startEngine: async () => undefined,
      stopEngine: async () => undefined,
      addWatch: async () => undefined,
      paperBuy: async () => ({ ok: false, messageFa: "—" }),
      recordDevMission: async (i) => {
        const rec = missions.append({ summaryFa: i.summaryFa, channel: i.channel, userId: i.userId });
        return rec
          ? { ok: true, messageFa: `✅ ماموریت توسعه ثبت شد (شناسه ${rec.id}) و در صف تیم مهندسی است. کاری هنوز انجام نشده است.` }
          : { ok: false, messageFa: "ماموریت توسعه ثبت نشد." };
      },
    };
  }

  it("owner: submit_dev_mission → warm locked proposal with code; nothing queued yet", async () => {
    const store = new PendingActionStore(() => 0);
    const ms = new DevMissionStore(join(TMP, "ms-a.jsonl"));
    const { runner } = fakeRunner([[call("submit_dev_mission", { summaryFa: "ساخت دانشگاه برای یادگیری مهارت‌ها" })]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("دانشگاه رو بساز", store, OWNER, [], ms));
    assert.equal(r.ok, true);
    if (r.ok) {
      assert.equal(r.locked, true);
      assert.ok(r.proposal);
      assert.match(r.plain, /خودم کد نمی‌نویسم/);
      assert.match(r.plain, /آماده ثبت است \(هنوز ثبت نشده\)/);
      assert.match(r.plain, new RegExp(`تایید ${r.proposal!.code}`));
    }
    assert.equal(ms.records().length, 0); // confirmed? not yet → nothing queued
  });
  it("non-owner: submit_dev_mission is denied, nothing queued", async () => {
    const store = new PendingActionStore(() => 0);
    const ms = new DevMissionStore(join(TMP, "ms-b.jsonl"));
    const { runner } = fakeRunner([[call("submit_dev_mission", { summaryFa: "یک فیچر جدید اضافه کن" })]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("فیچر جدید اضافه کن", store, STRANGER, [], ms));
    assert.ok(r.ok && !r.proposal);
    assert.ok(r.ok && /فقط برای مالک/.test(r.plain));
    assert.equal(ms.records().length, 0);
  });
  it("empty summary is not proposed", async () => {
    const store = new PendingActionStore(() => 0);
    const ms = new DevMissionStore(join(TMP, "ms-c.jsonl"));
    const { runner } = fakeRunner([[call("submit_dev_mission", { summaryFa: "   " })]]);
    const r = await new ChatAgent({ runner, env: ENV }).run(input("دانشگاه", store, OWNER, [], ms));
    assert.ok(r.ok && !r.proposal && /خالی است/.test(r.plain));
    assert.equal(ms.records().length, 0);
  });
  it("list_dev_missions: owner sees the queue, non-owner does not", () => {
    const ms = new DevMissionStore(join(TMP, "ms-d.jsonl"), { now: () => NOW });
    ms.append({ summaryFa: "راه‌اندازی عامل اخبار", channel: "telegram", userId: "111" });
    const owner = runReadTool("list_dev_missions", {}, SNAP, NOW, { missions: ms, owner: true }) as {
      count: number;
      items: Array<{ id: string; statusFa: string }>;
    };
    assert.equal(owner.count, 1);
    assert.equal(owner.items[0].id, "DM-000001");
    assert.equal(owner.items[0].statusFa, "در صف");
    const stranger = runReadTool("list_dev_missions", {}, SNAP, NOW, { missions: ms, owner: false }) as {
      count: number;
      noteFa: string;
    };
    assert.equal(stranger.count, 0);
    assert.match(stranger.noteFa, /فقط مالک/);
    const none = runReadTool("list_dev_missions", {}, SNAP, NOW, {}) as { count: number };
    assert.equal(none.count, 0);
  });
  it("confirm appends one QUEUED mission, single use, audited PROPOSED→CONFIRMED", async () => {
    let t = 0;
    const store = new PendingActionStore(() => t);
    const ms = new DevMissionStore(join(TMP, "ms-e.jsonl"), { now: () => NOW });
    const p = propose(store, "dev_mission", { missionSummaryFa: "اضافه کردن هشدار طلا" }, OWNER, "هشدار طلا رو اضافه کن", { env: ENV, audit });
    assert.ok(p.ok);
    const code = p.ok ? p.action.code : "";
    const parsed = parseConfirmation(`تایید ${code}`)!;
    const r1 = await handleConfirmation(store, parsed, OWNER, "x", { env: ENV, audit, deps: deps([], ms) });
    assert.equal(r1.executed, true);
    assert.match(r1.replyFa, /ثبت شد/);
    assert.match(r1.replyFa, /هنوز انجام نشده/);
    // Single use: re-confirming the same code does not append a second mission.
    const r2 = await handleConfirmation(store, parsed, OWNER, "x", { env: ENV, audit, deps: deps([], ms) });
    assert.equal(r2.executed, false);
    const recs = ms.records();
    assert.equal(recs.length, 1);
    assert.equal(recs[0].status, "QUEUED");
    assert.equal(recs[0].summaryFa, "اضافه کردن هشدار طلا");
    assert.ok(!recs[0].userIdHash.includes("111")); // hashed, never raw
    assert.equal(ms.verify().ok, true);
    assert.deepEqual(seen.slice(-2).map((a) => a.decision), ["PROPOSED", "CONFIRMED"]);
    t += 1;
  });
  it("cancel never queues; wrong identity never queues", async () => {
    const store = new PendingActionStore(() => 0);
    const ms = new DevMissionStore(join(TMP, "ms-f.jsonl"));
    const p = propose(store, "dev_mission", { missionSummaryFa: "بهتر کردن داشبورد" }, OWNER, "داشبورد رو بهتر کن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    const c = await handleConfirmation(store, { op: "cancel", code }, OWNER, "لغو", { env: ENV, audit, deps: deps([], ms) });
    assert.match(c.replyFa, /لغو شد/);
    const p2 = propose(store, "dev_mission", { missionSummaryFa: "فیچر X" }, OWNER, "x", { env: ENV, audit });
    const code2 = p2.ok ? p2.action.code : "";
    const s = await handleConfirmation(store, { op: "confirm", code: code2 }, STRANGER, "x", { env: ENV, audit, deps: deps([], ms) });
    assert.equal(s.executed, false);
    assert.equal(ms.records().length, 0);
  });
  it("system prompt tells the model it does not write code and must not claim work done", () => {
    const s = systemPrompt(NOW);
    assert.match(s, /کدی نمی‌نویسی/);
    assert.match(s, /submit_dev_mission/);
    assert.match(s, /انجام شده/);
  });
});

describe("memory", () => {
  it("keeps last N turns, redacts secrets, hashes keys, expires", () => {
    let t = 0;
    const m = new ConversationMemory({ maxTurns: 2, ttlMs: 1000, now: () => t });
    const k = memoryKey("telegram", "111");
    assert.ok(!k.includes("111"));
    m.append(k, "a", "b");
    m.append(k, "my key is AIza" + "x".repeat(30), "c");
    m.append(k, "e", "f");
    const turns = m.get(k);
    assert.equal(turns.length, 4);
    assert.ok(!turns.some((x) => x.content.includes("AIza")));
    t += 2000;
    assert.equal(m.get(k).length, 0);
    assert.equal(redactSecrets("TELEGRAM_BOT_TOKEN=123:abc"), "[REDACTED]");
  });
  it("system prompt carries the PAPER_ONLY / no-signal / propose-only rules", () => {
    const s = systemPrompt(NOW);
    assert.match(s, /سیگنال شخصی/);
    assert.match(s, /propose_/);
    assert.match(s, /stop loss/);
  });
});
