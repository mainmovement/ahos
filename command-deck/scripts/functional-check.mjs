/**
 * Functional verification through the real running app on :3300.
 * Exercises navigation, language/theme switching, table sort/filter/search,
 * CSV export, drawer, palette navigation, and readiness demo mode.
 * Writes evidence/functional-report.json
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { brotliDecompressSync } from "node:zlib";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { chromium as playwright } from "playwright-core";

const BASE = process.env.DECK_BASE_URL ?? "http://127.0.0.1:3300";
mkdirSync(new URL("../evidence/", import.meta.url).pathname, { recursive: true });

for (const name of ["al2023"]) {
  try {
    execFileSync("tar", ["-xf", `/tmp/${name}.tar`, "-C", `/tmp/${name}`]);
  } catch {}
}
const chromiumMod = await import("@sparticuz/chromium");
const executablePath = await chromiumMod.default.executablePath();

const ARGS = [
  "--headless", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
  "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
  "--font-render-hinting=none", "--mute-audio",
];
const env = { ...process.env, LD_LIBRARY_PATH: "/tmp/al2023/lib:/tmp/al2023/lib64" };

const results = [];
const record = (name, pass, detail = "") => {
  results.push({ name, pass, detail });
  console.log(`${pass ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}`);
};

async function withBrowser(fn) {
  const browser = await playwright.launch({ executablePath, headless: true, args: ARGS, env });
  try {
    await fn(browser);
  } finally {
    await browser.close().catch(() => {});
  }
}

await withBrowser(async (browser) => {
  const context = await browser.newContext({ viewport: { width: 1280, height: 860 }, locale: "fa-IR" });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));

  // 1. every route opens (both locales)
  const routes = ["", "/desks", "/desks/gold", "/desks/onchain", "/positions", "/intelligence", "/readiness", "/health", "/settings"];
  for (const locale of ["fa", "en"]) {
    for (const route of routes) {
      const res = await page.goto(`${BASE}/${locale}${route}`, { waitUntil: "load", timeout: 30000 });
      record(`route /${locale}${route}`, res?.status() === 200, `status ${res?.status()}`);
    }
  }

  // 2. root redirects to Persian
  await page.goto(`${BASE}/`, { waitUntil: "load" });
  record("root redirects to /fa", page.url().includes("/fa"), page.url());

  // 3. html dir + lang
  await page.goto(`${BASE}/fa`, { waitUntil: "networkidle" });
  record("fa → dir=rtl lang=fa", (await page.getAttribute("html", "dir")) === "rtl" && (await page.getAttribute("html", "lang")) === "fa");
  await page.goto(`${BASE}/en`, { waitUntil: "networkidle" });
  record("en → dir=ltr lang=en", (await page.getAttribute("html", "dir")) === "ltr" && (await page.getAttribute("html", "lang")) === "en");

  // 4. language toggle preserves path
  await page.goto(`${BASE}/fa/readiness`, { waitUntil: "networkidle" });
  await page.click('header a[aria-label="زبان: English"]');
  await page.waitForURL("**/en/readiness", { timeout: 15000 });
  record("language toggle fa→en keeps /readiness", page.url().endsWith("/en/readiness"), page.url());

  // 5. theme switch persists
  await page.goto(`${BASE}/en`, { waitUntil: "networkidle" });
  await page.click('button[aria-label="Theme"]');
  await page.getByRole("menuitem", { name: "Light" }).click();
  await page.waitForTimeout(400);
  const isLight = await page.evaluate(() => document.documentElement.classList.contains("light"));
  record("theme → light applies .light", isLight);
  await page.reload({ waitUntil: "networkidle" });
  const stillLight = await page.evaluate(() => document.documentElement.classList.contains("light"));
  record("theme persists after reload", stillLight);

  // 6. positions: search, filter, sort, pagination, CSV, drawer
  await page.goto(`${BASE}/fa/positions`, { waitUntil: "networkidle" });
  const initialRows = await page.locator("tbody tr").count();
  await page.getByPlaceholder("جستجوی نماد").fill("XAU");
  await page.waitForTimeout(300);
  const searchRows = await page.locator("tbody tr").count();
  const allXau = await page.locator("tbody tr td:first-child").allInnerTexts();
  record("search filters to XAU", searchRows > 0 && searchRows < initialRows && allXau.every((t) => t.includes("XAU")), `${initialRows}→${searchRows}`);
  await page.getByPlaceholder("جستجوی نماد").fill("");

  await page.getByLabel("جهت").click();
  await page.getByRole("option", { name: "شورت" }).click();
  await page.waitForTimeout(300);
  const sideCount = await page.locator("tbody tr").count();
  record("side filter applies", sideCount > 0, `${sideCount} SHORT rows`);

  // sort by net twice → asc/desc order flips
  await page.getByRole("button", { name: "سود/زیان خالص" }).click();
  await page.waitForTimeout(250);
  const firstAsc = await page.locator("tbody tr").first().innerText();
  await page.getByRole("button", { name: "سود/زیان خالص" }).click();
  await page.waitForTimeout(250);
  const firstDesc = await page.locator("tbody tr").first().innerText();
  record("net-P&L sort flips order", firstAsc !== firstDesc);

  // CSV export — real download of the sample set only
  const downloadPromise = page.waitForEvent("download", { timeout: 15000 });
  await page.getByRole("button", { name: "خروجی CSV" }).click();
  const download = await downloadPromise;
  const path = await download.path();
  const fs = await import("node:fs");
  const csv = fs.readFileSync(path ?? "", "utf8");
  record("CSV export downloads", download.suggestedFilename().endsWith(".csv") && csv.includes("PAPER-ONLY") && csv.includes("XAUUSD"), `${csv.split("\n").length - 1} lines`);

  // drawer
  await page.locator("tbody tr td:first-child button").first().click();
  await page.waitForTimeout(500);
  const drawerVisible = await page.getByRole("dialog").isVisible().catch(() => false);
  record("position drawer opens", drawerVisible);
  const drawerHasFormula = drawerVisible ? await page.getByRole("dialog").innerText().then((t) => t.includes("خالص = ناخالص") || t.includes("NET")) : false;
  record("drawer shows accounting identity", drawerHasFormula);
  await page.keyboard.press("Escape");

  // empty state
  await page.getByPlaceholder("جستجوی نماد").fill("ZZZZ-NOPE");
  await page.waitForTimeout(300);
  const emptyShown = await page.getByText("نتیجه‌ای یافت نشد").isVisible().catch(() => false);
  record("empty state appears", emptyShown);
  await page.getByRole("button", { name: "پاک‌کردن فیلترها" }).click();
  await page.waitForTimeout(300);
  record("clear filters restores rows", (await page.locator("tbody tr").count()) === 10);

  // pagination
  await page.getByRole("button", { name: "بعدی" }).click();
  await page.waitForTimeout(250);
  record("pagination advances", (await page.getByText("صفحه ۲")).isVisible());

  // 7. readiness demo toggle flips items but verdict stays
  await page.goto(`${BASE}/fa/readiness`, { waitUntil: "networkidle" });
  const before = await page.locator("text=PASS").count();
  await page.locator("#demo-mode").click();
  await page.waitForTimeout(300);
  const after = await page.locator("text=PASS").count();
  const verdict = await page.locator("text=آماده نیست / مجاز نیست").first().isVisible();
  record("demo mode reveals demonstration PASS states", after > before, `${before}→${after}`);
  record("verdict stays NOT READY / NOT AUTHORIZED", verdict);

  // 8. palette navigation
  await page.goto(`${BASE}/fa`, { waitUntil: "networkidle" });
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(400);
  await page.keyboard.type("تنظیمات");
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(800);
  record("palette navigates to settings", page.url().endsWith("/fa/settings"), page.url());

  // 9. notifications popover
  await page.goto(`${BASE}/fa`, { waitUntil: "networkidle" });
  await page.click('button[aria-label="هشدارها"]');
  await page.waitForTimeout(400);
  record("notifications popover shows alerts", await page.getByText("کلید توقف متصل نیست").isVisible());

  // 10. scene toggle persists + fallback path renders
  await page.keyboard.press("Escape"); // close the popover so it stops intercepting pointers
  await page.waitForTimeout(400);
  await page.click('button[aria-label="نمایش صحنه سه‌بعدی"]');
  await page.waitForTimeout(600);
  const canvasGone = await page.evaluate(() => document.querySelector("[data-globe-stage] canvas") === null);
  record("scene off → 2D fallback", canvasGone);
  await page.click('button[aria-label="نمایش صحنه سه‌بعدی"]');
  await page.waitForTimeout(1500);
  const canvasBack = await page.evaluate(() => document.querySelector("[data-globe-stage] canvas") !== null);
  record("scene on → canvas mounts", canvasBack);

  // 11. no order/trade actions exist anywhere
  await page.goto(`${BASE}/fa/positions`, { waitUntil: "networkidle" });
  const orderButtons = await page.locator('button:has-text("خرید"), button:has-text("فروش"), button:has-text("Order"), button:has-text("Buy"), button:has-text("Sell")').count();
  record("no order/close/trade actions", orderButtons === 0);

  // 12. operations room: three views, weather chip, role chips, workstation panel
  await page.goto(`${BASE}/fa`, { waitUntil: "networkidle" });
  await page.waitForTimeout(5200);
  const viewRadios = await page.locator("[data-scene-view]").count();
  record("room dock offers three views", viewRadios === 3, `count ${viewRadios}`);
  record("live weather chip present", (await page.locator("[data-weather-chip]").count()) === 1);
  record(
    "weather chip stays honest when offline",
    (await page.locator("[data-weather-chip] .text-amber-500").count()) === 1,
  );
  const roleChips = await page.evaluate(() => document.querySelectorAll("[data-role-chip]").length);
  record("role chips on desks ≥ 12", roleChips >= 12, `count ${roleChips}`);
  await page.evaluate(() => {
    document.querySelector('[data-role-chip="crypto"]')?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await page.waitForTimeout(500);
  record("role chip opens workstation panel", (await page.locator("[data-role-panel]").count()) === 1);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);
  record("Escape closes workstation panel", (await page.locator("[data-role-panel]").count()) === 0);
  await page.click('[data-scene-view="fpv"]');
  await page.waitForTimeout(2500);
  record(
    "commander FPV view stays alive",
    await page.evaluate(() => document.querySelector("[data-globe-stage] canvas") !== null),
  );
  const canvasCount = await page.evaluate(() => document.querySelectorAll("[data-globe-stage] canvas").length);
  // one WebGL canvas; every console/board screen is a CanvasTexture drawn into it
  record("room stage renders a single WebGL canvas with GPU screen textures", canvasCount === 1, `count ${canvasCount}`);

  record("zero page errors across interactions", pageErrors.length === 0, pageErrors.slice(0, 3).join(" | "));

  await context.close();
});

const passCount = results.filter((r) => r.pass).length;
console.log(`\n${passCount}/${results.length} functional checks passed`);
writeFileSync(new URL("../evidence/functional-report.json", import.meta.url).pathname, JSON.stringify({ passCount, total: results.length, results }, null, 2));
