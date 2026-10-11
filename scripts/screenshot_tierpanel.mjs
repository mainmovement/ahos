/**
 * M-D5.5 — capture the Hardware Tier Panel.
 *
 * The panel is behind the topbar's «سخت‌افزار» toggle and reads `/api/idea_shelf`,
 * which is gated like every other dashboard route. A headless browser holds no
 * session, so that fetch returns 401 and the panel renders its *error* branch —
 * the same reason the topbar pill already reads UNKNOWN in these captures. This
 * script records the raw status the browser received, so the capture is explicit
 * about which branch rendered and why, rather than looking like the missing-file
 * branch when it was not.
 *
 * Run: node scripts/screenshot_tierpanel.mjs <url> <out.png> [settleMs]
 *
 * Reads only DOM state. Never touches .env, tokens, or any authority surface.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";

const url = process.argv[2] ?? "http://127.0.0.1:3199/";
const out = process.argv[3] ?? "reports/dashboard/screens/M-D5.5/tier-panel.png";
const settleMs = Number(process.argv[4] ?? 25000);

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
/** Per-run throwaway profile, under the OS temp dir rather than the repo. */
const ISOLATED_PROFILE = `${process.env.TEMP ?? process.env.TMP ?? "/tmp"}/ahos-cdp-${process.pid}`;

const probe = async () => {
  mkdirSync(ISOLATED_PROFILE, { recursive: true });
  const chrome = spawn(
    CHROME,
    [
      "--headless=new",
      "--no-sandbox",
      "--hide-scrollbars",
      "--window-size=1600,900",
      // An isolated profile: the scripts share nothing with the owner's Chrome or
      // with each other, so a crashed earlier run cannot leave a profile lock that
      // makes this one wait on a DevTools endpoint that never comes.
      `--user-data-dir=${ISOLATED_PROFILE}`,
      "--remote-debugging-port=0",
      "about:blank",
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  const stderr = [];
  chrome.stderr.on("data", (b) => void stderr.push(b));

  const wsUrl = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("devtools endpoint never appeared")), 30000);
    chrome.stderr.on("data", function onData(buf) {
      const hit = /DevTools listening on (ws:\/\/\S+)/.exec(buf.toString());
      if (hit) {
        clearTimeout(timer);
        chrome.stderr.off("data", onData);
        resolve(hit[1]);
      }
    });
  });

  const ws = new WebSocket(wsUrl);
  await new Promise((r, e) => {
    ws.onopen = r;
    ws.onerror = e;
  });

  let id = 0;
  const pending = new Map();
  const events = [];
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) {
      events.push(msg);
    }
  };
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const mid = ++id;
      pending.set(mid, { resolve, reject });
      ws.send(JSON.stringify({ id: mid, method, params }));
    });

  const targetList = await send("Target.getTargets");
  const page = targetList.targetInfos.find((t) => t.type === "page" && t.url === "about:blank");
  if (!page) throw new Error("no page target to attach to");
  const session = await send("Target.attachToTarget", { targetId: page.targetId, flatten: true });
  const sessionId = session.sessionId;

  const sendTo = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const mid = ++id;
      pending.set(mid, { resolve, reject });
      ws.send(JSON.stringify({ id: mid, sessionId, method, params }));
    });
  const evaluate = async (expression, awaitPromise = false) => {
    const res = await sendTo("Runtime.evaluate", {
      expression,
      awaitPromise,
      returnByValue: true,
    });
    if (res.exceptionDetails) {
      throw new Error(`evaluation failed: ${res.exceptionDetails.text}`);
    }
    return JSON.parse(res.result.value);
  };

  await sendTo("Page.enable");
  await sendTo("Runtime.enable");
  await sendTo("Page.navigate", { url });

  // Wait for the probe to land and the stage to mount before opening the panel.
  const state = `(() => {
    const chip = document.querySelector('.dashi-tier');
    return JSON.stringify({
      chip: chip ? chip.className.replace(/^.*dashi-tier/, 'dashi-tier') : null,
      canvas: document.querySelectorAll('canvas').length,
      panel: !!document.querySelector('.tier-panel'),
      toggle: !!document.querySelector('.dashi-panel-toggle'),
    });
  })()`;
  const deadline = Date.now() + settleMs;
  let ready = {};
  do {
    ready = await evaluate(state);
    if (!ready.chip?.includes("pending") && ready.canvas > 0) break;
    await new Promise((r) => setTimeout(r, 500));
  } while (Date.now() < deadline);

  // Open the panel. The capture must be taken with it showing, and the toggle is
  // the only way in — clicking anything else would leave the capture panel-less.
  await evaluate(`(() => {
    const b = document.querySelector('.dashi-panel-toggle');
    if (b) b.click();
    return JSON.stringify({ clicked: !!b });
  })()`);

  // The panel's own fetch needs a moment; poll until its shelf section settles
  // out of the loading line.
  const panelState = `(() => {
    const p = document.querySelector('.tier-panel');
    if (!p) return JSON.stringify({ error: 'no .tier-panel in the DOM' });
    return JSON.stringify({
      title: (p.querySelector('.tier-panel__title') || {}).textContent?.trim() ?? null,
      rows: [...p.querySelectorAll('.tier-panel__row')].map((r) =>
        r.textContent.replace(/\\s+/g, ' ').trim()),
      reason: (p.querySelector('.tier-panel__reason') || {}).textContent?.trim() ?? null,
      ideas: [...p.querySelectorAll('.tier-panel__idea-title')].map((e) => e.textContent.trim()),
      unknown: [...p.querySelectorAll('.truth-badge--unknown')].length,
      footnote: (p.querySelector('.tier-panel__footnote') || {}).textContent?.trim() ?? null,
      shelfLine: (p.querySelector('.tier-panel__muted') || {}).textContent?.trim() ?? null,
      pending: (p.querySelector('.tier-panel__pending') || {}).textContent?.trim() ?? null,
    });
  })()`;
  let panel = {};
  for (let i = 0; i < 20; i++) {
    panel = await evaluate(panelState);
    if (!panel.pending) break;
    await new Promise((r) => setTimeout(r, 400));
  }

  // What the browser actually received from the route, so the capture is honest
  // about which of the panel's branches rendered and why.
  const apiResult = await evaluate(`(async () => {
    try {
      const res = await fetch('/api/idea_shelf', { credentials: 'include' });
      const body = await res.text();
      return JSON.stringify({ status: res.status, body: body.slice(0, 200) });
    } catch (e) {
      return JSON.stringify({ status: 'threw', body: String(e.message) });
    }
  })()`, true);

  // Whether the registry exists on disk, as the server sees it — the branch the
  // missing-file test covers, reported from the browser origin rather than the
  // filesystem so the script stays read-only on DOM state.
  const indexResult = await evaluate(`(async () => {
    try {
      const res = await fetch('/idea_shelf.json');
      return JSON.stringify({ status: res.status });
    } catch (e) {
      return JSON.stringify({ status: 'threw' });
    }
  })()`, true);

  await new Promise((r) => setTimeout(r, 1000));
  const shot = await sendTo("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(out, Buffer.from(shot.data, "base64"));

  const consoleErrors = events
    .filter(
      (e) =>
        e.method === "Runtime.exceptionThrown" ||
        (e.method === "Runtime.consoleAPICalled" && e.params.type === "error"),
    )
    .map((e) =>
      e.method === "Runtime.exceptionThrown"
        ? `exception: ${e.params.exceptionDetails.text}`
        : `console.error: ${e.params.args.map((a) => a.value ?? a.description).join(" ")}`,
    );

  ws.close();
  chrome.kill();
  return {
    ready,
    panel,
    apiResult,
    indexResult,
    consoleErrors,
    bytes: Buffer.from(shot.data, "base64").length,
  };
};

probe().then(
  ({ ready, panel, apiResult, indexResult, consoleErrors, bytes }) => {
    console.log("stage:", JSON.stringify(ready, null, 2));
    console.log("panel:", JSON.stringify(panel, null, 2));
    console.log("api /api/idea_shelf:", JSON.stringify(apiResult, null, 2));
    console.log("public /idea_shelf.json:", JSON.stringify(indexResult, null, 2));
    console.log("console errors:", consoleErrors.length ? consoleErrors : "none");
    console.log(`wrote ${out} (${bytes} bytes)`);
  },
  (err) => {
    console.error("capture failed:", err.message);
    process.exit(1);
  },
);
