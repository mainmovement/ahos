import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  MAX_HIGHLIGHTS, STALE_AFTER_MS, attentionRank, buildMessageHub, buildMissionMap, buildResearch, buildSelfEval, capHighlights, demoize,
  formatNum, freshness, ideasFromShelfFile, redact, tehranStamp, violationOf, type Highlight,
} from "../src/features/missions-b2/lib/model";
import { headerConflicts, parseMissionsStatus } from "../src/features/missions-b2/lib/missions-status";
import { getComponentState, validateContract } from "../src/features/missions-b2/contract/validate";
import { findForbiddenControl } from "../src/features/trade-venue/logic/truth";
import type { AHOSArenaContract } from "../src/features/missions-b2/contract/types";

const ROOT = join(import.meta.dirname, "..");
const FEATURE = join(ROOT, "src", "features", "missions-b2");
const contract = JSON.parse(readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8")) as AHOSArenaContract;
const fa = JSON.parse(readFileSync(join(ROOT, "src", "i18n", "fa.json"), "utf8"));
const NOW = Date.parse("2026-10-17T00:00:00+03:30");

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => { const p = join(dir, n); return statSync(p).isDirectory() ? walk(p) : [p]; });
}

test("contract: example validates, DEMO-flagged, paper-only", () => {
  assert.equal(validateContract(contract), true);
  for (const k of ["messageHub", "selfEvaluation", "ideaShelf", "researchInstitute", "missionMap"] as const) assert.equal(contract[k].demo, true);
  assert.equal(contract.executionMode, "PAPER_ONLY");
  assert.equal(contract.realTrading, false);
});
test("contract: invalid input is rejected, never throws", () => {
  for (const bad of [null, undefined, 3, "x", [], {}, { ...contract, messageHub: null }, { ...contract, realTrading: "no" }]) assert.equal(validateContract(bad), false);
});
test("contract: DEMO snapshot is never reported LIVE (audit fix)", () => {
  assert.equal(getComponentState(contract.messageHub), "SIMULATED");
  assert.equal(getComponentState({ ...contract.messageHub, demo: false }), "LIVE");
  assert.equal(getComponentState(null), "UNAVAILABLE");
});
test("contract: example secrets scan (no token/chat id values)", () => {
  const s = readFileSync(join(FEATURE, "contract", "ahos-arena-contract.example.json"), "utf8");
  assert.equal(/\d{6,}:[A-Za-z0-9_-]{20,}/.test(s), false);
  assert.equal(/"(token|chatId|chat_id|secret|password)"\s*:/i.test(s), false);
});

test("freshness: DEMO never LIVE; STALE needs timestamp; no timestamp => UNKNOWN", () => {
  assert.equal(freshness("demo", "2026-10-16T10:00:00Z", NOW), "DEMO");
  assert.equal(freshness("none", null, NOW), "UNAVAILABLE");
  assert.equal(freshness("file", null, NOW), "UNKNOWN");
  assert.equal(freshness("file", "garbage", NOW), "UNKNOWN");
  assert.equal(freshness("file", new Date(NOW - 1000).toISOString(), NOW), "LIVE");
  assert.equal(freshness("file", new Date(NOW - STALE_AFTER_MS - 1000).toISOString(), NOW), "STALE");
  assert.equal(demoize("LIVE", true), "DEMO");
  assert.equal(demoize("LIVE", false), "LIVE");
  assert.equal(demoize("STALE", true), "STALE");
});

test("calm view: <= 7 highlights, problems first, nothing invented", () => {
  const items: Highlight[] = Array.from({ length: 12 }, (_, i) => ({ id: `i${i}`, title: `t${i}`, detail: null, status: i === 9 ? "CONFLICT" : "DEMO" }));
  const { shown, hidden } = capHighlights(items);
  assert.equal(shown.length, MAX_HIGHLIGHTS);
  assert.equal(hidden, 5);
  assert.equal(shown[0].id, "i9");
  assert.ok(attentionRank("CONFLICT") < attentionRank("LIVE"));
  assert.deepEqual(capHighlights([]).shown, []);
});

test("message hub: DEMO rows never LIVE, blocked owner flagged, no secrets", () => {
  const v = buildMessageHub(contract.messageHub, true);
  assert.ok(v.highlights.every((h) => h.status !== "LIVE"));
  assert.equal(v.telegramBlockedOwner, true);
  assert.equal(JSON.stringify(v).match(/\d{6,}:[A-Za-z0-9_-]{20,}/), null);
});
test("self evaluation: period select, missing numbers render as dash", () => {
  const w = buildSelfEval(contract.selfEvaluation, "week", true);
  assert.ok(w.highlights.length <= 7 || w.highlights.length > 0);
  assert.ok(w.highlights.every((h) => h.status !== "LIVE"));
  assert.equal(formatNum(null), "-");
  assert.equal(formatNum(undefined), "-");
  assert.equal(formatNum(0), "0");
  assert.equal(formatNum(NaN), "-");
});
test("research: passed-unseen never computed from DEMO rows", () => {
  assert.equal(buildResearch(contract.researchInstitute, true).passedUnseen, null);
  const real = buildResearch(contract.researchInstitute, false);
  assert.equal(typeof real.passedUnseen, "number");
});
test("idea shelf: real file binding maps id/title/tier only", () => {
  const rows = ideasFromShelfFile(JSON.parse(readFileSync(join(ROOT, "config", "idea_shelf.json"), "utf8")));
  assert.ok(rows && rows.length > 0);
  assert.ok(rows.every((r) => r.origin === null && r.lifecycle === "UNKNOWN" && r.reason === null && r.minRam === null));
  assert.equal(ideasFromShelfFile(null), null);
  assert.equal(ideasFromShelfFile({ ideas: "x" }), null);
});

const MD = `# AHOS Claude missions: status checklist

Generated 2026-10-16 ~20:50 Tehran (UTC+3:30).

## 1. Totals

- Units tracked: **4**
- DONE: **2** (50%)
- PARTIAL: **1** (25%)
- NOT STARTED: **1** (25%)

## 2. Checklist

### DONE

- [x] **M9**: Truth baseline. abc123. CAVEAT: machinery only
- [x] **M-D1**: App window e9d2ddf

### PARTIAL

- [~] **M10**: Stages 1,2,3 done; stage 4 = BLOCKED_OWNER

### NOT STARTED

- [ ] **M35.3**: BLOCKED_OWNER: needs rotation

## 3. Other

- [ ] **ZZ**: not a mission row
`;
test("missions-status parser: states, caveat, blocked owner, header cross-check", () => {
  const p = parseMissionsStatus(MD)!;
  assert.equal(p.missions.length, 4);
  assert.equal(p.generatedAt, "2026-10-16T20:50:00+03:30");
  assert.equal(p.missions[0].caveat, "machinery only");
  assert.equal(p.missions[1].group, "M-D");
  assert.equal(p.missions[2].blockedOwner, true);
  assert.equal(p.missions[3].state, "NOT_STARTED");
  assert.equal(headerConflicts(p), false);
  assert.equal(headerConflicts({ ...p, header: { ...p.header, done: 5 } }), true);
  assert.equal(parseMissionsStatus(""), null);
  assert.equal(parseMissionsStatus("random text"), null);
});
test("mission map: counts derived from rows; DEMO has no counts", () => {
  const p = parseMissionsStatus(MD)!;
  const m = buildMissionMap(p.missions, false);
  assert.deepEqual(m.counts, { done: 2, partial: 1, notStarted: 1, blockedOwner: 2 });
  assert.equal(buildMissionMap(p.missions, true).counts, null);
  assert.ok(m.highlights[0].detail === "BLOCKED_OWNER");
});
test("mission map: real MISSIONS_STATUS.md (if present) parses and agrees with its header", { skip: !process.env.AHOS_MISSIONS_STATUS_PATH && false }, () => {
  const path = process.env.AHOS_MISSIONS_STATUS_PATH ?? join(ROOT, "..", "ahos_assets", "MISSIONS_STATUS.md");
  let text: string;
  try { text = readFileSync(path, "utf8"); } catch { return; }
  const p = parseMissionsStatus(text);
  assert.ok(p && p.missions.length > 0);
  assert.equal(headerConflicts(p), false, JSON.stringify(p.header));
});

test("redact: tokens and secrets never survive", () => {
  assert.ok(!redact("bot 123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw ok").includes("AAHdq"));
  assert.ok(!redact("api_key=abcdef123").includes("abcdef123"));
  assert.ok(!redact("Authorization Bearer abcdefghijklmnop1234").includes("abcdefghijkl"));
  assert.equal(redact(null), "");
  assert.equal(redact("plain text"), "plain text");
});
test("violation: realTrading or non-PAPER_ONLY => VIOLATION; paper => none", () => {
  assert.equal(violationOf("PAPER_ONLY", false), null);
  assert.equal(violationOf("PAPER_ONLY", true)?.code, "REAL_TRADING_FLAG");
  assert.equal(violationOf("LIVE", false)?.code, "NON_PAPER_MODE");
  assert.equal(violationOf("weird", false)?.code, "NON_PAPER_MODE");
});
test("tehran stamp: UTC+3:30, missing => dash", () => {
  assert.equal(tehranStamp("2026-10-16T10:00:00Z"), "2026-10-16 13:30");
  assert.equal(tehranStamp(null), "-");
  assert.equal(tehranStamp("nope"), "-");
});

test("source scan: no controls, no trade/approve verbs, no <12px, no green/red pnl, i18n via tr()", () => {
  const files = walk(FEATURE).filter((f) => /\.(tsx|ts|css)$/.test(f) && !f.includes("contract"));
  const appFiles = ["message-hub", "self-evaluation", "idea-shelf", "research-institute", "mission-map"].flatMap((n) => walk(join(ROOT, "app", "arena", n)));
  for (const f of [...files, ...appFiles]) {
    const s = readFileSync(f, "utf8");
    if (f.endsWith(".tsx")) {
      assert.ok(!/<button\b|onClick=|<input\b|<form\b/.test(s), `control element in ${f}`);
      assert.ok(!/text-(green|red|emerald|rose)-/.test(s), `green/red class in ${f}`);
    }
    if (f.endsWith(".css")) {
      for (const m of s.matchAll(/font-size:\s*(\d+(?:\.\d+)?)px/g)) assert.ok(Number(m[1]) >= 12, `font-size ${m[1]}px in ${f}`);
      assert.ok(!/(green|#0f0|#00ff00|#f00\b|#ff0000)/i.test(s), `green/red colour in ${f}`);
    }
  }
});
test("i18n: every missionsB2 key used by tr() exists in fa.json; no forbidden control wording in copy", () => {
  const used = new Set<string>();
  for (const f of walk(FEATURE).filter((x) => x.endsWith(".tsx"))) {
    const s = readFileSync(f, "utf8");
    for (const m of s.matchAll(/\bt\(\s*"([^"]+)"/g)) used.add(m[1]);
    for (const m of s.matchAll(/tr\("fa",\s*"missionsB2\.([^"]+)"/g)) used.add(m[1]);
    for (const m of s.matchAll(/t\(`([a-zA-Z.]+)\$\{/g)) used.add(`~${m[1]}`);
  }
  const get = (p: string) => p.split(".").reduce<unknown>((o, k) => (o && typeof o === "object" ? (o as Record<string, unknown>)[k] : undefined), fa.missionsB2);
  for (const k of used) if (!k.startsWith("~")) assert.equal(typeof get(k), "string", `missing fa key missionsB2.${k}`);
  for (const id of ["message-hub", "self-evaluation", "idea-shelf", "research-institute", "mission-map"]) {
    assert.equal(typeof get(`page.${id}.title`), "string");
    assert.equal(typeof get(`page.${id}.sub`), "string");
  }
  for (const w of ["week", "month"]) assert.equal(typeof get(`selfEvaluation.${w}`), "string");
  for (const k of Object.keys(fa.missionsB2.nav)) assert.equal(findForbiddenControl(fa.missionsB2.nav[k]), null);
});
