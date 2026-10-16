// Hero orb truth rules (no GPU, no window). Run: npm run test:orb
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { gateMath, selectMarkers, HIGHLIGHT_LIMIT } from "../src/components/orb/cobe/lib/style.ts";
import { demoGateCounts } from "../src/components/orb/orbDemo.ts";

test("an empty gate is UNKNOWN, never 0%", () => {
  const m = gateMath({ absorbed: 0, dissipated: 0 });
  assert.equal(m.known, false);
  assert.equal(m.absorbedShare, null);
  assert.equal(m.strictness, null);
});

test("DEMO gate counts: breach is dissipation-dominant, calm is absorption-dominant, both labelled DEMO", () => {
  const calm = demoGateCounts("calm");
  const breach = demoGateCounts("breach");
  assert.equal(calm.freshness, "DEMO");
  assert.equal(breach.freshness, "DEMO");
  assert.ok((calm.absorbed ?? 0) > (calm.dissipated ?? 0));
  assert.ok((breach.dissipated ?? 0) > (breach.absorbed ?? 0));
});

test("never more than HIGHLIGHT_LIMIT highlighted markers", () => {
  const markets = Array.from({ length: 20 }, (_, i) => ({
    id: `m${i}`,
    nameFa: "x",
    nameEn: "x",
    lat: 0,
    lng: i,
    freshness: "DEMO" as const,
    asOf: null,
    needsAttention: true,
  }));
  assert.ok(selectMarkers(markets, true).highlighted.length <= HIGHLIGHT_LIMIT);
  assert.ok(selectMarkers(markets, false).highlighted.length <= HIGHLIGHT_LIMIT);
});

test("/arena renders a single globe: EarthPanel is gone, PAPER ONLY pill and truth chips are in the orb", () => {
  const dash = readFileSync(new URL("../src/components/dashboard/CommandDashboard.tsx", import.meta.url), "utf8");
  assert.ok(!dash.includes("EarthPanel"));
  const orb = readFileSync(new URL("../src/components/orb/PulseOrb.tsx", import.meta.url), "utf8");
  assert.ok(orb.includes("PAPER ONLY"));
  assert.ok(orb.includes("orb-truth-data") && orb.includes("orb-truth-gate"));
  assert.ok(!/live.*green|green/i.test(orb));
});