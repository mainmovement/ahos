// B11 screenshots + DOM checks via Chrome DevTools protocol. Read-only: loads pages, captures PNG, evaluates DOM metrics.
import { mkdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
const BASE = process.argv[2] ?? "http://127.0.0.1:3290";
const OUT = process.argv[3] ?? "reports/dashboard/screens/B11";
const PROFILE = process.argv[4];
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PAGES = ["trade-venue", "oil-gold"];
const STATES = { calm: "", details: "?details=1" };
mkdirSync(OUT, { recursive: true });
const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=9334", `--user-data-dir=${PROFILE}`, "--window-size=1600,900", "--hide-scrollbars", "--no-first-run", "--disable-gpu", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ver = null;
for (let i = 0; i < 40 && !ver; i++) { try { ver = await (await fetch("http://127.0.0.1:9334/json/version")).json(); } catch { await sleep(500); } }
if (!ver) { chrome.kill(); throw new Error("chrome devtools not reachable"); }
const tab = await (await fetch("http://127.0.0.1:9334/json/new?about:blank", { method: "PUT" })).json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
const METRICS = `(() => {
  const root = document.querySelector('[data-mb-page]') || document.querySelector('[data-real-paper]');
  if (!root) return { ok: false, title: document.title, body: document.body.innerText.slice(0, 200) };
  let minFont = 99; for (const el of root.querySelectorAll('*')) { if (!el.childNodes.length) continue; const has = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!has) continue; const f = parseFloat(getComputedStyle(el).fontSize); if (f < minFont) minFont = f; }
  const q = (s) => root.querySelectorAll(s).length;
  const r = root.getBoundingClientRect();
  return { ok: true, real: { paper: q('[data-real-paper]'), kpis: q('[data-real-kpis]'), position: q('[data-real-position]'), live: q('[data-real-live]'), replay: q('[data-real-replay]'), replayRows: q('[data-real-replay-row]'), tradesRows: q('[data-real-trades-row]'), imgs: q('[data-real-equity] img'), imgsLoaded: [...document.querySelectorAll('[data-real-equity] img')].filter(i => i.complete && i.naturalWidth > 0).length, controls: q('[data-real-paper] button, [data-real-paper] form, [data-real-paper] input, [data-real-oilgold] button, [data-real-oilgold] input'), paperOnly: /PAPER_ONLY/.test(document.body.innerText), notLive: /REPLAY_NOT_LIVE/.test(document.body.innerText), noEdge: /no proven edge yet/.test(document.body.innerText), demoNote: !!document.querySelector('[data-real-demo-note]'), realText: (document.querySelector('[data-real-paper],[data-real-oilgold]')?.innerText ?? '').replace(/\\s+/g, ' ').slice(0, 400) }, page: root.dataset.mbPage, h1: root.querySelector('h1')?.textContent, dir: root.getAttribute('dir'),
    source: root.querySelector('[data-mb-source]')?.innerText, chips: [...root.querySelectorAll('.tv-chip, [class*="truth-chip"], [data-status]')].slice(0, 4).map(e => e.textContent.trim()).filter(Boolean),
    highlights: root.querySelector('[data-mb-highlights]')?.dataset.mbHighlights ?? null, violationBar: q('[class*="violation"]') > 0, demoRibbon: /DEMO/.test(root.innerText),
    buttons: q('button:not([aria-expanded]), input, form'), docOverflowX: document.documentElement.scrollWidth > innerWidth, rootWidth: Math.round(r.width), rootHeight: Math.round(r.height), minFontPx: minFont,
    stateBlock: q('[class*="state-block"], [class*="StateBlock"]') > 0, text: root.innerText.replace(/\\s+/g, ' ').slice(0, 260) };
})()`;
const results = {};
for (const p of PAGES) for (const [s, qs] of Object.entries(STATES)) {
  await send("Page.navigate", { url: `${BASE}/arena/${p}${qs}` });
  let m = null;
  for (let i = 0; i < 60; i++) { await sleep(1000); const r = await send("Runtime.evaluate", { expression: METRICS, returnByValue: true }); m = r.result?.result?.value; if (m?.ok) break; }
  await sleep(1500);
  m = (await send("Runtime.evaluate", { expression: METRICS, returnByValue: true })).result?.result?.value ?? m;
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const file = `${OUT}/b14_${p}_${s}.png`;
  writeFileSync(file, Buffer.from(shot.result.data, "base64"));
  results[`${p}/${s}`] = { file, ...m };
  console.log(p, s, m?.ok ? "ok" : "NOT MOUNTED");
}
writeFileSync(`${OUT}/b14_dom_checks.json`, JSON.stringify(results, null, 2));
ws.close(); chrome.kill();
process.exit(0);