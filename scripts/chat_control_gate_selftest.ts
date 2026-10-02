/**
 * GM-04 chat control capability gate (conservative, capability-reducing form).
 * Run: npm run test:chat-control-gate
 * Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  CONTROL_INTENTS,
  FileAuditSink,
  GENESIS_HASH,
  MemoryAuditSink,
  defaultAuditPath,
  detectControlCommand,
  gateChatControl,
  hashId,
  looksLikePaperBuy,
  normalizeCommandText,
  recordControlAudit,
  verifyAuditLines,
  type AuditSink,
} from "../chat_control_gate.ts";

const NEGATIVES = [
  "stop loss", "stop loss چنده؟", "stoploss", "Stop-Loss", "start-up", "startup", "restart",
  "nonstop", "unstoppable", "start the analysis of BTC", "stop loss for PEPE?", "how do I stop loss",
  "قیمت توقف ضرر چنده", "حد توقف ضرر", "توقف ضرر", "شروع بازار کیه؟", "روشن‌فکر", "خاموشی بازار",
  "چرا موتور خاموشه؟", "موتور روشنه؟", "بازار چه خبر؟", "paper trading چیه", "راهنما", "",
  "stop stop stop now", "please start the analysis", "starting", "stopped", "استارتاپ",
];
const STARTS = [
  "start", "START", " Start ", "start!", "/start", "/start@Sun_sniperbot", "please start",
  "شروع", "شروع کن", "لطفا شروع کن", "لطفاً روشن کن", "روشنش کن", "استارت!", "موتور رو روشن کن",
  "ｓｔａｒｔ", "st\u200Bart", "\u202Bشروع\u202C", "start engine", "شروع کن؟",
];
const STOPS = [
  "stop", "STOP", " stop! ", "/stop", "/stop@Sun_sniperbot", "Stop.", "please stop", "stop please",
  "توقف", "توقف کن", "لطفا خاموش کن", "خاموشش کن", "استاپ", "موتور را خاموش کن",
  "ｓｔｏｐ", "st\u200Bop", "s\u200Ct\u200Bop".replace("\u200C", ""), "stop\u00A0engine", "توقف!",
];

describe("detectControlCommand: whole-message only", () => {
  for (const t of NEGATIVES) {
    it(`does NOT match ${JSON.stringify(t)}`, () => assert.equal(detectControlCommand(t), null));
  }
  for (const t of STARTS) {
    it(`start: ${JSON.stringify(t)}`, () => assert.equal(detectControlCommand(t), "start"));
  }
  for (const t of STOPS) {
    it(`stop: ${JSON.stringify(t)}`, () => assert.equal(detectControlCommand(t), "stop"));
  }
  it("Arabic-letter variants normalize (ي/ك)", () => {
    assert.equal(normalizeCommandText("خاموشش كن"), "خاموشش کن");
    assert.equal(normalizeCommandText("روشني"), "روشنی");
  });
  it("ZWNJ becomes a space; stop-loss with ZWNJ still not a command", () => {
    assert.equal(detectControlCommand("توقف\u200Cضرر"), null);
  });
});

describe("looksLikePaperBuy: explicit phrase only", () => {
  for (const t of ["خریدم PEPE", "خرید کاغذی ثبت کن", "ثبت خرید", "paper buy WIF", "PAPER-BUY"]) {
    it(`buy: ${t}`, () => assert.equal(looksLikePaperBuy(t), true));
  }
  for (const t of ["paper trading چیه", "paper", "موقعیت‌های کاغذی", "newspaper buyer"]) {
    it(`not buy: ${t}`, () => assert.equal(looksLikePaperBuy(t), false));
  }
});

describe("gateChatControl: deny-by-default for every claimed channel", () => {
  const channels = ["telegram", "web", "api", "dashboard", "local", "LOCAL_DASHBOARD", undefined, null, "", "web\u200B", "../../x"];
  for (const intent of Object.keys(CONTROL_INTENTS)) {
    for (const ch of channels) {
      it(`${intent} refused for channel=${JSON.stringify(ch)}`, () => {
        const d = gateChatControl({ intent, text: intent, channelClaimed: ch as string | null | undefined, userId: "42" });
        assert.equal(d.controlled, true);
        assert.equal(d.allowed, false);
        assert.equal(d.reason, "CHAT_PATH_CANNOT_PROVE_LOCAL_DASHBOARD");
        assert.match(d.replyFa ?? "", /غیرفعال است/);
        assert.match(d.replyFa ?? "", /هیچ تغییری اعمال نشد/);
      });
    }
  }
  it("covers exactly start/stop/paper_buy", () => {
    assert.deepEqual(Object.keys(CONTROL_INTENTS).sort(), ["paper_buy", "start", "stop"]);
  });
  for (const intent of ["market", "help", "greeting", "watch", "paper_list", "explain", "general"]) {
    it(`non-control intent ${intent} passes through`, () => {
      const d = gateChatControl({ intent, text: "x", channelClaimed: "telegram" });
      assert.equal(d.controlled, false);
    });
  }
});

describe("append-only hashed audit", () => {
  const SECRET_TEXT = "توقف 0xDEADBEEF user 987654321";
  it("records no raw text or raw id; chain verifies", () => {
    const sink = new MemoryAuditSink();
    const r1 = recordControlAudit({ surface: "chat", intent: "stop", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R", channelClaimed: "telegram", userId: "987654321", text: SECRET_TEXT }, sink);
    const r2 = recordControlAudit({ surface: "chat", intent: "start", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R", channelClaimed: "web", userId: null, text: "شروع" }, sink);
    assert.ok(r1 && r2);
    assert.equal(r1.prev_hash, GENESIS_HASH);
    assert.equal(r2.prev_hash, r1.entry_hash);
    const blob = sink.lines.join("");
    assert.ok(!blob.includes("987654321"));
    assert.ok(!blob.includes("DEADBEEF"));
    assert.ok(!blob.includes("توقف"));
    assert.equal(r1.user_id_hash, hashId("user", "987654321"));
    assert.equal(r1.user_id_hash.length, 16);
    assert.equal(r2.user_id_hash, "UNKNOWN");
    assert.equal(verifyAuditLines(sink.lines), -1);
  });
  it("detects tampering and deletion", () => {
    const sink = new MemoryAuditSink();
    for (let i = 0; i < 3; i++) {
      recordControlAudit({ surface: "chat", intent: "stop", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R", text: `t${i}` }, sink);
    }
    const tampered = [...sink.lines];
    tampered[1] = tampered[1].replace("REFUSED", "ALLOWED");
    assert.equal(verifyAuditLines(tampered), 1);
    assert.equal(verifyAuditLines([sink.lines[0], sink.lines[2]]), 1);
    assert.equal(verifyAuditLines(["not json"]), 0);
  });
  it("spoofed channel is sanitized and recorded only as a claim", () => {
    const sink = new MemoryAuditSink();
    const r = recordControlAudit({ surface: "chat", intent: "stop", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R", channelClaimed: "local\n{\"decision\":\"ALLOWED\"}" }, sink);
    assert.ok(r);
    assert.match(r.channel_claimed, /^[\w.-]+$/);
    assert.equal(sink.lines.length, 1);
    assert.equal(sink.lines[0].split("\n").filter(Boolean).length, 1);
  });
  it("replayed identical update: refused again and audited twice (no dedupe-as-grant)", () => {
    const sink = new MemoryAuditSink();
    for (let i = 0; i < 2; i++) {
      const d = gateChatControl({ intent: "stop", text: "/stop", channelClaimed: "telegram", userId: "1" });
      assert.equal(d.allowed, false);
      recordControlAudit({ surface: "chat", intent: "stop", capability: d.capability, decision: "REFUSED", reason: d.reason, channelClaimed: "telegram", userId: "1", text: "/stop" }, sink);
    }
    assert.equal(sink.lines.length, 2);
    const [a, b] = sink.lines.map((l) => JSON.parse(l));
    assert.equal(a.message_sha256, b.message_sha256);
    assert.notEqual(a.entry_hash, b.entry_hash);
    assert.equal(verifyAuditLines(sink.lines), -1);
  });
  it("sink failure never throws and the gate still refuses", () => {
    const broken: AuditSink = { lastHash: () => { throw new Error("disk"); }, append: () => { throw new Error("disk"); } };
    const d = gateChatControl({ intent: "start", text: "start", channelClaimed: "web" });
    assert.equal(d.allowed, false);
    assert.equal(recordControlAudit({ surface: "chat", intent: "start", capability: d.capability, decision: "REFUSED", reason: d.reason }, broken), null);
  });
  it("FileAuditSink appends (never rewrites) and chains across instances, incl. torn tail", () => {
    const dir = mkdtempSync(join(tmpdir(), "gm04-"));
    try {
      const p = join(dir, "sub", "audit.jsonl");
      recordControlAudit({ surface: "chat", intent: "stop", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R", text: "a" }, new FileAuditSink(p));
      recordControlAudit({ surface: "engine_api", intent: "start", capability: "ENGINE_CONTROL", decision: "ALLOWED", reason: "B" }, new FileAuditSink(p));
      const lines = readFileSync(p, "utf8").split("\n").filter(Boolean);
      assert.equal(lines.length, 2);
      assert.equal(verifyAuditLines(lines), -1);
      writeFileSync(p, readFileSync(p, "utf8") + "{torn", { encoding: "utf8" });
      const r = recordControlAudit({ surface: "chat", intent: "stop", capability: "ENGINE_CONTROL", decision: "REFUSED", reason: "R" }, new FileAuditSink(p));
      assert.ok(r);
      const after = readFileSync(p, "utf8");
      assert.ok(after.startsWith(lines.join("\n")));
      assert.equal(verifyAuditLines(after.split("\n").filter(Boolean)), 2);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
  it("defaultAuditPath honours AHOS_CONTROL_AUDIT_PATH then AHOS_DATA_DIR", () => {
    assert.equal(defaultAuditPath({ AHOS_CONTROL_AUDIT_PATH: "/x/a.jsonl" }), "/x/a.jsonl");
    assert.equal(defaultAuditPath({ AHOS_DATA_DIR: "/d" }), join("/d", "control_audit", "chat_control_audit.jsonl"));
  });
});
