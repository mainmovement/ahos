import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  TONE, TRUTH_TONE, TRUTH_STATUSES, computeTotals, deriveStoryVerification, independentSourceCount,
  isPaperOnlyViolation, connectedMarkets, disconnectedMarkets,
} from "../src/features/newsroom/lib/truth.ts";
import { buildStoryView, filterStories } from "../src/features/newsroom/lib/selectors.ts";
import { derivePipeline } from "../src/features/newsroom/lib/pipeline.ts";
import { demoteLiveOnMock } from "../src/features/newsroom/lib/normalize.ts";
import { CALM_SNAPSHOT, EMPTY_SNAPSHOT, VIOLATION_SNAPSHOT } from "../src/mock/newsroom/fixtures.ts";
import { parseFlag, parseScenario, parseTier } from "../src/mock/newsroom/scenarios.ts";
import type { NewsSource, Story } from "../src/features/newsroom/lib/types.ts";

const ROOT = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.(ts|tsx)$/.test(p)) out.push(p);
  }
  return out;
}
const FILES = [...walk(join(ROOT, "src/features/newsroom")), ...walk(join(ROOT, "src/mock/newsroom")), join(ROOT, "app/arena/newsroom/page.tsx")];

const src = (id: string, group: string, over: Partial<NewsSource> = {}): NewsSource => ({
  id, nameFa: id, urlPlaceholder: "https://example.invalid/" + id, credibility: "A", status: "LIVE",
  lastReadAt: "2026-10-14T08:00:00Z", independenceGroup: group, noteFa: null, ...over,
});
const story = (sourceIds: string[], over: Partial<Story> = {}): Story => ({
  id: "s1", headlineFa: "x", headlineEn: null, market: "OIL", publishedAt: "2026-10-14T08:00:00Z",
  claimStrength: "MODERATE", sourceIds, marketImpactNoteFa: null, demo: false, status: "LIVE", conflictId: null, ...over,
});

test("UNKNOWN is grey and only LIVE is green", () => {
  assert.equal(TRUTH_TONE.UNKNOWN, "unknown");
  const positive = TRUTH_STATUSES.filter((s) => TONE[TRUTH_TONE[s]].positive);
  assert.deepEqual(positive, ["LIVE"]);
  assert.deepEqual([...TRUTH_STATUSES], ["LIVE", "STALE", "UNKNOWN", "DEMO", "CONFLICT", "REJECTED"]);
});

test("two-source rule: VERIFIED needs two independent sources", () => {
  const a = src("a", "g1"); const b = src("b", "g2"); const c = src("c", "g1");
  assert.equal(deriveStoryVerification({ story: story(["a", "b"]), sources: [a, b], hasConflict: false }), "VERIFIED");
  assert.equal(deriveStoryVerification({ story: story(["a"]), sources: [a], hasConflict: false }), "PARTIAL");
  assert.equal(deriveStoryVerification({ story: story(["a", "c"]), sources: [a, c], hasConflict: false }), "PARTIAL");
  assert.equal(independentSourceCount([a, c]), 1);
  const noTime = src("n", "g3", { lastReadAt: null });
  assert.equal(deriveStoryVerification({ story: story(["a", "n"]), sources: [a, noTime], hasConflict: false }), "PARTIAL");
  assert.equal(deriveStoryVerification({ story: story([]), sources: [], hasConflict: false }), "UNKNOWN");
});

test("CONFLICT never auto-clears and DEMO wins precedence", () => {
  const a = src("a", "g1"); const b = src("b", "g2");
  assert.equal(deriveStoryVerification({ story: story(["a", "b"]), sources: [a, b], hasConflict: true }), "CONFLICT");
  assert.equal(deriveStoryVerification({ story: story(["a", "b"], { demo: true }), sources: [a, b], hasConflict: true }), "DEMO");
  for (const c of CALM_SNAPSHOT.conflicts) assert.equal(c.status, "CONFLICT");
});

test("DEMO rows are excluded from verified totals", () => {
  const t = computeTotals(CALM_SNAPSHOT);
  assert.equal(t.total, CALM_SNAPSHOT.stories.length);
  const demoRows = CALM_SNAPSHOT.stories.filter((s) => s.demo || s.status === "DEMO").length;
  assert.ok(t.demo >= demoRows);
  assert.equal(t.verified + t.partial + t.unknown + t.conflict + t.demo, t.total);
  for (const s of CALM_SNAPSHOT.stories.filter((x) => x.demo)) {
    assert.notEqual(buildStoryView(CALM_SNAPSHOT, s).verification, "VERIFIED");
  }
});

test("mock snapshots never show LIVE or VERIFIED after normalisation", () => {
  for (const snap of [CALM_SNAPSHOT, VIOLATION_SNAPSHOT, EMPTY_SNAPSHOT]) {
    const n = demoteLiveOnMock(snap);
    assert.equal(computeTotals(n).verified, 0);
    for (const s of n.sources) assert.notEqual(s.status, "LIVE");
    for (const s of n.stories) assert.notEqual(s.status, "LIVE");
    for (const r of n.reporters) assert.notEqual(r.status, "LIVE");
  }
});

test("STALE needs a timestamp; no timestamp means UNKNOWN in fixtures", () => {
  for (const s of CALM_SNAPSHOT.sources) {
    if (s.status === "STALE") assert.ok(s.lastReadAt, s.id);
    if (!s.lastReadAt) assert.notEqual(s.status, "LIVE", s.id);
  }
});

test("violation predicate: executionMode != PAPER_ONLY or realTrading", () => {
  assert.equal(isPaperOnlyViolation({ executionMode: "PAPER_ONLY", realTrading: false }), false);
  assert.equal(isPaperOnlyViolation({ executionMode: "PAPER_ONLY", realTrading: true }), true);
  assert.equal(isPaperOnlyViolation({ executionMode: "LIVE", realTrading: false }), true);
  assert.equal(isPaperOnlyViolation({ executionMode: "UNKNOWN", realTrading: false }), true);
  assert.equal(isPaperOnlyViolation(CALM_SNAPSHOT), false);
  assert.equal(isPaperOnlyViolation(VIOLATION_SNAPSHOT), true);
});

test("focus: only oil and gold connected, others PLANNED with no invented stories", () => {
  assert.deepEqual(connectedMarkets(CALM_SNAPSHOT.markets).map((m) => m.id).sort(), ["GOLD", "OIL"]);
  const off = disconnectedMarkets(CALM_SNAPSHOT.markets);
  assert.ok(off.length >= 2);
  for (const m of off) { assert.equal(m.status, "PLANNED"); assert.equal(m.storyCount, null); }
  for (const s of CALM_SNAPSHOT.stories) assert.ok(s.market === "OIL" || s.market === "GOLD");
});

test("pipeline: unrun stages are never fake DONE", () => {
  const a = src("a", "g1");
  const stages = derivePipeline({ story: story(["a"]), sources: [a], hasConflict: false });
  assert.equal(stages.length, 5);
  assert.equal(stages.filter((s) => s.state === "CURRENT").length <= 1, true);
  const last = stages[stages.length - 1];
  assert.notEqual(last.state, "DONE");
});

test("filters oil/gold/conflict/demo and calm view limit", () => {
  assert.ok(filterStories(CALM_SNAPSHOT, "OIL").every((s) => s.market === "OIL"));
  assert.ok(filterStories(CALM_SNAPSHOT, "GOLD").every((s) => s.market === "GOLD"));
  const inbox = readFileSync(join(ROOT, "src/features/newsroom/components/StoryInbox.tsx"), "utf8");
  assert.match(inbox, /CALM_STORY_LIMIT = 7/);
});

test("route params parse safely", () => {
  assert.equal(parseScenario("nope"), "calm");
  assert.equal(parseScenario("empty"), "empty");
  assert.equal(parseTier("0"), 0); assert.equal(parseTier("9"), 1);
  assert.equal(parseFlag("1"), true); assert.equal(parseFlag("true"), false);
});

const FORBIDDEN: { pattern: RegExp; why: string }[] = [
  { pattern: /\bon(Buy|Sell)\b/, why: "buy/sell handler" },
  { pattern: /\bplaceOrder\b|\borderPlacement\b|\bsubmitOrder\b/, why: "order placement" },
  { pattern: /\bexecuteTrade\b|\bexecuteOrder\b|\btradeOnNews\b/, why: "trade execution" },
  { pattern: /\bapprove(Story|Trade|Signal)\b|\bhandleApprove\b/, why: "approval control" },
  { pattern: /\boverride(Verdict|Decision)\b|\bhandleOverride\b/, why: "judge override" },
  { pattern: /\benableTrading\b|\bactivateTrading\b|\bgoLiveTrading\b/, why: "enable trading" },
  { pattern: /\bpositionSize\b|\bleverageSize\b|\briskCapital\b/, why: "sizing control" },
  { pattern: /\btakeProfit\b|\bstopLoss\b|\borderType\b/, why: "order parameters" },
  { pattern: /\bautoTrade\b|\bautoTrading\b|\btradeHook\b/, why: "auto-trading hook" },
  { pattern: /\bfetch\(['"]https?:/, why: "outbound network call" },
  { pattern: /\baxios\b|\bnode-fetch\b/, why: "http client dependency" },
];
const FA_ACTIONS = ["خرید", "فروش", "ثبت سفارش", "ارسال سفارش", "فعال‌سازی معاملات", "تأیید نهایی", "سیگنال خرید", "سیگنال فروش"];
const NEGATION = /(نمی‌شود|نمی‌کن|ممنوع|never|no |without|forbidden|allowed|مجاز نیست|خواندنی)/i;
const FA = JSON.parse(readFileSync(join(ROOT, "src/i18n/fa.json"), "utf8"));
function resolveTr(text: string): string {
  return text.replace(/tr\("fa", "([^"]+)"\)/g, (_m, key: string) => {
    const v = key.split(".").reduce((o: any, k) => o?.[k], FA);
    return typeof v === "string" ? v : key;
  });
}

test("no trading controls, approvals or auto-trading hooks in source", () => {
  assert.ok(FILES.length > 15);
  const bad: string[] = [];
  for (const f of FILES) readFileSync(f, "utf8").split("\n").forEach((line, i) => {
    if (NEGATION.test(line)) return;
    for (const { pattern, why } of FORBIDDEN) if (pattern.test(line)) bad.push(f + ":" + (i + 1) + " [" + why + "] " + line.trim());
  });
  assert.deepEqual(bad, []);
});

test("no actionable control is labelled with a trading verb (after tr() resolution)", () => {
  const bad: string[] = [];
  for (const f of FILES.filter((x) => x.endsWith(".tsx"))) readFileSync(f, "utf8").split("\n").forEach((raw, i) => {
    const line = resolveTr(raw);
    if (!/<button|role="button"|<a\s|aria-label=|title=|>\{?ACTION\./.test(line) || NEGATION.test(line)) return;
    for (const w of FA_ACTIONS) if (line.includes(w)) bad.push(f + ":" + (i + 1) + " [" + w + "]");
  });
  assert.deepEqual(bad, []);
});

test("no server action, API route or outbound network in the newsroom tree", () => {
  for (const f of FILES) {
    const t = readFileSync(f, "utf8");
    assert.doesNotMatch(t, /['"]use server['"]/);
    assert.doesNotMatch(t, /export (async )?function (GET|POST|PUT|DELETE)\s*\(/);
    assert.doesNotMatch(t, /\bWebSocket\b|XMLHttpRequest/);
  }
});

test("PAPER_ONLY pill is permanent in the page bar (no dismiss handler)", () => {
  const bar = readFileSync(join(ROOT, "src/features/newsroom/components/PageBar.tsx"), "utf8");
  assert.match(bar, /paper-only-pill/);
  assert.doesNotMatch(bar, /dismiss|onClose/i);
});
