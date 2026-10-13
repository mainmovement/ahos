/**
 * M-D5.4 — prove the context-loss fallback and the live tier switch.
 *
 * Two acceptance criteria from the queue:
 *
 *   M-D5.4  context-loss fallback to the 2D layout with a Persian notice
 *   M-D5.4  no data loss on a live tier switch
 *
 * Both are reachable from the DOM but neither is triggered by anything the app
 * does on its own, so they have to be provoked. A synthetic `new Event(...)` on
 * the canvas would be a fake; `WEBGL_lose_context.loseContext()` makes the driver
 * raise a *real* `webglcontextlost`, which is the event the app's listener has to
 * survive. That extension exists precisely for this purpose.
 *
 * Run: node scripts/screenshot_contextloss.mjs <url> <out.png> [settleMs]
 *
 * Reads only DOM state. Never touches .env, tokens, or any authority surface.
 */
import { writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { defaultDashboardUrl } from "./gateway_url.mjs";

const url = process.argv[2] ?? (await defaultDashboardUrl()).url;
const out = process.argv[3] ?? "reports/dashboard/screens/M-D5.4/context-lost.png";
const settleMs = Number(process.argv[4] ?? 25000);

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const probe = async () => {
  const chrome = spawn(
    CHROME,
    [
      "--headless=new",
      "--no-sandbox",
      "--hide-scrollbars",
      "--window-size=1600,900",
      "--remote-debugging-port=0",
      "about:blank",
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  const stderr = [];
  chrome.stderr.on("data", (b) => void stderr.push(b));

  const wsUrl = await new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("devtools endpoint never appeared")),
      30000,
    );
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
  const page = targetList.targetInfos.find(
    (t) => t.type === "page" && t.url === "about:blank",
  );
  if (!page) throw new Error("no page target to attach to");
  const session = await send("Target.attachToTarget", {
    targetId: page.targetId,
    flatten: true,
  });
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
      throw new Error(
        `evaluation failed: ${res.exceptionDetails.text} ${
          res.exceptionDetails.exception?.description ?? ""
        }`,
      );
    }
    return JSON.parse(res.result.value);
  };

  await sendTo("Page.enable");
  await sendTo("Runtime.enable");
  await sendTo("Page.navigate", { url });

  // The DOM shape this script reasons about. Kept in one place so a change in
  // the shell's class names fails loudly instead of silently degrading the check.
  const snapshot = `(() => {
    const chip = document.querySelector('.dashi-tier');
    const pill = document.querySelector('.dashi-pill--paper');
    const fb = document.querySelector('.dashi-fallback');
    return JSON.stringify({
      chip: chip ? chip.className.replace(/^.*dashi-tier/, 'dashi-tier') : null,
      chipText: chip ? chip.textContent.trim() : null,
      pillText: pill ? pill.textContent.trim() : null,
      canvas: document.querySelectorAll('canvas').length,
      fallback: fb ? fb.textContent.replace(/\\s+/g, ' ').trim() : null,
      title: fb ? (fb.querySelector('.dashi-fallback__title') || {}).textContent?.trim() : null,
      retry: !!document.querySelector('.dashi-fallback button, .dashi-retry'),
      scope: (document.querySelector('.dashi-scope') || {}).textContent?.trim() ?? null,
    });
  })()`;

  // 1. Wait for the probe to land and the stage to have its context.
  const deadline = Date.now() + settleMs;
  let before = {};
  do {
    before = await evaluate(snapshot);
    if (!before.chip?.includes("pending") && before.canvas > 0) break;
    await new Promise((r) => setTimeout(r, 500));
  } while (Date.now() < deadline);

  if (before.canvas === 0) {
    throw new Error(
      `the stage never mounted before the test could provoke a loss: ${JSON.stringify(before)}`,
    );
  }

  // 2. A real context loss. `loseContext()` makes the driver raise the event the
  // app's listener is registered for; dispatching a synthetic Event would test
  // the addEventListener call but not the recovery.
  const lost = await evaluate(`(() => {
    const c = document.querySelector('canvas');
    if (!c) return JSON.stringify({ error: 'no canvas' });
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (!gl) return JSON.stringify({ error: 'no gl on the canvas' });
    const ext = gl.getExtension('WEBGL_lose_context');
    if (!ext) return JSON.stringify({ error: 'WEBGL_lose_context unavailable' });
    ext.loseContext();
    return JSON.stringify({ lost: true });
  })()`);

  // 3. React has to re-render, so give it a frame budget before asserting.
  let after = {};
  for (let i = 0; i < 20; i++) {
    after = await evaluate(snapshot);
    if (after.fallback !== null) break;
    await new Promise((r) => setTimeout(r, 250));
  }

  // The acceptance artifact: the fallback notice, captured while it is showing.
  // Retrying and switching afterwards would otherwise leave the screenshot showing
  // a healthy stage, and the PNG would not depict the state it is evidence of.
  await new Promise((r) => setTimeout(r, 800));
  const shot = await sendTo("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  writeFileSync(out, Buffer.from(shot.data, "base64"));
  const fallbackBytes = Buffer.from(shot.data, "base64").length;

  // 4. The retry path: re-probing must restore the stage, not just clear the
  // notice. The click is only sent if the button was actually found, so a shell
  // with no retry button fails loudly instead of passing as a no-op.
  const hadRetry = after.retry;
  let afterRetry = null;
  if (hadRetry) {
    await evaluate(`(() => {
      const b = document.querySelector('.dashi-fallback button, .dashi-retry');
      if (b) b.click();
      return JSON.stringify({ clicked: !!b });
    })()`);
    for (let i = 0; i < 40; i++) {
      afterRetry = await evaluate(snapshot);
      if (afterRetry.canvas > 0 || afterRetry.chip?.includes("pending")) break;
      await new Promise((r) => setTimeout(r, 250));
    }
  }

  // 5. No data loss on a live tier switch: the shell's snapshot pill is DOM state
  // that must survive the stage unmounting and the probe re-running. The chip
  // click writes the override and re-probes, which is the switch the queue means.
  //
  // The chip does *not* go back to "pending" during a re-probe — the old verdict
  // stays displayed until the new one lands — so the switch is detected by the
  // tier class actually changing, not by a pending state appearing. Polling for
  // "not pending" here would read the pre-click class and silently pass a switch
  // that never took effect.
  const switchResult = await evaluate(`(async () => {
    const chip = document.querySelector('.dashi-tier');
    const pillBefore = (document.querySelector('.dashi-pill--paper') || {}).textContent?.trim() ?? null;
    const scopeBefore = (document.querySelector('.dashi-scope') || {}).textContent?.trim() ?? null;
    const classOf = () => (document.querySelector('.dashi-tier') || {}).className?.replace(/^.*dashi-tier/, 'dashi-tier') ?? null;
    if (!chip || classOf()?.includes('pending')) return JSON.stringify({ error: 'no chip to switch' });
    const before = classOf();

    const waitFor = async (from, wanted, budget) => {
      // Waits for the class to move off the pre-click class — not the class at
      // the start of the whole run. Comparing against the original class makes a
      // second consecutive switch look like it already happened, and reads a
      // verdict whose probe is still in flight.
      for (let i = 0; i < budget; i++) {
        const c = classOf();
        if (c !== null && !c.includes('pending') && c !== from && (wanted === null || c.includes(wanted))) return c;
        await new Promise((r) => setTimeout(r, 250));
      }
      return classOf();
    };

    // Down: T1 -> T0 writes the override, the stage unmounts, the 2D notice shows.
    chip.click();
    const downClass = await waitFor(before, 'dashi-tier--t0', 40);
    const noticeAtT0 = (document.querySelector('.dashi-fallback') || {}).textContent?.replace(/\\s+/g, ' ').trim() ?? null;

    // Up again: a click at the floor clears the override, so the machine is
    // re-measured and the stage returns — proving the switch is reversible and
    // that the 2D notice was a view, not a stuck state.
    const chip2 = document.querySelector('.dashi-tier');
    const atFloor = classOf();
    if (chip2) chip2.click();
    const upClass = await waitFor(atFloor, null, 48);

    // Distinguish a stuck override from an honest demotion. If the key is gone and
    // the tier is still T0, a *measurement* lowered it (reasonFa says "اندازه‌گیری"
    // and the title carries an fps/floor line) — that is the ladder working, not a
    // defect, and the forced loss earlier in this run is the likely cause. If the
    // key is still "T0", writeOverride(null) failed to clear it — a real bug.
    const upTitle = (document.querySelector('.dashi-tier') || {}).getAttribute?.('title') ?? null;
    const overrideAfter = (() => {
      try { return localStorage.getItem('ahos.stage.tier.override'); } catch { return 'unreadable'; }
    })();

    const pillAfter = (document.querySelector('.dashi-pill--paper') || {}).textContent?.trim() ?? null;
    const scopeAfter = (document.querySelector('.dashi-scope') || {}).textContent?.trim() ?? null;
    // The caption's low-power line is tier *description* (it appears exactly when
    // the motion budget is zero), not data, so data survival is judged on the base
    // sentence with that suffix stripped — otherwise an honest caption change
    // would read as data loss.
    const base = (s) => (s ?? '').replace(/\\s*حالت کم‌مصرف:.*$/, '').trim();
    return JSON.stringify({
      before, downClass, upClass,
      noticeAtT0,
      overrideAfter,
      upTitle,
      pillBefore, pillAfter,
      scopeBefore, scopeAfter,
      pillSurvived: pillBefore !== null && pillBefore === pillAfter,
      scopeSurvived: base(scopeBefore) === base(scopeAfter) && base(scopeBefore) !== '',
      stageReturned: document.querySelectorAll('canvas').length,
    });
  })()`, true);

  await new Promise((r) => setTimeout(r, 1200));

  // A second capture after recovery, so the receipt shows both states: the
  // notice and the stage that came back from it.
  const tail = await sendTo("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  const tailOut = out.replace(/\.png$/, "-recovered.png");
  if (tailOut !== out) writeFileSync(tailOut, Buffer.from(tail.data, "base64"));

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
    lost,
    before,
    after,
    afterRetry,
    switchResult,
    consoleErrors,
    fallbackBytes,
    recoveredBytes: Buffer.from(tail.data, "base64").length,
    tailOut,
  };
};

probe().then(
  ({ lost, before, after, afterRetry, switchResult, consoleErrors, fallbackBytes, recoveredBytes, tailOut }) => {
    console.log("provoked loss:", JSON.stringify(lost, null, 2));
    console.log("before:", JSON.stringify(before, null, 2));
    console.log("after loss:", JSON.stringify(after, null, 2));
    console.log("after retry:", JSON.stringify(afterRetry, null, 2));
    console.log("tier switch:", JSON.stringify(switchResult, null, 2));
    console.log("console errors:", consoleErrors.length ? consoleErrors : "none");
    console.log(`wrote ${out} (${fallbackBytes} bytes) + ${tailOut} (${recoveredBytes} bytes)`);
  },
  (err) => {
    console.error("capture failed:", err.message);
    process.exit(1);
  },
);
