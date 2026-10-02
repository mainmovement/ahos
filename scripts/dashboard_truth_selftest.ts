/**
 * GM-03 dashboard truthfulness (presentation only).
 * Run: npm run test:dashboard-truth
 * Self-test, not independent verification.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  deriveViewTruth,
  evidenceFreshnessLimitMs,
  executionModeStatus,
  freshnessStatus,
  lastCycleStatusHealth,
  MIN_EVIDENCE_FRESHNESS_MS,
  paperPortfolioStatus,
  presentRunning,
  presentStatus,
  VIEW_STALE_AFTER_MS,
} from "../dashboard_truth.ts";

const NOW = Date.parse("2026-10-02T12:00:00Z");
const ago = (ms: number) => new Date(NOW - ms).toISOString();

describe("freshness limits", () => {
  it("never shorter than the 10-minute floor", () => {
    assert.equal(evidenceFreshnessLimitMs(null), MIN_EVIDENCE_FRESHNESS_MS);
    assert.equal(evidenceFreshnessLimitMs(0), MIN_EVIDENCE_FRESHNESS_MS);
    assert.equal(evidenceFreshnessLimitMs(-5), MIN_EVIDENCE_FRESHNESS_MS);
    assert.equal(evidenceFreshnessLimitMs(Number.NaN), MIN_EVIDENCE_FRESHNESS_MS);
  });
  it("scales with a long engine interval", () => {
    assert.equal(evidenceFreshnessLimitMs(600), 600 * 1000 * 3);
  });
});

describe("freshnessStatus", () => {
  const LIMIT = 10 * 60_000;
  it("recent evidence is OK", () => assert.equal(freshnessStatus(ago(60_000), NOW, LIMIT), "OK"));
  it("old evidence is STALE, not OK", () => assert.equal(freshnessStatus(ago(LIMIT + 1), NOW, LIMIT), "STALE"));
  it("boundary is inclusive", () => assert.equal(freshnessStatus(ago(LIMIT), NOW, LIMIT), "OK"));
  it("missing timestamp is UNKNOWN", () => {
    assert.equal(freshnessStatus(null, NOW, LIMIT), "UNKNOWN");
    assert.equal(freshnessStatus(undefined, NOW, LIMIT), "UNKNOWN");
    assert.equal(freshnessStatus("", NOW, LIMIT), "UNKNOWN");
  });
  it("garbage timestamp is UNKNOWN", () => assert.equal(freshnessStatus("not-a-date", NOW, LIMIT), "UNKNOWN"));
  it("future timestamp beyond skew is UNKNOWN", () =>
    assert.equal(freshnessStatus(new Date(NOW + 5 * 60_000), NOW, LIMIT), "UNKNOWN"));
  it("accepts Date objects", () => assert.equal(freshnessStatus(new Date(NOW - 1000), NOW, LIMIT), "OK"));
});

describe("policy dims read persisted state, not literals", () => {
  it("PAPER_ONLY is OK", () => assert.equal(executionModeStatus("PAPER_ONLY"), "OK"));
  it("any other mode is a VIOLATION", () => {
    assert.equal(executionModeStatus("LIVE"), "VIOLATION");
    assert.equal(executionModeStatus("paper_only"), "VIOLATION");
  });
  it("missing mode is UNKNOWN", () => {
    assert.equal(executionModeStatus(null), "UNKNOWN");
    assert.equal(executionModeStatus("   "), "UNKNOWN");
  });
  it("paper portfolio needs a readable ledger AND PAPER_ONLY", () => {
    assert.equal(paperPortfolioStatus("PAPER_ONLY", true), "OK");
    assert.equal(paperPortfolioStatus("PAPER_ONLY", false), "UNKNOWN");
    assert.equal(paperPortfolioStatus("LIVE", true), "VIOLATION");
  });
});

describe("lastCycleStatusHealth", () => {
  const LIMIT = 10 * 60_000;
  it("SUCCESS + recent is OK", () => assert.equal(lastCycleStatusHealth("SUCCESS", ago(1000), NOW, LIMIT), "OK"));
  it("SUCCESS but old is STALE", () => assert.equal(lastCycleStatusHealth("SUCCESS", ago(LIMIT * 2), NOW, LIMIT), "STALE"));
  it("SUCCESS without timestamp is STALE (not OK)", () =>
    assert.equal(lastCycleStatusHealth("SUCCESS", null, NOW, LIMIT), "STALE"));
  it("non-SUCCESS is UNKNOWN", () => assert.equal(lastCycleStatusHealth("CODE_FAILURE", ago(1), NOW, LIMIT), "UNKNOWN"));
});

describe("view truth (browser-held snapshot)", () => {
  it("fresh snapshot, no error -> not stale", () => {
    const v = deriveViewTruth({ generatedAt: ago(5_000), lastRefreshError: null, nowMs: NOW });
    assert.equal(v.stale, false);
    assert.equal(v.reason, "OK");
  });
  it("refresh failed -> stale even if snapshot is recent", () => {
    const v = deriveViewTruth({ generatedAt: ago(5_000), lastRefreshError: "Failed to fetch", nowMs: NOW });
    assert.equal(v.stale, true);
    assert.equal(v.reason, "REFRESH_FAILED");
  });
  it("old snapshot -> stale without an error", () => {
    const v = deriveViewTruth({ generatedAt: ago(VIEW_STALE_AFTER_MS + 1), lastRefreshError: null, nowMs: NOW });
    assert.equal(v.stale, true);
    assert.equal(v.reason, "SNAPSHOT_TOO_OLD");
  });
  it("no snapshot -> stale", () => {
    assert.equal(deriveViewTruth({ generatedAt: null, lastRefreshError: null, nowMs: NOW }).reason, "NO_SNAPSHOT");
    assert.equal(deriveViewTruth({ generatedAt: "garbage", lastRefreshError: null, nowMs: NOW }).stale, true);
  });
});

describe("presentation never keeps green when stale", () => {
  for (const green of ["OK", "SUCCESS", "PASS", "HIGH", "AVAILABLE"]) {
    it(`${green} -> STALE when stale`, () => assert.equal(presentStatus(green, true), "STALE"));
    it(`${green} unchanged when fresh`, () => assert.equal(presentStatus(green, false), green));
  }
  it("non-green statuses pass through (no upgrade, no downgrade)", () => {
    for (const s of ["UNKNOWN", "DEGRADED", "VIOLATION", "CODE_FAILURE", "INSUFFICIENT_EVIDENCE"]) {
      assert.equal(presentStatus(s, true), s);
    }
  });
  it("cannot mint decisions", () => {
    assert.equal(presentStatus("UNKNOWN", false), "UNKNOWN");
    assert.notEqual(presentStatus("STALE", false), "OK");
  });
  it("run pill only claims RUNNING from a fresh view", () => {
    assert.equal(presentRunning(true, false), "RUNNING");
    assert.equal(presentRunning(true, true), "UNKNOWN");
    assert.equal(presentRunning(false, true), "UNKNOWN");
    assert.equal(presentRunning(false, false), "STOPPED");
  });
});
