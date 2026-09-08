import assert from "node:assert/strict";
import test from "node:test";
import {
  overlayOpportunity,
  paperAllowedFromCanonical,
  parseCanonicalReadModel,
  presentCanonicalDecisions,
  toBackendDecision,
  unavailableModel,
} from "../canonical_read_model.ts";

const NOW = 1_800_000_000;

function availableBuy() {
  return parseCanonicalReadModel(
    {
      version: "canonical-decision-read-model-v1",
      status: "AVAILABLE",
      generated_ts: NOW,
      decisions: [
        {
          token_key: "solana:so11111111111111111111111111111111111111112",
          chain: "solana",
          address: "So11111111111111111111111111111111111111112",
          outcome: "BUY",
          advisor_action: "ENTER",
          identity_state: "VERIFIED",
          security_state: "PASS",
          is_positive: true,
          paper_allowed: true,
          alerts_allowed: true,
          confidence_level: "HIGH",
          opportunity_score: 88,
        },
      ],
    },
    NOW,
  );
}

test("missing model is unavailable and cannot mint WATCH", () => {
  const model = unavailableModel("missing_read_model");
  const over = overlayOpportunity(
    { chain: "solana", address: "So11111111111111111111111111111111111111112", decision: "WATCH", confidence: "HIGH" },
    model,
  );
  assert.equal(over.decision, "UNAVAILABLE");
  assert.equal(over.paperAllowed, false);
  assert.equal(toBackendDecision(null, "UNAVAILABLE"), null);
});

test("python BUY is presented without TS inventing it", () => {
  const model = availableBuy();
  const over = overlayOpportunity(
    { chain: "solana", address: "So11111111111111111111111111111111111111112", decision: "WATCH", confidence: "LOW" },
    model,
  );
  assert.equal(over.decision, "BUY");
  assert.equal(over.canonicalOutcome, "BUY");
  assert.equal(over.paperAllowed, true);
  assert.equal(over.confidence, "HIGH");
  const backend = toBackendDecision(model.decisions[0], model.status);
  assert.equal(backend?.outcome, "BUY");
});

test("MONITOR_ONLY and REJECT stay non-positive", () => {
  const model = parseCanonicalReadModel(
    {
      status: "AVAILABLE",
      generated_ts: NOW,
      decisions: [
        {
          token_key: "solana:aaa",
          chain: "solana",
          address: "aaa",
          outcome: "MONITOR_ONLY",
          paper_allowed: false,
          is_positive: false,
        },
        {
          token_key: "solana:bbb",
          chain: "solana",
          address: "bbb",
          outcome: "REJECT",
          paper_allowed: false,
          is_positive: false,
        },
      ],
    },
    NOW,
  );
  assert.equal(overlayOpportunity({ chain: "solana", address: "aaa", decision: "WATCH" }, model).decision, "MONITOR_ONLY");
  assert.equal(overlayOpportunity({ chain: "solana", address: "bbb", decision: "WATCH" }, model).decision, "REJECT");
  assert.equal(paperAllowedFromCanonical(model, "solana", "aaa"), false);
});

test("stale/unavailable presentation strips positives", () => {
  const stale = parseCanonicalReadModel(
    {
      status: "AVAILABLE",
      generated_ts: NOW - 48 * 3600,
      decisions: [
        {
          token_key: "solana:so11111111111111111111111111111111111111112",
          chain: "solana",
          address: "So11111111111111111111111111111111111111112",
          outcome: "BUY",
          paper_allowed: true,
          is_positive: true,
        },
      ],
    },
    NOW,
  );
  const views = presentCanonicalDecisions(stale);
  assert.equal(stale.status, "STALE");
  assert.equal(views[0].outcome, "STALE");
  assert.equal(views[0].paperAllowed, false);
  assert.equal(views[0].isPositive, false);
  const over = overlayOpportunity(
    { chain: "solana", address: "So11111111111111111111111111111111111111112", decision: "BUY" },
    stale,
  );
  assert.equal(over.decision, "STALE");
  assert.equal(over.paperAllowed, false);
  assert.equal(toBackendDecision(stale.decisions[0], stale.status), null);
});

test("presentCanonicalDecisions shows python BUY only when available", () => {
  const views = presentCanonicalDecisions(availableBuy());
  assert.equal(views[0].outcome, "BUY");
  assert.equal(views[0].isPositive, true);
  assert.equal(views[0].paperAllowed, true);
});

test("presentCanonicalDecisions does not invent BUY from empty model", () => {
  const views = presentCanonicalDecisions(unavailableModel("missing_read_model"));
  assert.deepEqual(views, []);
});

test("unmatched token is UNAVAILABLE even if TS said WATCH", () => {
  const model = availableBuy();
  const over = overlayOpportunity(
    { chain: "solana", address: "OtherToken1111111111111111111111111111111", decision: "WATCH" },
    model,
  );
  assert.equal(over.decision, "UNAVAILABLE");
  assert.equal(over.paperAllowed, false);
});

test("TS WATCH cannot alert unless python alerts_allowed", async () => {
  const { shouldAlertOpportunity } = await import("../alerts.ts");
  const opp = {
    decision: "WATCH",
    rankScore: 0.9,
    confidence: "HIGH",
    securityStatus: "PASS",
    token: {
      tokenKey: "solana:so11111111111111111111111111111111111111112",
      chain: "solana",
      address: "So11111111111111111111111111111111111111112",
      symbol: "SOL",
      liquidityUsd: 100_000,
      paidPromotion: false,
    },
  };
  const state = { sent: {} };
  assert.equal(shouldAlertOpportunity(opp as never, state, unavailableModel("missing")), false);
  const watchOnly = parseCanonicalReadModel(
    {
      status: "AVAILABLE",
      generated_ts: NOW,
      decisions: [
        {
          token_key: "solana:so11111111111111111111111111111111111111112",
          chain: "solana",
          address: "So11111111111111111111111111111111111111112",
          outcome: "WATCH",
          alerts_allowed: false,
          is_positive: false,
        },
      ],
    },
    NOW,
  );
  assert.equal(shouldAlertOpportunity(opp as never, state, watchOnly), false);
  assert.equal(shouldAlertOpportunity(opp as never, state, availableBuy()), true);
});
