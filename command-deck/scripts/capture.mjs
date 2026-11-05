/**
 * Real-browser screenshot evidence for the AHOS Intelligence Command Deck.
 * Uses playwright-core driving an npm-bundled Chromium (@sparticuz/chromium).
 * Every screenshot comes from the actual running application on :3300.
 *
 * Usage: DECK_BASE_URL=http://127.0.0.1:3300 npm run shots
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { brotliDecompressSync } from "node:zlib";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { chromium as playwright } from "playwright-core";

const BASE = process.env.DECK_BASE_URL ?? "http://127.0.0.1:3300";
const OUT = new URL("../evidence/screenshots/", import.meta.url).pathname;

/* ---------------- prepare the bundled chromium ---------------- */

// extract the al2 libs, fonts and swiftshader next to the binary
for (const name of ["al2023", "fonts", "swiftshader"]) {
  const raw = readFileSync(
    new URL(`../node_modules/@sparticuz/chromium/bin/${name}.tar.br`, import.meta.url),
  );
  const tarPath = `/tmp/${name}.tar`;
  writeFileSync(tarPath, brotliDecompressSync(raw));
  const dir = name === "al2023" ? "/tmp/al2023" : `/tmp/${name}`;
  execFileSync("tar", ["-xf", tarPath, "-C", dir]);
}
const chromiumMod = await import("@sparticuz/chromium");
const chromium = chromiumMod.default;
const executablePath = await chromium.executablePath();

const env = {
  ...process.env,
  LD_LIBRARY_PATH: "/tmp/al2023/lib:/tmp/al2023/lib64:/tmp/swiftshader:/usr/lib/x86_64-linux-gnu",
  FONTCONFIG_PATH: "/tmp/fonts",
};

const ARGS = [
  "--headless",
  "--no-sandbox",
  "--disable-setuid-sandbox",
  "--disable-dev-shm-usage",
  "--disable-gpu-sandbox",
  "--disable-background-networking",
  "--disable-default-apps",
  "--disable-extensions",
  "--disable-sync",
  "--disable-translate",
  "--metrics-recording-only",
  "--mute-audio",
  "--no-first-run",
  "--use-gl=angle",
  "--use-angle=swiftshader",
  "--enable-unsafe-swiftshader",
  "--ignore-gpu-blocklist",
  "--enable-webgl",
  "--font-render-hinting=none",
  "--hide-scrollbars",
  "--force-color-profile=srgb",
];

/* ---------------- shot list ---------------- */

const SHOTS = [
  { file: "01-command-center-fa-dark-hero.png", path: "/fa", theme: "dark", viewport: [1280, 860], fullPage: false, settle: 4200 },
  { file: "01b-command-center-fa-dark-full.png", path: "/fa", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 4200 },
  { file: "02-command-center-en-dark.png", path: "/en", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 4200 },
  { file: "03-desks-fa-dark.png", path: "/fa/desks", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1400 },
  { file: "04-desk-detail-gold-fa-dark.png", path: "/fa/desks/gold", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1600 },
  { file: "04b-desk-detail-gold-en-dark.png", path: "/en/desks/gold", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1600 },
  { file: "05-readiness-fa-dark.png", path: "/fa/readiness", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1200 },
  { file: "06-positions-fa-dark.png", path: "/fa/positions", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1400 },
  { file: "07-intelligence-fa-dark.png", path: "/fa/intelligence", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1200 },
  { file: "08-health-fa-dark.png", path: "/fa/health", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1200 },
  { file: "09-settings-fa-dark.png", path: "/fa/settings", theme: "dark", viewport: [1280, 860], fullPage: true, settle: 1000 },
  { file: "10-command-center-fa-light.png", path: "/fa", theme: "light", viewport: [1280, 860], fullPage: false, settle: 4200 },
  { file: "10b-desks-en-light.png", path: "/en/desks", theme: "light", viewport: [1280, 860], fullPage: true, settle: 1400 },
  { file: "11-command-center-fa-dark-768.png", path: "/fa", theme: "dark", viewport: [768, 900], fullPage: false, settle: 3800 },
  { file: "12-positions-fa-dark-768.png", path: "/fa/positions", theme: "dark", viewport: [768, 900], fullPage: true, settle: 1200 },
];

mkdirSync(OUT, { recursive: true });

const consoleReport = [];

async function withBrowser(fn) {
  const browser = await playwright.launch({
    executablePath,
    headless: true,
    args: ARGS,
    env,
  });
  try {
    await fn(browser);
  } finally {
    await browser.close().catch(() => {});
  }
}

for (const shot of SHOTS) {
  await withBrowser(async (browser) => {
    const context = await browser.newContext({
      viewport: { width: shot.viewport[0], height: shot.viewport[1] },
      deviceScaleFactor: 1,
      locale: shot.path.startsWith("/en") ? "en-US" : "fa-IR",
    });
    await context.addInitScript((theme) => {
      window.localStorage.setItem("theme", theme);
      try {
        const prefs = JSON.parse(localStorage.getItem("ahos-deck-prefs.v1") ?? "{}");
        prefs.datasetBannerDismissed = true;
        prefs.sceneEnabled = true;
        prefs.sceneView = "room";
        localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify(prefs));
      } catch {}
    }, shot.theme);

    if (shot.prefs) {
      await context.addInitScript((extra) => {
        try {
          const prefs = JSON.parse(localStorage.getItem("ahos-deck-prefs.v1") ?? "{}");
          Object.assign(prefs, extra);
          localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify(prefs));
        } catch {}
      }, shot.prefs);
    }

    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    const networkErrors = [];
    page.on("pageerror", (err) => pageErrors.push(String(err)));
    page.on("console", (msg) => {
      if (msg.type() !== "error") return;
      const text = msg.text();
      // live-market fetches fail inside the egress-restricted sandbox by design —
      // the UI must (and does) degrade to honest NOT_CONNECTED states. Those
      // browser-side resource logs are counted separately from real JS errors.
      if (text.includes("Failed to load resource") || text.includes("net::")) networkErrors.push(text);
      else consoleErrors.push(text);
    });

    try {
      await page.goto(`${BASE}${shot.path}`, { waitUntil: "networkidle", timeout: 45000 });
      await page.waitForTimeout(shot.settle);
      await page.screenshot({ path: `${OUT}${shot.file}`, fullPage: shot.fullPage });
      console.log(`✓ ${shot.file}`);
    } catch (err) {
      console.log(`✗ ${shot.file}: ${err.message}`);
    }

    if (pageErrors.length || consoleErrors.length || networkErrors.length) {
      consoleReport.push({ shot: shot.file, pageErrors, consoleErrors, networkErrors });
    }
    await context.close().catch(() => {});
  });
}

// palette-open evidence shot — keyboard interaction through the real UI
await withBrowser(async (browser) => {
  const context = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  await context.addInitScript(() => {
    window.localStorage.setItem("theme", "dark");
  });
  const page = await context.newPage();
  try {
    await page.goto(`${BASE}/fa`, { waitUntil: "networkidle", timeout: 45000 });
    await page.waitForTimeout(2500);
    await page.keyboard.press("Control+k");
    await page.waitForTimeout(700);
    await page.screenshot({ path: `${OUT}13-command-palette-fa-dark.png`, timeout: 60000 });
    console.log("✓ 13-command-palette-fa-dark.png");

  } catch (err) {
    console.log(`✗ palette shot: ${err.message}`);
  }
  await context.close().catch(() => {});
});


/* ---------------- extra: space view + wide room ---------------- */
await withBrowser(async (browser) => {
  const context2 = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 1, locale: "fa-IR" });
  await context2.addInitScript((theme) => {
    window.localStorage.setItem("theme", theme);
    localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify({ datasetBannerDismissed: true, sceneEnabled: true, sceneView: "space" }));
  }, "dark");
  const page2 = await context2.newPage();
  try {
    await page2.goto(`${BASE}/fa`, { waitUntil: "networkidle", timeout: 45000 });
    await page2.waitForTimeout(5200);
    await page2.screenshot({ path: `${OUT}14-command-center-fa-space.png`, timeout: 60000 });
    console.log("✓ 14-command-center-fa-space.png");
  } catch (err) {
    console.log(`✗ space shot: ${err.message}`);
  }
  await context2.close().catch(() => {});
});

await withBrowser(async (browser) => {
  const context3 = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1, locale: "fa-IR" });
  await context3.addInitScript((theme) => {
    window.localStorage.setItem("theme", theme);
    localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify({ datasetBannerDismissed: true, sceneEnabled: true, sceneView: "room" }));
  }, "dark");
  const page3 = await context3.newPage();
  try {
    await page3.goto(`${BASE}/fa`, { waitUntil: "networkidle", timeout: 45000 });
    await page3.waitForTimeout(6200);
    await page3.screenshot({ path: `${OUT}15-command-room-fa-wide.png`, timeout: 60000 });
    console.log("✓ 15-command-room-fa-wide.png");
  } catch (err) {
    console.log(`✗ wide shot: ${err.message}`);
  }
  await context3.close().catch(() => {});
});

await withBrowser(async (browser) => {
  const context4 = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 1, locale: "fa-IR" });
  await context4.addInitScript((theme) => {
    window.localStorage.setItem("theme", theme);
    localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify({ datasetBannerDismissed: true, sceneEnabled: true, sceneView: "fpv" }));
  }, "dark");
  const page4 = await context4.newPage();
  const fpvProblems = [];
  page4.on("pageerror", (err) => fpvProblems.push(String(err)));
  try {
    await page4.goto(`${BASE}/fa`, { waitUntil: "networkidle", timeout: 45000 });
    await page4.waitForTimeout(5600);
    await page4.screenshot({ path: `${OUT}16-command-room-fa-fpv.png`, timeout: 60000 });
    console.log("✓ 16-command-room-fa-fpv.png");
  } catch (err) {
    console.log(`✗ fpv shot: ${err.message}`);
  }
  if (fpvProblems.length) consoleReport.push({ shot: "16-command-room-fa-fpv.png", pageErrors: fpvProblems, consoleErrors: [], networkErrors: [] });
  await context4.close().catch(() => {});
});

await withBrowser(async (browser) => {
  const context5 = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1, locale: "fa-IR" });
  await context5.addInitScript((theme) => {
    window.localStorage.setItem("theme", theme);
    localStorage.setItem("ahos-deck-prefs.v1", JSON.stringify({ datasetBannerDismissed: true, sceneEnabled: true, sceneView: "room" }));
  }, "dark");
  const page5 = await context5.newPage();
  const panelProblems = [];
  page5.on("pageerror", (err) => panelProblems.push(String(err)));
  try {
    await page5.goto(`${BASE}/fa`, { waitUntil: "networkidle", timeout: 45000 });
    await page5.waitForTimeout(6000);
    const opened = await page5.evaluate(() => {
      const chip = document.querySelector('[data-role-chip="gold"]');
      if (!chip) return false;
      chip.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      return true;
    });
    await page5.waitForTimeout(900);
    await page5.screenshot({ path: `${OUT}17-command-room-fa-workstation-panel.png`, timeout: 60000 });
    console.log(`✓ 17-command-room-fa-workstation-panel.png (chip ${opened ? "clicked" : "MISSING"})`);
  } catch (err) {
    console.log(`✗ panel shot: ${err.message}`);
  }
  if (panelProblems.length) consoleReport.push({ shot: "17-command-room-fa-workstation-panel.png", pageErrors: panelProblems, consoleErrors: [], networkErrors: [] });
  await context5.close().catch(() => {});
});

writeFileSync(`${OUT}console-report.json`, JSON.stringify(consoleReport, null, 2));

const fatalPages = consoleReport.filter((r) => (r.pageErrors?.length ?? 0) + (r.consoleErrors?.length ?? 0) > 0);
console.log(`\nconsole/page errors: ${fatalPages.length === 0 ? "NONE" : fatalPages.length + " pages affected"}`);
console.log(`network resource errors (expected offline sandbox): ${consoleReport.reduce((n, r) => n + (r.networkErrors?.length ?? 0), 0)}`);
