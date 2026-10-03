/**
 * Mission 9.6 (MN-4): the Gemini egress approval gate.
 *
 * No network, no Python, no key. Exercises gemini_egress_config.ts against the
 * committed record plus synthetic ones written to the OS temp dir. Run:
 *   npm run test:gemini-egress
 * Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeFileSync, unlinkSync } from "node:fs";
import { describe, it, afterEach } from "node:test";
import {
  egressApproved,
  egressRecordError,
  readEgressRecord,
  resetEgressRecordCache,
  type EgressRecord,
} from "../gemini_egress_config.ts";

/** The committed record lives at <root>/config/gemini_egress.json; the default
 * resolver finds it from the repo root (the process cwd under npm). */
const REAL = { AHOS_GEMINI_EGRESS_CONFIG: "" };

function tmpRecord(body: string): string {
  const p = join(tmpdir(), `ahos_egress_${process.pid}_${Math.random().toString(36).slice(2)}.json`);
  writeFileSync(p, body, "utf8");
  return p;
}

const tmpPaths: string[] = [];

afterEach(() => {
  resetEgressRecordCache();
  while (tmpPaths.length) {
    const p = tmpPaths.pop() as string;
    try {
      unlinkSync(p);
    } catch {
      /* already gone */
    }
  }
});

describe("MN-4 egress gate: committed approval record", () => {
  it("approves both channels when the record is present and untampered", () => {
    const rec = readEgressRecord(REAL);
    assert.ok(rec, "the committed config/gemini_egress.json must parse");
    assert.equal(rec?.approved, true);
    assert.equal(rec?.revokedAt, null);
    assert.deepEqual(rec?.scope.sort(), ["chat_agent", "phraser"]);
    assert.ok(egressApproved("phraser", REAL));
    assert.ok(egressApproved("chat_agent", REAL));
    assert.equal(egressRecordError(), null);
  });

  it("holds no secret of any kind", () => {
    const rec = readEgressRecord(REAL);
    assert.ok(rec);
    const blob = JSON.stringify(rec);
    // The note legitimately says "holds no secret", so scan for key-shaped
    // material rather than the word "secret".
    for (const banned of [/AIza[0-9A-Za-z_-]{20,}/, /\bsk-[A-Za-z0-9]{16,}/, /Bearer\s+[A-Za-z0-9._-]{8,}/i, /-----BEGIN[A-Z ]*KEY-----/, /[0-9A-Fa-f]{40,}/]) {
      assert.ok(!banned.test(blob), `record must not contain key material matching ${banned.source}`);
    }
    assert.ok(JSON.stringify(rec).length < 2000, "the record must stay small enough to audit by hand");
  });
});

describe("MN-4 egress gate: fail closed", () => {
  it("disables egress when the record is missing", () => {
    const src = { AHOS_GEMINI_EGRESS_CONFIG: join(tmpdir(), "ahos_definitely_missing_record.json") };
    assert.equal(egressApproved("phraser", src), false);
    assert.equal(egressApproved("chat_agent", src), false);
    assert.equal(egressRecordError(), "EGRESS_RECORD_MISSING");
  });

  it("disables egress when the record is malformed", () => {
    tmpPaths.push(tmpRecord("{ not json "));
    const src = { AHOS_GEMINI_EGRESS_CONFIG: tmpPaths[tmpPaths.length - 1] };
    assert.equal(egressApproved("phraser", src), false);
    assert.match(egressRecordError() ?? "", /^EGRESS_RECORD_INVALID/);
  });

  it("disables egress when approved is false", () => {
    tmpPaths.push(tmpRecord(JSON.stringify({ ...readEgressRecord(REAL), approved: false } as EgressRecord)));
    const src = { AHOS_GEMINI_EGRESS_CONFIG: tmpPaths[tmpPaths.length - 1] };
    assert.equal(egressApproved("phraser", src), false);
  });

  it("disables egress when revokedAt is set", () => {
    tmpPaths.push(tmpRecord(JSON.stringify({ ...readEgressRecord(REAL), revokedAt: "2026-10-03T01:00:00+03:30" } as EgressRecord)));
    const src = { AHOS_GEMINI_EGRESS_CONFIG: tmpPaths[tmpPaths.length - 1] };
    assert.equal(egressApproved("chat_agent", src), false);
  });

  it("disables egress when the channel is not in scope", () => {
    tmpPaths.push(tmpRecord(JSON.stringify({ ...readEgressRecord(REAL), scope: ["phraser"] } as EgressRecord)));
    const src = { AHOS_GEMINI_EGRESS_CONFIG: tmpPaths[tmpPaths.length - 1] };
    assert.ok(egressApproved("phraser", src));
    assert.equal(egressApproved("chat_agent", src), false);
  });

  it("rejects a record missing required fields", () => {
    tmpPaths.push(tmpRecord(JSON.stringify({ approved: true, scope: ["phraser"], recipients: [], revokedAt: null })));
    const src = { AHOS_GEMINI_EGRESS_CONFIG: tmpPaths[tmpPaths.length - 1] };
    assert.equal(egressApproved("phraser", src), false);
    assert.match(egressRecordError() ?? "", /EGRESS_RECORD_INVALID/);
  });
});

describe("MN-4 egress gate: kill switches", () => {
  it("AHOS_GEMINI_EGRESS=off disables every channel", () => {
    assert.equal(egressApproved("phraser", { ...REAL, AHOS_GEMINI_EGRESS: "off" }), false);
    assert.equal(egressApproved("chat_agent", { ...REAL, AHOS_GEMINI_EGRESS: "0" }), false);
  });

  it("AHOS_PHRASER=off disables only the phraser", () => {
    assert.equal(egressApproved("phraser", { ...REAL, AHOS_PHRASER: "off" }), false);
    assert.ok(egressApproved("chat_agent", { ...REAL, AHOS_PHRASER: "off" }));
  });

  it("AHOS_CHAT_AGENT=off disables only the chat agent", () => {
    assert.equal(egressApproved("chat_agent", { ...REAL, AHOS_CHAT_AGENT: "off" }), false);
    assert.ok(egressApproved("phraser", { ...REAL, AHOS_CHAT_AGENT: "off" }));
  });
});

describe("MN-4 egress gate: default singletons honour the record", () => {
  it("getDefaultPhraser is null without approval and a GeminiPhraser with it", async () => {
    const { getDefaultPhraser, resetDefaultPhraserForTests } = await import("../gemini_phraser.ts");
    resetDefaultPhraserForTests();
    assert.equal(getDefaultPhraser({ AHOS_GEMINI_EGRESS: "off" }), null);
    resetDefaultPhraserForTests();
    assert.equal(getDefaultPhraser({ AHOS_PHRASER: "off" }), null);
    resetDefaultPhraserForTests();
    // The committed record approves the phraser, so a real instance is built.
    assert.ok(getDefaultPhraser(REAL) !== null);
    resetDefaultPhraserForTests();
  });

  it("getDefaultChatAgent is null when egress is not approved", async () => {
    const { getDefaultChatAgent, resetDefaultChatAgentForTests } = await import("../chat_agent.ts");
    resetDefaultChatAgentForTests();
    assert.equal(getDefaultChatAgent({ AHOS_CHAT_AGENT: "off" }), null);
    resetDefaultChatAgentForTests();
    assert.equal(getDefaultChatAgent({ AHOS_GEMINI_EGRESS: "off" }), null);
    resetDefaultChatAgentForTests();
    assert.ok(getDefaultChatAgent(REAL) !== null);
    resetDefaultChatAgentForTests();
  });
});
