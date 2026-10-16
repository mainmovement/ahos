import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { rowDisplay, isDemoSource } from "../src/features/trade-venue/logic/rowStatus.ts";
import { pickHighlights } from "../src/features/trade-venue/logic/highlights.ts";
import {
  ALLOWED_VERBS,
  FORBIDDEN_CONTROL_PATTERNS,
  STATUS_TONE,
  detectViolation,
  findForbiddenControl,
  staleOrUnknown,
  valueText,
} from "../src/features/trade-venue/logic/truth.ts";
import { getVenueBundle } from "../src/mock/trade_venue/index.ts";
import { readVenueSearchParams } from "../src/features/trade-venue/logic/search-params.ts";

const ROOT = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (p.endsWith(".tsx")) out.push(p);
  }
  return out;
}

test("STALE without a timestamp is UNKNOWN; with one it stays STALE", () => {
  assert.equal(staleOrUnknown(null), "UNKNOWN");
  assert.equal(staleOrUnknown("2026-10-16T10:00:00Z"), "STALE");
  assert.equal(rowDisplay({ status: "STALE", updatedAt: null, sourceId: "paper.engine.ledger" }).status, "UNKNOWN");
  assert.equal(rowDisplay({ status: "STALE", updatedAt: "2026-10-16T10:00:00Z", sourceId: "paper.engine.ledger" }).status, "STALE");
});

test("a demo row never displays as LIVE (green) and is marked demo", () => {
  const d = rowDisplay({ status: "LIVE", updatedAt: "2026-10-16T10:00:00Z", sourceId: "feed.gold.demo" });
  assert.equal(d.status, "DEMO");
  assert.equal(d.demo, true);
  assert.notEqual(STATUS_TONE[d.status], "live");
  assert.equal(isDemoSource("some.unknown.source"), true);
  assert.equal(rowDisplay({ status: "LIVE", updatedAt: "x", sourceId: "x", bundleDemo: true }).status, "DEMO");
});

test("every row of every mock bundle: no LIVE-displayed demo row, STALE displays carry a timestamp", () => {
  for (const world of ["REAL_PAPER", "SIMULATION"] as const) {
    for (const forceDemo of [false, true]) {
      const query = readVenueSearchParams({ world, demo: forceDemo ? "1" : undefined });
      const bundle = getVenueBundle(query);
      const snap = world === "SIMULATION" ? bundle.simulation : bundle.realPaper;
      const rows = [
        ...snap.paper.map((r) => ({ s: r.status, t: r.updatedAt, src: r.sourceId })),
        ...snap.fillLog.map((r) => ({ s: r.status, t: r.at, src: r.sourceId })),
      ];
      assert.ok(rows.length > 0);
      for (const r of rows) {
        const d = rowDisplay({ status: r.s, updatedAt: r.t, sourceId: r.src, bundleDemo: snap.demoForced });
        if (d.demo) assert.notEqual(d.status, "LIVE");
        if (d.status === "STALE") assert.ok(r.t, "STALE needs a timestamp");
      }
    }
  }
});

test("highlights: at most 7, attention rows first", () => {
  const snap = getVenueBundle(readVenueSearchParams({})).realPaper;
  const picked = pickHighlights(snap.paper, 50);
  assert.ok(picked.length <= 7);
  assert.ok(pickHighlights(snap.paper, 3).length <= 3);
});

test("missing values never render as 0", () => {
  assert.equal(valueText(null), "—");
  assert.equal(valueText(undefined), "—");
  assert.equal(valueText(Number.NaN), "—");
  assert.equal(valueText(0), "0.00");
});

test("violation: non-paper mode or realTrading lights the bar", () => {
  assert.equal(detectViolation({ executionMode: "PAPER_ONLY", realTrading: false }), null);
  assert.ok(detectViolation({ executionMode: "LIVE", realTrading: false }));
  assert.ok(detectViolation({ executionMode: "PAPER_ONLY", realTrading: true }));
  const q = readVenueSearchParams({ violation: "1" });
  const b = getVenueBundle(q);
  assert.ok(detectViolation({ executionMode: b.realPaper.executionMode, realTrading: b.realPaper.realTrading }));
});

test("forbidden controls: every <button> carries an allowed data-verb; no forbidden wording in sources or copy", () => {
  const files = [
    ...walk(join(ROOT, "src/features/trade-venue")),
    ...walk(join(ROOT, "src/components/truth")),
    join(ROOT, "app/arena/trade-venue/page.tsx"),
  ];
  assert.ok(files.length > 10);
  for (const file of files) {
    const src = readFileSync(file, "utf8");
    for (const m of src.matchAll(/<button\b[^>]*>/g)) {
      const verb = /data-verb="([a-z_]+)"/.exec(m[0])?.[1];
      assert.ok(verb && (ALLOWED_VERBS as readonly string[]).includes(verb), `${file}: ${m[0].slice(0, 80)}`);
    }
    const noComments = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    const hit = findForbiddenControl(noComments);
    assert.equal(hit, null, `${file} matches ${hit}`);
  }
  for (const lang of ["fa", "en"]) {
    const json = readFileSync(join(ROOT, `src/i18n/${lang}.json`), "utf8");
    const tv = JSON.stringify(JSON.parse(json).tradeVenue);
    for (const p of FORBIDDEN_CONTROL_PATTERNS) assert.ok(!p.test(tv), `${lang} tradeVenue copy matches ${p}`);
  }
});

test("page chrome: no internal strings, no duplicate topbar", () => {
  const page = readFileSync(join(ROOT, "src/features/trade-venue/TradeVenuePage.tsx"), "utf8");
  const root = readFileSync(join(ROOT, "src/features/trade-venue/VenueClientRoot.tsx"), "utf8");
  for (const src of [page, root]) {
    assert.ok(!/tree-sha|TREE_SHA|src\/mock|local-offline|<Topbar|RealityMapFooter/.test(src.replace(/^import .*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "")));
  }
  const route = readFileSync(join(ROOT, "app/arena/trade-venue/page.tsx"), "utf8");
  assert.ok(route.includes("DashboardShell"));
});
