import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { STATUS_TONE, TRUTH_STATUSES, type ChipStatus } from "../src/features/white-hats/truth/status.ts";
import { displayStatus, normalizeSnapshot } from "../src/features/white-hats/lib/normalize.ts";
import { countNonDemo, isViolation, telemetryRowCount } from "../src/features/white-hats/predicates.ts";
import { buildFixture } from "../src/mock/white_hats/fixtures/index.ts";

const ROOT = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (p.endsWith(".tsx")) out.push(p);
  }
  return out;
}
const FA = JSON.parse(readFileSync(join(ROOT, "src/i18n/fa.json"), "utf8"));
function resolveTr(text: string): string {
  return text.replace(/tr\("fa", "([^"]+)"\)/g, (_m, key: string) => {
    const v = key.split(".").reduce((o: any, k) => o?.[k], FA);
    return typeof v === "string" ? v : key;
  });
}
const SRC = [...walk(join(ROOT, "src/features/white-hats")), join(ROOT, "app/arena/white-hats/page.tsx")];

test("UNKNOWN is grey; green is reserved for LIVE", () => {
  assert.equal(STATUS_TONE.UNKNOWN, "grey");
  const green = (Object.keys(STATUS_TONE) as ChipStatus[]).filter((s) => STATUS_TONE[s] === "live");
  assert.deepEqual(green, ["LIVE"]);
  for (const s of TRUTH_STATUSES) assert.ok(STATUS_TONE[s]);
});

test("demo-backed data never displays LIVE; STALE needs a timestamp", () => {
  assert.equal(displayStatus("LIVE", true, "2026-10-16T10:00:00Z"), "DEMO");
  assert.equal(displayStatus("STALE", false, null), "UNKNOWN");
  assert.equal(displayStatus("STALE", true, "2026-10-16T10:00:00Z"), "STALE");
  for (const scenario of ["calm", "violation", "empty"] as const) {
    const snap = normalizeSnapshot(buildFixture(scenario));
    assert.ok(snap.demo, "mock fixtures are demo");
    assert.notEqual(snap.freshness, "LIVE");
    for (const d of snap.decisions) {
      assert.notEqual(d.freshness, "LIVE");
      if (d.freshness === "STALE") assert.ok(d.proposedAt);
    }
    for (const i of snap.inspectors) {
      assert.notEqual(i.status, "LIVE");
      if (i.status === "STALE") assert.ok(i.lastRunAt);
    }
  }
});

test("DEMO rows are excluded from totals", () => {
  const snap = buildFixture("calm");
  assert.equal(snap.decisions.length, 7);
  assert.equal(countNonDemo(snap.decisions), 6);
  assert.deepEqual(telemetryRowCount(snap), { total: 20, nonDemo: 18 });
});

test("violation predicate", () => {
  assert.equal(isViolation(buildFixture("calm")), false);
  assert.equal(isViolation(buildFixture("violation")), true);
  assert.equal(isViolation({ ...buildFixture("calm"), realTrading: true }), true);
  assert.equal(isViolation({ ...buildFixture("calm"), executionMode: "SIMULATION" }), true);
});

test("unjudged decisions are UNKNOWN, undated ones have null time", () => {
  const snap = buildFixture("calm");
  const unjudged = snap.decisions.filter((d) => d.verdict === "UNKNOWN");
  assert.ok(unjudged.length > 0);
  assert.ok(snap.decisions.some((d) => d.proposedAt === null));
});

test("no execution controls: buttons are read-only verbs; no forms/number inputs/sliders; no trading verbs", () => {
  const allowed = /(کپی|جزئیات|بستن|بازخوانی|برون‌بری|CSV|JSON|مشاهده شواهد|همه|باز|برطرف|کپی شد)/;
  const forbidden = /(خرید|فروش|approve|override|enable[\s-]?trading|place[\s-]?order|سفارش گذاشتن|فعال[\s-]?سازی معامله)/i;
  for (const file of SRC) {
    const src = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    assert.ok(!/<form\b/.test(src), `${file}: form`);
    assert.ok(!/type="(number|range)"/.test(src), `${file}: sizing input`);
    assert.ok(!forbidden.test(src), `${file}: forbidden verb`);
    for (const m of src.matchAll(/<button\b[\s\S]*?<\/button>/g)) {
      const text = resolveTr(m[0]);
      assert.ok(allowed.test(text) || /\{opt\.label\}/.test(text), `${file}: ${text.slice(0, 160)}`);
    }
  }
  for (const lang of ["fa", "en"]) {
    const j = JSON.parse(readFileSync(join(ROOT, `src/i18n/${lang}.json`), "utf8")).whiteHats;
    assert.ok(!forbidden.test(JSON.stringify(j)));
  }
});

test("chrome: no duplicate topbar, no hard-coded demo, no internal strings, fonts >= 12px", () => {
  const screen = readFileSync(join(ROOT, "src/features/white-hats/WhiteHatsScreen.tsx"), "utf8");
  assert.ok(!/demo=\{true\}/.test(screen));
  assert.ok(!/<Topbar/.test(screen));
  for (const file of SRC) {
    const src = readFileSync(file, "utf8");
    assert.ok(!/mock:\/\/|truncate/.test(src.replace(/^\s*(\/\/|\*).*$/gm, "")), `${file}: internal string / truncate`);
    for (const m of src.matchAll(/text-\[(\d+(?:\.\d+)?)px\]/g)) assert.ok(Number(m[1]) >= 12, `${file}: ${m[0]}`);
  }
  assert.ok(readFileSync(join(ROOT, "app/arena/white-hats/page.tsx"), "utf8").includes("DashboardShell"));
});
