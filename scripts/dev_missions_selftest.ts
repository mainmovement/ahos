/**
 * Phase 8: dev-mission queue self-test (hash chain, privacy, cleaning).
 * No network, no DB, no key. Writes only to a temp directory.
 * Run: npm run test:dev-missions   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  DEV_MISSION_SCHEMA,
  DevMissionStore,
  cleanSummaryFa,
  defaultDevMissionsPath,
  faAgo,
  redactMissionSecrets,
  titleFromSummaryFa,
} from "../dev_missions.ts";

const TMP = mkdtempSync(join(tmpdir(), "ahos-dm-"));
// MN-1: a stable test pepper so the self-test never creates ./data/.id_pepper.
// DevMissionStore hashes the confirm code and the user id through idPepper().
process.env.AHOS_ID_PEPPER = "selftest-pepper-dev-missions";
const path = (n: string) => join(TMP, n);
const NOW = new Date("2026-10-02T14:00:00Z");

describe("queue store", () => {
  it("appends one QUEUED mission with a hash-chained record and stable id", () => {
    const s = new DevMissionStore(path("a.jsonl"), { now: () => NOW });
    const r = s.append({ summaryFa: "راه‌اندازی عامل اخبار", channel: "telegram", userId: "111" });
    assert.ok(r);
    assert.equal(r!.schema, DEV_MISSION_SCHEMA);
    assert.equal(r!.seq, 0);
    assert.equal(r!.id, "DM-000001");
    assert.equal(r!.status, "QUEUED");
    assert.equal(r!.kind, "MISSION");
    const r2 = s.append({ summaryFa: "اضافه کردن هشدار طلا", channel: "web", userId: null });
    assert.equal(r2!.id, "DM-000002");
    assert.equal(r2!.seq, 1);
    assert.equal(r2!.prev_hash, r!.entry_hash);
    assert.equal(s.records().length, 2);
    assert.equal(s.verify().ok, true);
  });
  it("empty / whitespace summary is refused; nothing is written", () => {
    const s = new DevMissionStore(path("b.jsonl"));
    assert.equal(s.append({ summaryFa: "   " }), null);
    assert.equal(s.append({ summaryFa: "" }), null);
    assert.equal(s.records().length, 0);
  });
  it("never stores the raw user message: greeting stripped, one line, truncated", () => {
    const s = new DevMissionStore(path("c.jsonl"));
    const long = "سلام، " + "یک قابلیت جدید " .repeat(40);
    const r = s.append({ summaryFa: long, channel: "telegram", userId: "1" });
    assert.ok(r);
    assert.ok(!r!.summaryFa.startsWith("سلام"));
    assert.ok(!r!.summaryFa.includes("\n"));
    assert.ok(r!.summaryFa.length <= 280);
    assert.ok(r!.summaryFa.endsWith("…"));
    const zwnj = s.append({ summaryFa: "دانشگاه‌رو بساز", channel: "web", userId: null });
    assert.ok(!zwnj!.summaryFa.includes("‌"));
  });
  it("title is the first clause, capped", () => {
    assert.equal(titleFromSummaryFa("اضافه کردن هشدار طلا. بعدشم داشبورد"), "اضافه کردن هشدار طلا");
    const long = titleFromSummaryFa("یک قابلیت طولانی " + "x".repeat(80));
    assert.ok(long.length <= 60);
    assert.ok(long.endsWith("…"));
  });
  it("redacts secret-looking substrings before hashing and writing", () => {
    const p = path("d.jsonl");
    const s = new DevMissionStore(p);
    const r = s.append({ summaryFa: `کلید گوگل: AIza${"a".repeat(35)}`, channel: "telegram", userId: "1" });
    assert.ok(r);
    assert.ok(!r!.summaryFa.includes("AIza"));
    assert.match(r!.summaryFa, /REDACTED/);
    const onDisk = readFileSync(p, "utf8");
    assert.ok(!onDisk.includes("AIza"));
  });
  it("stores a hash of the sender id, never the raw id", () => {
    const s = new DevMissionStore(path("e.jsonl"));
    const r = s.append({ summaryFa: "x", channel: "telegram", userId: "9876543210" });
    assert.ok(r);
    assert.ok(!r!.userIdHash.includes("9876543210"));
    assert.ok(r!.userIdHash.length >= 8);
  });
  it("queued() is newest first, with Persian age labels", () => {
    let t = new Date("2026-10-02T14:00:00Z").getTime();
    const s = new DevMissionStore(path("f.jsonl"), { now: () => new Date(t) });
    s.append({ summaryFa: "اول", channel: "web", userId: null });
    t += 45 * 60_000;
    s.append({ summaryFa: "دوم", channel: "web", userId: null });
    const q = s.queued(new Date(t));
    assert.deepEqual(
      q.map((m) => m.titleFa),
      ["دوم", "اول"],
    );
    assert.equal(q[0].statusFa, "در صف");
    assert.equal(q[0].queuedAgoFa, "همین الان");
    assert.match(q[1].queuedAgoFa, /۴۵ دقیقه/);
  });
  it("detects tampering: edited line, deleted first line, reordered line", () => {
    const p = path("g.jsonl");
    const s = new DevMissionStore(p, { now: () => NOW });
    s.append({ summaryFa: "یک", channel: "web", userId: null });
    s.append({ summaryFa: "دو", channel: "web", userId: null });
    assert.equal(s.verify().ok, true);
    const lines = readFileSync(p, "utf8").split("\n").filter((l) => l.trim());
    // edit a field
    writeFileSync(p, lines.map((l, i) => (i === 0 ? l.replace('"یک"', "هک") : l)).join("\n") + "\n", "utf8");
    assert.equal(new DevMissionStore(p).verify().ok, false);
    // delete the FIRST line → prev_hash no longer matches genesis
    writeFileSync(p, lines.slice(1).join("\n") + "\n", "utf8");
    assert.equal(new DevMissionStore(p).records().length, 0);
    // reorder
    writeFileSync(p, lines.slice().reverse().join("\n") + "\n", "utf8");
    assert.equal(new DevMissionStore(p).records().length, 0);
  });
  it("limitation, documented: deleting only the LAST line is invisible to a keyless chain", () => {
    // That is why head_hash must be anchored outside the file (handoff doc, commit).
    const p = path("h.jsonl");
    const s = new DevMissionStore(p, { now: () => NOW });
    s.append({ summaryFa: "یک", channel: "web", userId: null });
    s.append({ summaryFa: "دو", channel: "web", userId: null });
    const lines = readFileSync(p, "utf8").split("\n").filter((l) => l.trim());
    writeFileSync(p, lines.slice(0, 1).join("\n") + "\n", "utf8");
    assert.equal(new DevMissionStore(p).records().length, 1);
    assert.equal(new DevMissionStore(p).verify().ok, true);
  });
  it("append fails closed when the path cannot be created", () => {
    const blocker = join(TMP, "blocker.jsonl");
    writeFileSync(blocker, "not a directory", "utf8");
    const s = new DevMissionStore(join(blocker, "x.jsonl"));
    assert.equal(s.append({ summaryFa: "یک", channel: "web", userId: null }), null);
  });
});

describe("helpers", () => {
  it("path precedence: AHOS_DEV_MISSIONS_PATH > AHOS_DATA_DIR > ./data", () => {
    assert.equal(defaultDevMissionsPath({ AHOS_DEV_MISSIONS_PATH: "/x/y.jsonl" }), "/x/y.jsonl");
    assert.equal(defaultDevMissionsPath({ AHOS_DATA_DIR: "/d" }), join("/d", "dev_missions", "dev_missions.jsonl"));
    assert.ok(defaultDevMissionsPath({}).endsWith(join("data", "dev_missions", "dev_missions.jsonl")));
  });
  it("faAgo covers minute/hour/day and unknown", () => {
    const n = new Date("2026-10-02T14:00:00Z");
    assert.equal(faAgo("2026-10-02T14:00:00Z", n), "همین الان");
    assert.equal(faAgo("2026-10-02T13:30:00Z", n), "۳۰ دقیقه پیش");
    assert.equal(faAgo("2026-10-02T13:00:00Z", n), "۱ ساعت پیش");
    assert.equal(faAgo("2026-10-01T14:00:00Z", n), "۱ روز پیش");
    assert.equal(faAgo("not-a-date", n), "نامشخص");
  });
  it("cleanSummaryFa normalizes Arabic letters and zero-width marks", () => {
    const c = cleanSummaryFa("دانشگاهِيك رو بساز");
    assert.ok(!c.includes("ي"));
    assert.ok(!c.includes("ك"));
  });
  it("redactMissionSecrets covers tokens, keys and bearer strings", () => {
    assert.match(redactMissionSecrets("token 123456789:abcdef" + "g".repeat(24)), /REDACTED/);
    assert.match(redactMissionSecrets("sk-ant-" + "a".repeat(20)), /REDACTED/);
    assert.match(redactMissionSecrets("Authorization: Bearer " + "a".repeat(16)), /REDACTED/);
    assert.equal(redactMissionSecrets("قیمت طلا"), "قیمت طلا");
  });
});
