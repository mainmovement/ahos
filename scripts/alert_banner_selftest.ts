/**
 * Web opportunity banner must re-check live canonical BUY + overlay PASS.
 * Run: npm run test:alert-banner
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { evaluateWebAlertBanner, WEB_ALERT_HOT_WINDOW_SEC } from "../alert_banner.ts";
import type { CanonicalReadModel } from "../canonical_read_model.ts";

const NOW = 1_800_000_000;

function buyModel(over: Partial<CanonicalReadModel["decisions"][0]> = {}): CanonicalReadModel {
  return {
    version: "canonical-decision-read-model-v1",
    status: "AVAILABLE",
    reason: null,
    generated_ts: NOW,
    authority_version: "test",
    decision_count: 1,
    decisions: [
      {
        token_key: "solana:demo111",
        chain: "solana",
        address: "Demo111",
        alerts_allowed: true,
        paper_allowed: true,
        is_positive: true,
        outcome: "BUY",
        security_state: "PASS",
        identity_state: "VERIFIED",
        ...over,
      },
    ],
    stale: false,
    no_invented_evidence: true,
  };
}

function state(over: Record<string, unknown> = {}) {
  return {
    last_alert_at: NOW - 10,
    last_token: "solana:demo111",
    sent: { "solana:demo111": NOW - 10 },
    last_payload: {
      tokenKey: "solana:demo111",
      symbol: "DEMO",
      chain: "solana",
      address: "Demo111",
      decision: "BUY",
      canonicalSecurityState: "PASS",
    },
    ...over,
  };
}

describe("evaluateWebAlertBanner", () => {
  it("activates only for live canonical BUY + overlay PASS inside the hot window", () => {
    const banner = evaluateWebAlertBanner(state(), buyModel(), NOW);
    assert.equal(banner.active, true);
    assert.equal(banner.reason, "CANONICAL_BUY_PASS");
    assert.equal(banner.payload?.symbol, "DEMO");
    assert.match(banner.disclaimerFa, /PAPER ONLY/);
  });

  it("does not activate on missing state", () => {
    const banner = evaluateWebAlertBanner({}, buyModel(), NOW);
    assert.equal(banner.active, false);
    assert.equal(banner.reason, "NO_ALERT_STATE");
  });

  it("does not activate after the hot window", () => {
    const banner = evaluateWebAlertBanner(
      state({ last_alert_at: NOW - (WEB_ALERT_HOT_WINDOW_SEC + 1) }),
      buyModel(),
      NOW,
    );
    assert.equal(banner.active, false);
    assert.equal(banner.reason, "EXPIRED");
  });

  it("does not activate when the read model is UNAVAILABLE or STALE", () => {
    const missing = evaluateWebAlertBanner(state(), {
      ...buyModel(),
      status: "UNAVAILABLE",
      decisions: [],
      decision_count: 0,
    }, NOW);
    assert.equal(missing.active, false);
    assert.equal(missing.reason, "MODEL_UNAVAILABLE");
    const stale = evaluateWebAlertBanner(state(), { ...buyModel(), status: "STALE" }, NOW);
    assert.equal(stale.active, false);
    assert.equal(stale.reason, "MODEL_STALE");
  });

  it("does not activate for WATCH or when alerts_allowed is false", () => {
    const watch = evaluateWebAlertBanner(
      state(),
      buyModel({ outcome: "WATCH", alerts_allowed: false, is_positive: false }),
      NOW,
    );
    assert.equal(watch.active, false);
    const storedWatch = evaluateWebAlertBanner(
      state({
        last_payload: {
          tokenKey: "solana:demo111",
          symbol: "DEMO",
          chain: "solana",
          address: "Demo111",
          decision: "WATCH",
          canonicalSecurityState: "PASS",
        },
      }),
      buyModel(),
      NOW,
    );
    assert.equal(storedWatch.active, false);
    assert.equal(storedWatch.reason, "STORED_DECISION_NOT_BUY");
  });

  it("stored WATCH text cannot keep the banner hot without live BUY", () => {
    const banner = evaluateWebAlertBanner(
      state({
        last_payload: {
          tokenKey: "solana:demo111",
          symbol: "DEMO",
          chain: "solana",
          address: "Demo111",
          decision: "WATCH",
          canonicalSecurityState: "PASS",
        },
      }),
      buyModel({ outcome: "WATCH", alerts_allowed: false, is_positive: false }),
      NOW,
    );
    assert.equal(banner.active, false);
  });

  it("does not activate when overlay is not PASS", () => {
    for (const sec of ["INCOMPLETE", "REJECT", "STALE", "UNKNOWN", null]) {
      const banner = evaluateWebAlertBanner(
        state(),
        buyModel({ security_state: sec as string | null, alerts_allowed: true, outcome: "BUY" }),
        NOW,
      );
      assert.equal(banner.active, false, String(sec));
    }
  });

  it("does not activate for a different unmatched address", () => {
    const banner = evaluateWebAlertBanner(
      state({
        last_payload: {
          tokenKey: "solana:other",
          symbol: "OTH",
          chain: "solana",
          address: "Other111",
          decision: "BUY",
          canonicalSecurityState: "PASS",
        },
      }),
      buyModel(),
      NOW,
    );
    assert.equal(banner.active, false);
    assert.equal(banner.reason, "ALERTS_NOT_ALLOWED");
  });
});
