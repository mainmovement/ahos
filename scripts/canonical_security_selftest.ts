/**
 * Execution tests for canonical security side-effect gates.
 * Run: npm run test:canonical-security
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  escapeTelegramHtml,
  formatTelegramHtml,
  processOpportunityAlerts,
  shouldAlertOpportunity,
  type AlertPayload,
  type AlertState,
} from "../alerts.ts";
import {
  attachCanonicalSecurityStates,
  canonicalSecurityAllowsSideEffect,
  paperOpenDecision,
  parseCanonicalSecurityState,
} from "../canonical_security.ts";
import type { CanonicalReadModel } from "../canonical_read_model.ts";
import type { PairObservation, ScoredOpportunity } from "../types.ts";

const emptyState = (): AlertState => ({ sent: {} });

function buyModel(over: Partial<CanonicalReadModel["decisions"][0]> = {}): CanonicalReadModel {
  return {
    version: "canonical-decision-read-model-v1",
    status: "AVAILABLE",
    reason: null,
    generated_ts: 1_800_000_000,
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
        ...over,
      },
    ],
    stale: false,
    no_invented_evidence: true,
  };
}

function token(over: Partial<PairObservation> = {}): PairObservation {
  return {
    tokenKey: "solana:demo",
    symbol: "DEMO",
    name: "Demo",
    chain: "solana",
    address: "Demo111",
    pairAddress: null,
    dexId: null,
    url: null,
    imageUrl: null,
    priceUsd: 1,
    liquidityUsd: 80_000,
    volume24h: 50_000,
    fdv: null,
    marketCap: null,
    priceChange5m: null,
    priceChange1h: 5,
    priceChange6h: null,
    priceChange24h: 10,
    buys24h: 40,
    sells24h: 20,
    pairCreatedAt: null,
    boostActive: null,
    paidPromotion: false,
    source: "dexscreener",
    labels: [],
    ...over,
  };
}

function opp(over: Partial<ScoredOpportunity> = {}): ScoredOpportunity {
  return {
    token: token(),
    decision: "WATCH",
    rankScore: 0.9,
    confidence: "HIGH",
    securityStatus: "OBSERVED",
    canonicalSecurityState: null,
    evidenceCoverage: 0.8,
    reasonsFa: ["liq"],
    risksFa: [],
    unknownsFa: [],
    invalidationFa: "",
    missingFa: [],
    councilVerdict: "WATCH",
    disagreement: false,
    votes: [],
    security: null,
    ...over,
  };
}

describe("parseCanonicalSecurityState", () => {
  it("accepts only overlay vocabulary", () => {
    assert.equal(parseCanonicalSecurityState("PASS"), "PASS");
    assert.equal(parseCanonicalSecurityState("reject"), "REJECT");
    assert.equal(parseCanonicalSecurityState("INCOMPLETE"), "INCOMPLETE");
    assert.equal(parseCanonicalSecurityState("STALE"), "STALE");
    assert.equal(parseCanonicalSecurityState("UNKNOWN"), null);
    assert.equal(parseCanonicalSecurityState("OBSERVED"), null);
    assert.equal(parseCanonicalSecurityState("HONEYPOT"), null);
    assert.equal(parseCanonicalSecurityState(""), null);
    assert.equal(parseCanonicalSecurityState(null), null);
    assert.equal(parseCanonicalSecurityState(undefined), null);
    assert.equal(parseCanonicalSecurityState(1), null);
    assert.equal(parseCanonicalSecurityState("PASS_WITH_UNKNOWN"), null);
    assert.equal(parseCanonicalSecurityState("SECURITY_VETO"), null);
  });
});

describe("canonicalSecurityAllowsSideEffect", () => {
  it("allows only PASS", () => {
    assert.equal(canonicalSecurityAllowsSideEffect("PASS"), true);
    for (const s of [
      "REJECT",
      "INCOMPLETE",
      "STALE",
      "UNKNOWN",
      "OBSERVED",
      "",
      null,
      undefined,
    ]) {
      assert.equal(canonicalSecurityAllowsSideEffect(s), false, String(s));
    }
  });
});

describe("paperOpenDecision", () => {
  it("denies missing malformed reject incomplete stale unknown", () => {
    assert.equal(paperOpenDecision("PASS").ok, true);
    assert.equal(paperOpenDecision(null).ok, false);
    assert.equal(paperOpenDecision(undefined).ok, false);
    assert.equal(paperOpenDecision("").ok, false);
    assert.equal(paperOpenDecision("OBSERVED").canonicalSecurityState, "MALFORMED");
    assert.equal(paperOpenDecision("INCOMPLETE").ok, false);
    assert.equal(paperOpenDecision("STALE").ok, false);
    assert.equal(paperOpenDecision("REJECT").ok, false);
    assert.equal(paperOpenDecision("UNKNOWN").ok, false);
    assert.equal(paperOpenDecision("PASS_WITH_UNKNOWN").ok, false);
    assert.equal(paperOpenDecision("PASS_WITH_UNKNOWN").canonicalSecurityState, "MALFORMED");
    assert.equal(paperOpenDecision("SECURITY_VETO").ok, false);
  });
});

describe("shouldAlertOpportunity — former bypass", () => {
  const st = emptyState();
  const gate = { nowSec: 1_800_000_000, cooldownSec: 0, scoreFloor: 0.72 };
  const model = buyModel();

  it("BEFORE-behavior: UNKNOWN/OBSERVED/empty used to alert; AFTER: denied", () => {
    assert.equal(
      shouldAlertOpportunity(opp({ securityStatus: "UNKNOWN", canonicalSecurityState: null }), st, model, gate),
      false,
    );
    assert.equal(
      shouldAlertOpportunity(opp({ securityStatus: "OBSERVED", canonicalSecurityState: undefined }), st, model, gate),
      false,
    );
    assert.equal(
      shouldAlertOpportunity(opp({ securityStatus: "", canonicalSecurityState: "" }), st, model, gate),
      false,
    );
  });

  it("canonical PASS + BUY + high opportunity → alert allowed", () => {
    assert.equal(
      shouldAlertOpportunity(opp({ canonicalSecurityState: "PASS" }), st, model, gate),
      true,
    );
  });

  it("canonical PASS without alerts_allowed → no alert", () => {
    assert.equal(
      shouldAlertOpportunity(
        opp({ canonicalSecurityState: "PASS" }),
        st,
        buyModel({ alerts_allowed: false }),
        gate,
      ),
      false,
    );
  });

  it("canonical REJECT/INCOMPLETE/STALE/UNKNOWN + high opportunity → no alert", () => {
    for (const s of ["REJECT", "INCOMPLETE", "STALE", "UNKNOWN"]) {
      assert.equal(
        shouldAlertOpportunity(opp({ canonicalSecurityState: s, rankScore: 0.99 }), st, model, gate),
        false,
        s,
      );
    }
  });

  it("local OBSERVED + canonical INCOMPLETE → no alert", () => {
    assert.equal(
      shouldAlertOpportunity(
        opp({ securityStatus: "OBSERVED", canonicalSecurityState: "INCOMPLETE", rankScore: 0.99 }),
        st,
        model,
        gate,
      ),
      false,
    );
  });

  it("local UNKNOWN + canonical PASS + BUY → overlay PASS remains required (alert allowed)", () => {
    assert.equal(
      shouldAlertOpportunity(
        opp({ securityStatus: "UNKNOWN", canonicalSecurityState: "PASS", rankScore: 0.99 }),
        st,
        model,
        gate,
      ),
      true,
    );
  });
});

describe("processOpportunityAlerts side effects", () => {
  const optsBase = {
    nowSec: 1_800_000_000,
    cooldownSec: 0,
    scoreFloor: 0.5,
    loadState: async () => emptyState(),
    saveState: async () => {},
    loadModel: async () => buyModel(),
  };

  it("Telegram send does not execute for negative canonical states", async () => {
    const sent: string[] = [];
    const transport = { send: async (text: string) => { sent.push(text); return { ok: true, sent: 1 }; } };
    const negatives = [undefined, null, "", "REJECT", "INCOMPLETE", "STALE", "UNKNOWN", "OBSERVED", "HONEYPOT", "nope"];
    for (const s of negatives) {
      const r = await processOpportunityAlerts(
        [opp({ canonicalSecurityState: s as string | null, rankScore: 0.99 })],
        { ...optsBase, transport },
      );
      assert.equal(r.emitted.length, 0, String(s));
      assert.equal(r.telegram.length, 0, String(s));
    }
    assert.equal(sent.length, 0);
  });

  it("positive path executes only for canonical PASS", async () => {
    const sent: string[] = [];
    const transport = { send: async (text: string) => { sent.push(text); return { ok: true, sent: 1 }; } };
    const r = await processOpportunityAlerts(
      [opp({ canonicalSecurityState: "PASS", rankScore: 0.99 })],
      { ...optsBase, transport },
    );
    assert.equal(r.emitted.length, 1);
    assert.equal(r.emitted[0].canonicalSecurityState, "PASS");
    assert.equal(r.telegram.length, 1);
    assert.equal(sent.length, 1);
    assert.match(sent[0], /CRITICAL OPPORTUNITY ALERT/);
  });

  it("Telegram HTML escapes untrusted fields on the send path", async () => {
    const sent: string[] = [];
    const transport = { send: async (text: string) => { sent.push(text); return { ok: true, sent: 1 }; } };
    const r = await processOpportunityAlerts(
      [opp({
        canonicalSecurityState: "PASS",
        rankScore: 0.99,
        token: token({ symbol: "<b>HAX</b>&x" }),
        reasonsFa: ["a < b & c"],
        risksFa: ["x > y"],
        unknownsFa: ["foo & bar"],
      })],
      { ...optsBase, transport },
    );
    assert.equal(r.emitted.length, 1);
    assert.equal(sent.length, 1);
    const html = sent[0];
    assert.match(html, /<b>CRITICAL OPPORTUNITY ALERT/);
    assert.match(html, /&lt;b&gt;HAX&lt;\/b&gt;&amp;x/);
    assert.doesNotMatch(html, /<b>HAX<\/b>/);
    assert.match(html, /a &lt; b &amp; c/);
    assert.match(html, /x &gt; y/);
    assert.match(html, /foo &amp; bar/);
  });
});

describe("escapeTelegramHtml", () => {
  it("escapes &, <, > in that order and is not a no-op", () => {
    assert.equal(escapeTelegramHtml(""), "");
    assert.equal(escapeTelegramHtml("plain"), "plain");
    assert.equal(escapeTelegramHtml("<b>x</b>"), "&lt;b&gt;x&lt;/b&gt;");
    assert.equal(escapeTelegramHtml("a & b"), "a &amp; b");
    assert.equal(escapeTelegramHtml("&<>"), "&amp;&lt;&gt;");
    assert.notEqual(escapeTelegramHtml("<"), "<");
  });

  it("formatTelegramHtml keeps structural tags and escapes payload fields", () => {
    const payload: AlertPayload = {
      tokenKey: "solana:x",
      symbol: "A&B<C>",
      chain: "solana",
      address: "addr<>",
      decision: "BUY",
      rankScore: 0.9,
      confidence: "HIGH",
      securityStatus: "PASS",
      canonicalSecurityState: "PASS",
      liquidityUsd: null,
      volume24h: null,
      priceUsd: null,
      priceChange1h: null,
      reasonsFa: [],
      risksFa: [],
      unknownsFa: [],
      timestamp: "2026-09-09T00:00:00Z",
      disclaimerFa: "n < 1 & n > 0",
    };
    const html = formatTelegramHtml(payload);
    assert.match(html, /<b>A&amp;B&lt;C&gt;<\/b>/);
    assert.match(html, /<code>addr&lt;&gt;<\/code>/);
    assert.match(html, /n &lt; 1 &amp; n &gt; 0/);
  });
});

describe("attachCanonicalSecurityStates", () => {
  it("unavailable query leaves state null (fail closed)", async () => {
    const ranked = [opp({ securityStatus: "OBSERVED" })];
    await attachCanonicalSecurityStates(ranked, async () => { throw new Error("down"); });
    assert.equal(ranked[0].canonicalSecurityState, null);
    assert.equal(canonicalSecurityAllowsSideEffect(ranked[0].canonicalSecurityState), false);
  });

  it("malformed overlay values do not become PASS", async () => {
    const ranked = [opp()];
    await attachCanonicalSecurityStates(ranked, async () => ({ "solana:demo": "OBSERVED" }));
    assert.equal(ranked[0].canonicalSecurityState, null);
  });

  it("Python overlay PASS is attached and used", async () => {
    const ranked = [opp({ securityStatus: "UNKNOWN" })];
    await attachCanonicalSecurityStates(ranked, async () => ({ "solana:demo": "PASS" }));
    assert.equal(ranked[0].canonicalSecurityState, "PASS");
  });

  it("empty overlay map is missing canonical state → no alert / no telegram", async () => {
    const ranked = [opp({ securityStatus: "OBSERVED", rankScore: 0.99 })];
    await attachCanonicalSecurityStates(ranked, async () => ({}));
    assert.equal(ranked[0].canonicalSecurityState, null);
    const sent: string[] = [];
    const r = await processOpportunityAlerts(ranked, {
      nowSec: 1_800_000_000,
      cooldownSec: 0,
      scoreFloor: 0.5,
      loadState: async () => emptyState(),
      saveState: async () => {},
      loadModel: async () => buyModel(),
      transport: { send: async (text: string) => { sent.push(text); return { ok: true, sent: 1 }; } },
    });
    assert.equal(r.emitted.length, 0);
    assert.equal(sent.length, 0);
  });
});

describe("live Python overlay_query adapter", () => {
  it("GoPlus-like TS snapshot cannot PASS; full overlay signals can", async () => {
    const { queryPythonOverlayStates } = await import("../canonical_security.ts");
    const nowSec = 1_800_000_000;
    const incomplete = await queryPythonOverlayStates(
      [{
        tokenKey: "solana:partial",
        signals: {
          is_honeypot: false,
          has_mint_authority: false,
          has_freeze_authority: false,
          cannot_sell_all: false,
        },
        pair_created_ts: nowSec - 30 * 86400,
        retrieved_ts: nowSec,
      }],
      nowSec,
    );
    assert.notEqual(incomplete["solana:partial"], "PASS");
    assert.equal(canonicalSecurityAllowsSideEffect(incomplete["solana:partial"]), false);

    const passing = await queryPythonOverlayStates(
      [{
        tokenKey: "solana:full",
        signals: {
          is_honeypot: false,
          sell_tax_pct: 1,
          buy_tax_pct: 1,
          liquidity_locked_pct: 95,
          has_mint_authority: false,
          has_freeze_authority: false,
          is_contract_verified: true,
          is_ownership_renounced: true,
          top10_holder_concentration_pct: 20,
          deployer_past_rug_count: 0,
          is_blacklisted: false,
          cannot_sell_all: false,
          is_proxy: false,
        },
        pair_created_ts: nowSec - 30 * 86400,
        retrieved_ts: nowSec,
      }],
      nowSec,
    );
    assert.equal(passing["solana:full"], "PASS");
    assert.equal(canonicalSecurityAllowsSideEffect(passing["solana:full"]), true);
  });
});
