/**
 * Mission 9.6 (MJ-12): DB-free behavioural harness for `handleChat`.
 *
 * The two independent reviews (REDTEAM-19, Agent-16 QA) both flagged that no
 * test drove the real gate path: the unit tests used a fake runner, fake deps
 * and an audit sink returning null, so the refusal/propose/confirm wiring in
 * chat.ts itself was never exercised. This harness drives `handleChat` end to
 * end with every database and network dependency removed:
 *
 *   - snapshot: `failClosedCommandSnapshot` over an empty read model (no DB);
 *     opportunities are injected only where a test needs a token.
 *   - execution: `ActionDeps` record calls into an in-memory log instead of the
 *     engine — nothing reaches the DB, the paper store or an exchange.
 *   - chat agent + phraser: disabled via env, so no Gemini spawn or network.
 *   - audit + dev-mission queue: temp files via AHOS_CONTROL_AUDIT_PATH /
 *     AHOS_DEV_MISSIONS_PATH, and the chain is verified at the end.
 *
 * Run: npm run test:chat-handlechat   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import { handleChat, setChatTestDeps, type ChatResponse } from "../chat.ts";
import { failClosedCommandSnapshot } from "../snapshot.ts";
import { loadCanonicalReadModel } from "../canonical_read_model.ts";
import { PendingActionStore, type ActionDeps, type Identity } from "../chat_actions.ts";
import { verifyAuditLines } from "../chat_control_gate.ts";

type Snap = Awaited<ReturnType<typeof failClosedCommandSnapshot>>;

const TMP = mkdtempSync(join(tmpdir(), "ahos-handlechat-"));
const AUDIT_PATH = join(TMP, "audit.jsonl");
const MISSIONS_PATH = join(TMP, "dev_missions.jsonl");
process.env.AHOS_CONTROL_AUDIT_PATH = AUDIT_PATH;
process.env.AHOS_DEV_MISSIONS_PATH = MISSIONS_PATH;
// MN-1: a stable test pepper so the self-test never creates ./data/.id_pepper
process.env.AHOS_ID_PEPPER = "selftest-pepper-handlechat";
// No network: the conversational agent and the Gemini phraser are both opt-out.
process.env.AHOS_CHAT_AGENT = "off";
process.env.AHOS_PHRASER = "off";
// Owner identity is decided by isOwner against these admin ids only (MJ-6:
// 222 is on the reader allowlist and must NOT be an owner).
process.env.TELEGRAM_ADMIN_USER_IDS = "111";
process.env.TELEGRAM_ALLOWED_CHAT_IDS = "222";

const OWNER: Identity = { channel: "telegram", userId: "111", proven: true };
const READER: Identity = { channel: "telegram", userId: "222", proven: true };
const STRANGER: Identity = { channel: "telegram", userId: "999", proven: true };
const DASH: Identity = { channel: "dashboard", userId: "sess-a", proven: true };
const UNPROVEN_WEB: Identity = { channel: "web", userId: null, proven: false };
const UNPROVEN_TG_ADMIN: Identity = { channel: "telegram", userId: "111", proven: false };

const STOP_TEXT = "موتور رو خاموش کن";

/** Single controllable clock for expiry tests (PendingActionStore reads it). */
let clock = 0;

async function fakeSnap(withOpp = false): Promise<Snap> {
  const model = await loadCanonicalReadModel(0);
  const snap = failClosedCommandSnapshot(new Error("harness: no database"), model);
  if (withOpp) {
    return {
      ...snap,
      opportunities: [
        { tokenKey: "k1", symbol: "PEPE", chain: "solana", name: "Pepe" },
      ] as Snap["opportunities"],
    };
  }
  return snap;
}

type Harness = {
  executed: string[];
  store: PendingActionStore;
  run: (text: string, id: Identity) => Promise<ChatResponse>;
};

/** A fresh harness: fresh pending store (controllable clock), recorded
 * executions. `run` re-installs this harness's seam on every call so two
 * harnesses can never see each other's store or deps. */
function harness(withOpp = false): Harness {
  const executed: string[] = [];
  const store = new PendingActionStore(() => clock);
  const deps: ActionDeps = {
    startEngine: () => {
      executed.push("start");
      return Promise.resolve();
    },
    stopEngine: () => {
      executed.push("stop");
      return Promise.resolve();
    },
    addWatch: () => {
      executed.push("watch");
      return Promise.resolve();
    },
    paperBuy: (p) => {
      executed.push(`paper:${p.symbol}:${p.quantity ?? "null"}`);
      return Promise.resolve({ ok: true, messageFa: "ثبت شد — فقط کاغذی." });
    },
    recordDevMission: () => {
      executed.push("mission");
      return Promise.resolve({ ok: true, messageFa: "ثبت شد." });
    },
  };
  const install = () =>
    setChatTestDeps({ snapshot: () => fakeSnap(withOpp), actionDeps: deps, store });
  install();
  return {
    executed,
    store,
    run: (text, id) => {
      install();
      return handleChat(text, { channel: id.channel, userId: id.userId, proven: id.proven });
    },
  };
}

/** Every audit line the harness wrote, across all tests (append-only file). */
function auditEntries(): Array<{ decision: string; reason: string }> {
  try {
    const lines = readFileSync(AUDIT_PATH, "utf8").split("\n").filter((l) => l.trim());
    return lines.map((l) => JSON.parse(l) as { decision: string; reason: string });
  } catch {
    return [];
  }
}

function auditDecisions(): string[] {
  return auditEntries().map((e) => e.decision);
}

function auditReasons(): string[] {
  return auditEntries().map((e) => e.reason);
}

describe("MJ-12 handleChat behavioural harness", () => {
  it("a non-owner control command is refused and never proposed", async () => {
    const h = harness();
    const r = await h.run(STOP_TEXT, STRANGER);
    assert.equal(r.intent, "stop");
    assert.match(r.reply, /هیچ تغییری اعمال نشد/);
    assert.equal(r.pendingAction ?? null, null);
    assert.deepEqual(h.executed, []);
    assert.ok(auditDecisions().includes("REFUSED"));
  });

  it("a reader-allowlist id is not the owner (MJ-6)", async () => {
    const h = harness();
    const r = await h.run(STOP_TEXT, READER);
    assert.equal(r.pendingAction ?? null, null);
    assert.deepEqual(h.executed, []);
  });

  it("an unproven caller claiming web, or an admin id without proof, is refused (BL-3)", async () => {
    const a = harness();
    const ra = await a.run(STOP_TEXT, UNPROVEN_WEB);
    assert.equal(ra.pendingAction ?? null, null);
    const b = harness();
    const rb = await b.run(STOP_TEXT, UNPROVEN_TG_ADMIN);
    assert.equal(rb.pendingAction ?? null, null);
    assert.deepEqual([...a.executed, ...b.executed], []);
  });

  it("a caller that sends no channel at all is refused (no web default)", async () => {
    const h = harness();
    const r = await h.run(STOP_TEXT, { channel: null, userId: null, proven: false });
    assert.equal(r.pendingAction ?? null, null);
    assert.deepEqual(h.executed, []);
  });

  it("an owner gets a proposal with a code and nothing executes yet", async () => {
    const h = harness();
    const r = await h.run(STOP_TEXT, OWNER);
    assert.equal(r.intent, "proposal");
    assert.ok(r.pendingAction?.code, "a one-time code is returned to the owner");
    assert.match(r.reply, /تأیید|تایید/);
    assert.deepEqual(h.executed, []); // nothing ran: only a proposal exists
    assert.ok(auditDecisions().includes("PROPOSED"));
  });

  it("an owner confirming the code executes through the injected deps once", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    const r = await h.run(`تایید ${code}`, OWNER);
    assert.equal(r.intent, "confirm");
    assert.deepEqual(h.executed, ["stop"]); // single use, executed exactly once
    assert.ok(auditDecisions().includes("CONFIRMED"));
    // A replay of the same code does nothing.
    const r2 = await h.run(`تایید ${code}`, OWNER);
    assert.deepEqual(h.executed, ["stop"]);
    assert.equal(r2.pendingAction ?? null, null);
  });

  it("a wrong code does not execute and is audited", async () => {
    const h = harness();
    await h.run(STOP_TEXT, OWNER);
    const r = await h.run("تایید ZZZZZZ", OWNER);
    assert.equal(r.intent, "confirm");
    assert.deepEqual(h.executed, []);
    assert.ok(auditDecisions().includes("DENIED"), "a wrong code is audited DENIED");
    assert.ok(
      auditReasons().includes("UNKNOWN_OR_FOREIGN_CODE") ||
        auditReasons().includes("RATE_LIMIT_LOCKED_OUT"),
      "the reason is recorded",
    );
  });

  it("five wrong codes lock the identity out", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    for (let i = 0; i < 5; i++) await h.run("تایید ZZZZZZ", OWNER);
    const r = await h.run(`تایید ${code}`, OWNER); // even the real code is refused now
    assert.deepEqual(h.executed, []);
    assert.match(r.reply, /مسدود/);
  });

  it("an expired code does not execute", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    clock = 6 * 60 * 1000; // past the 5-minute TTL
    const r = await h.run(`تایید ${code}`, OWNER);
    assert.deepEqual(h.executed, []);
    assert.match(r.reply, /منقضی/);
    clock = 0;
  });

  it("an owner can cancel a proposal and nothing executes", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    const r = await h.run(`لغو ${code}`, OWNER);
    assert.deepEqual(h.executed, []);
    assert.match(r.reply, /لغو شد/);
    assert.ok(auditDecisions().includes("CANCELLED"));
  });

  it("another session cannot confirm a foreign code (m2)", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    const r = await h.run(`تایید ${code}`, DASH); // different identity key
    assert.deepEqual(h.executed, []);
    assert.equal(r.intent, "confirm");
  });

  it("a non-owner cannot confirm an owner's code", async () => {
    const h = harness();
    const p = await h.run(STOP_TEXT, OWNER);
    const code = p.pendingAction?.code ?? "";
    const r = await h.run(`تایید ${code}`, STRANGER); // same store, foreign identity
    assert.deepEqual(h.executed, []);
    assert.equal(r.intent, "confirm");
  });

  it("an owner paper buy proposes and executes on confirm (PAPER_WRITE path)", async () => {
    const h = harness(true);
    const p = await h.run("خرید کاغذی PEPE", OWNER);
    assert.equal(p.intent, "proposal");
    assert.ok(p.pendingAction?.code);
    const code = p.pendingAction?.code ?? "";
    const r = await h.run(`تایید ${code}`, OWNER);
    assert.deepEqual(h.executed, ["paper:PEPE:null"]); // no quantity asked → null, capped
    assert.equal(r.intent, "confirm");
    assert.ok(auditDecisions().includes("CONFIRMED"));
  });

  it("a non-owner paper buy is refused, not proposed", async () => {
    const h = harness(true);
    const r = await h.run("خرید کاغذی PEPE", STRANGER);
    assert.equal(r.pendingAction ?? null, null);
    assert.deepEqual(h.executed, []);
  });

  it("a control command hidden in a longer message never matches (GM-04)", async () => {
    const h = harness();
    const r = await h.run("stop loss بیت کوین رو کجا بذارم؟", STRANGER);
    assert.notEqual(r.intent, "stop");
    assert.deepEqual(h.executed, []);
  });

  it("each harness instance sees only its own pending store", async () => {
    const a = harness();
    const pa = await a.run(STOP_TEXT, OWNER);
    const codeA = pa.pendingAction?.code ?? "";
    const b = harness(); // fresh store: the first harness's code is unknown here
    const rb = await b.run(`تایید ${codeA}`, OWNER);
    assert.deepEqual(b.executed, []);
    assert.equal(rb.pendingAction ?? null, null);
    // The first harness can still confirm its own action with the same code.
    await a.run(`تایید ${codeA}`, OWNER);
    assert.deepEqual(a.executed, ["stop"]);
  });

  it("the audit chain written by the harness is intact", () => {
    const lines = readFileSync(AUDIT_PATH, "utf8").split("\n").filter((l) => l.trim());
    assert.ok(lines.length > 0, "the harness wrote audit lines");
    assert.equal(verifyAuditLines(lines), -1, "no broken link in the chain");
  });

  it("clearing the seam restores the production snapshot source", () => {
    setChatTestDeps(null);
    // The fallback is the real commandSnapshot (not exercised here — no DB);
    // clearing the seam must not throw and a fresh harness must work afterwards.
    const h = harness();
    assert.ok(h.store instanceof PendingActionStore);
  });
});

// The seam is process-local: never let it leak into another suite.
process.on("exit", () => {
  setChatTestDeps(null);
  try {
    rmSync(TMP, { recursive: true, force: true });
  } catch {
    /* best effort */
  }
});
