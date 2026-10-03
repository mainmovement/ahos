/**
 * Mission 9.5: self-test for the confirm-gated command surface
 * (chat_actions.ts). Covers exactly the attack cases the two independent
 * reviews (REDTEAM-19, Agent-16 QA) flagged, plus the write-ahead audit and the
 * lockout. No network, no DB, no real audit file (temp dir only).
 * Run: npm run test:chat-actions   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  ACTION_TTL_MS,
  LOCKOUT_MS,
  MAX_PAPER_QUANTITY,
  PendingActionStore,
  handleConfirmation,
  identityKey,
  isOwner,
  parseConfirmation,
  propose,
  summaryFaFor,
  type ActionDeps,
  type AuditFn,
  type Identity,
} from "../chat_actions.ts";
import { MemoryAuditSink, recordControlAudit } from "../chat_control_gate.ts";
import { DevMissionStore } from "../dev_missions.ts";

const TMP = mkdtempSync(join(tmpdir(), "ahos-actions-"));
process.env.AHOS_CONTROL_AUDIT_PATH = join(TMP, "audit.jsonl");
process.env.AHOS_DEV_MISSIONS_PATH = join(TMP, "dev_missions.jsonl");

const ENV = { TELEGRAM_ADMIN_USER_IDS: "111", TELEGRAM_ALLOWED_CHAT_IDS: "222" };
const OWNER: Identity = { channel: "telegram", userId: "111", proven: true };
const ADMIN2: Identity = { channel: "telegram", userId: "222", proven: true }; // reader-allowlist only
const DASH_A: Identity = { channel: "dashboard", userId: "sess-a", proven: true };
const DASH_B: Identity = { channel: "dashboard", userId: "sess-b", proven: true };
const STRANGER: Identity = { channel: "telegram", userId: "999", proven: true };
const CLAIMED_WEB: Identity = { channel: "web", userId: null }; // unproven

function sinkAudit(sink: MemoryAuditSink, log: Array<{ decision: string; reason: string }>): AuditFn {
  const fn = (p: Parameters<typeof recordControlAudit>[0]) => {
    const rec = recordControlAudit(p, sink);
    if (rec) log.push({ decision: rec.decision, reason: rec.reason });
    return rec;
  };
  return fn as unknown as AuditFn;
}

function deps(log: string[], missions = new DevMissionStore(join(TMP, "m.jsonl"))): ActionDeps {
  return {
    startEngine: async () => log.push("start"),
    stopEngine: async () => log.push("stop"),
    addWatch: async () => log.push("watch"),
    paperBuy: async (p) => (log.push(`paper:${p.quantity}`), { ok: true, messageFa: "ثبت شد — فقط کاغذی." }),
    recordDevMission: async (i) => {
      const rec = missions.append({ summaryFa: i.summaryFa, confirmCode: i.confirmCode, channel: i.channel, userId: i.userId });
      return rec ? { ok: true, messageFa: `✅ ثبت شد (شناسه ${rec.id}).` } : { ok: false, messageFa: "ثبت نشد." };
    },
  };
}

describe("owner identity (B1 / BL-3 / M1 / MJ-6)", () => {
  it("an unproven channel claim is never the owner, and there is no default to web", () => {
    assert.equal(isOwner(CLAIMED_WEB, ENV), false);
    assert.equal(isOwner({ channel: null, userId: null }, ENV), false);
    assert.equal(isOwner({ channel: "telegram", userId: "111" }, ENV), false); // missing proof
    assert.equal(isOwner({ channel: "dashboard", userId: null }, ENV), false);
  });
  it("the reader allowlist no longer grants control", () => {
    assert.equal(isOwner(ADMIN2, ENV), false);
  });
  it("a verified dashboard session is owner; a verified Telegram admin is owner", () => {
    assert.equal(isOwner(DASH_A, ENV), true);
    assert.equal(isOwner(OWNER, ENV), true);
  });
  it("two dashboard sessions get distinct identity keys (m2)", () => {
    assert.notEqual(identityKey(DASH_A), identityKey(DASH_B));
    // and one session cannot cancel the other's pending action
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "engine_stop", {}, DASH_A, "x", { env: ENV });
    assert.ok(p.ok);
    const code = p.ok ? p.action.code : "";
    const r = handleConfirmation(store, { op: "cancel", code }, DASH_B, "لغو", { env: ENV, deps: deps([]) });
    return r.then((out) => {
      assert.match(out.replyFa, /پیدا نشد/);
      assert.equal(out.executed, false);
    });
  });
});

describe("write-ahead audit (MJ-1)", () => {
  it("executes only when the EXECUTING record is written", async () => {
    const log: string[] = [];
    const auditLog: Array<{ decision: string; reason: string }> = [];
    const sink = new MemoryAuditSink();
    const audit = sinkAudit(sink, auditLog);
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "engine_stop", {}, OWNER, "خاموش کن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    const r = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit, deps: deps(log) });
    assert.equal(r.executed, true);
    assert.deepEqual(log, ["stop"]);
    assert.deepEqual(auditLog.map((a) => a.decision), ["PROPOSED", "EXECUTING", "CONFIRMED"]);
  });
  it("a broken audit sink aborts the action and burns the code", async () => {
    const log: string[] = [];
    const deadAudit = (() => null) as unknown as AuditFn;
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "engine_start", {}, OWNER, "روشن کن", { env: ENV, audit: deadAudit });
    const code = p.ok ? p.action.code : "";
    const r = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit: deadAudit, deps: deps(log) });
    assert.equal(r.executed, false);
    assert.deepEqual(log, []); // nothing ran
    assert.match(r.replyFa, /ثبت امنیتی .* نوشته نشد/);
    // The code is consumed: a later confirm with a working sink still cannot run it.
    const sink = new MemoryAuditSink();
    const r2 = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit: sinkAudit(sink, []), deps: deps(log) });
    assert.equal(r2.executed, false);
    assert.deepEqual(log, []);
  });
});

describe("wrong-code lockout (m5)", () => {
  it("five wrong codes lock the identity out for the TTL", async () => {
    const sink = new MemoryAuditSink();
    const audit = sinkAudit(sink, []);
    const store = new PendingActionStore(() => 0);
    for (let i = 0; i < 5; i++) {
      const r = await handleConfirmation(store, { op: "confirm", code: "ZZZZZZ" }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
      assert.equal(r.executed, false);
    }
    assert.equal(store.isLocked(OWNER), true);
    // Even a REAL proposal cannot be confirmed while locked.
    const p = propose(store, "engine_stop", {}, OWNER, "خاموش کن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    const r = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
    assert.equal(r.executed, false);
    assert.match(r.replyFa, /مسدود شد/);
    void LOCKOUT_MS;
  });
  it("a successful confirm clears the counter", async () => {
    const sink = new MemoryAuditSink();
    const audit = sinkAudit(sink, []);
    const store = new PendingActionStore(() => 0);
    for (let i = 0; i < 4; i++) {
      await handleConfirmation(store, { op: "confirm", code: "ZZZZZZ" }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
    }
    assert.equal(store.isLocked(OWNER), false);
    const p = propose(store, "engine_stop", {}, OWNER, "خاموش کن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    const r = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
    assert.equal(r.executed, true);
    // Counter cleared: four more wrong codes still do not lock.
    for (let i = 0; i < 4; i++) {
      await handleConfirmation(store, { op: "confirm", code: "ZZZZZZ" }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
    }
    assert.equal(store.isLocked(OWNER), false);
  });
  it("expiry still counts as an attempt", async () => {
    let t = 0;
    const sink = new MemoryAuditSink();
    const audit = sinkAudit(sink, []);
    const store = new PendingActionStore(() => t);
    const p = propose(store, "engine_stop", {}, OWNER, "خاموش کن", { env: ENV, audit });
    const code = p.ok ? p.action.code : "";
    t = ACTION_TTL_MS + 1;
    const r = await handleConfirmation(store, { op: "confirm", code }, OWNER, "تایید", { env: ENV, audit, deps: deps([]) });
    assert.equal(r.executed, false);
    assert.match(r.replyFa, /منقضی/);
    assert.equal(store.isLocked(OWNER), false);
    t = 0;
  });
});

describe("paper quantity cap (m6)", () => {
  it("clamps a model-chosen quantity", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "paper_buy", { symbol: "PEPE", tokenKey: "k", chain: "solana", quantity: 999999 }, OWNER, "بخر", { env: ENV });
    assert.ok(p.ok);
    assert.equal(p.ok ? p.action.params.quantity : null, MAX_PAPER_QUANTITY);
    assert.match(p.ok ? p.action.summaryFa : "", new RegExp(String(MAX_PAPER_QUANTITY)));
  });
  it("a null quantity stays null", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "paper_buy", { symbol: "PEPE", tokenKey: "k", chain: "solana" }, OWNER, "بخر", { env: ENV });
    assert.ok(p.ok);
    assert.equal(p.ok ? p.action.params.quantity : undefined, null);
  });
});

describe("dev-mission proposal integrity (M3 / MJ-7)", () => {
  it("the proposal shows the FULL stored summary, not a truncated prefix", () => {
    const long = "اضافه کردن هشدار طلا برای زمانی که شاخص ترس و طمع از حد خاصی عبور می‌کند و یک گزارش روزانه بساز";
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "dev_mission", { missionSummaryFa: long }, OWNER, "هشدار طلا", { env: ENV });
    assert.ok(p.ok);
    const summary = p.ok ? p.action.summaryFa : "";
    assert.match(summary, /گزارش روزانه/); // the tail is shown
    assert.ok(summary.length > 80);
  });
  it("the pending action binds the exact summary text", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "dev_mission", { missionSummaryFa: "ساخت دانشگاه" }, OWNER, "دانشگاه", { env: ENV });
    assert.ok(p.ok);
    assert.ok(p.ok && p.action.summaryHash !== null && p.action.summaryHash.length === 64);
  });
  it("secrets in the summary are redacted before the owner sees them", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "dev_mission", { missionSummaryFa: `کلید گوگل AIza${"a".repeat(35)} رو ذخیره کن` }, OWNER, "کلید", { env: ENV });
    assert.ok(p.ok);
    assert.ok(!(p.ok ? p.action.summaryFa : "").includes("AIza"));
    assert.match(p.ok ? p.action.summaryFa : "", /REDACTED/);
  });
  it("summaryFaFor never truncates a dev mission to 80 chars", () => {
    const s = summaryFaFor("dev_mission", { missionSummaryFa: "x".repeat(200) });
    assert.ok(s.length > 100);
  });
});

describe("non-owner and spoof attempts", () => {
  it("a non-owner gets no proposal and no code", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "engine_stop", {}, STRANGER, "خاموش کن", { env: ENV });
    assert.equal(p.ok, false);
    assert.equal(store.latestFor(STRANGER), undefined);
  });
  it("an unproven caller cannot propose even with an admin id in the body", () => {
    const store = new PendingActionStore(() => 0);
    const p = propose(store, "engine_stop", {}, CLAIMED_WEB, "خاموش کن", { env: ENV });
    assert.equal(p.ok, false);
  });
  it("parseConfirmation anchors on the whole message", () => {
    assert.equal(parseConfirmation("لطفا تایید ABC123 کن"), null);
    assert.equal(parseConfirmation("stop loss"), null);
    assert.equal(parseConfirmation("تایید ABC123 و بعد موتور رو روشن کن"), null);
    assert.equal(parseConfirmation("تایید ABC123")?.op, "confirm");
    // MN-8: English confirm words are no longer accepted (Persian and explicit only).
    assert.equal(parseConfirmation("confirm ABC123"), null);
    assert.equal(parseConfirmation("yes ABC123"), null);
    assert.equal(parseConfirmation("لغو ABC123")?.op, "cancel");
  });
});
