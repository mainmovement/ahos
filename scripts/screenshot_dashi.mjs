/**
 * M-D5.2 — capture the Dashi shell after the stage actually mounts.
 *
 * `chrome --headless --screenshot` fires at the load event, which is before the
 * `ssr:false` dynamic import resolves and before `probeQuality()` lands, so it
 * photographs the loading placeholder every time. Driving Chrome over the
 * DevTools protocol instead lets this script wait for the real signals — the
 * tier chip leaving "pending" and a <canvas> appearing — and then capture.
 *
 * Run: node scripts/screenshot_dashi.mjs <url> <out.png> [settleMs] [overrideTier]
 *
 * `overrideTier` (T0..T3) writes the app's own manual override into localStorage
 * before the page boots, so the capture can show a tier this machine did not
 * measure. It uses the same `writeOverride` path the Tier Panel uses — the verdict
 * still runs through `resolveTier`, so a limit this machine really has still caps
 * it and the chip's title says the pick was lowered. Nothing is fabricated: the
 * capture records the verdict it got, not the one that was asked for.
 *
 * Reads only DOM state. Never touches .env, tokens, or any authority surface.
 */
import { writeFileSync } from "node:fs";
import { spawn } from "node:child_process";

const url = process.argv[2] ?? "http://127.0.0.1:3199/";
const out = process.argv[3] ?? "reports/dashboard/screens/M-D5.2/stage.png";
const settleMs = Number(process.argv[4] ?? 20000);
const overrideTier = process.argv[5] ?? null;
const OVERRIDES = ["T0", "T1", "T2", "T3"];
if (overrideTier !== null && !OVERRIDES.includes(overrideTier)) {
  console.error(`overrideTier must be one of ${OVERRIDES.join("/")}, got ${overrideTier}`);
  process.exit(2);
}

const CHROME =
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

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

  // Wait for DevTools to print its listening URL.
  const wsUrl = await new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("devtools endpoint never appeared")),
      30000,
    );
    chrome.stderr.on("data", function onData(buf) {
      const line = buf.toString();
      const hit = /DevTools listening on (ws:\/\/\S+)/.exec(line);
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

  // Attach to the page target, not the browser endpoint: domain commands like
  // Page.* only route through a session, and a bare browser-level socket
  // answers them with "wasn't found".
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

  await sendTo("Page.enable");
  await sendTo("Runtime.enable");

  // Instrument getContext *before* the app boots, so what detectBackend sees at
  // t=0 is recorded rather than inferred from a later, settled page.
  await sendTo("Page.addScriptToEvaluateOnNewDocument", {
    source: `
      window.__glTrace = [];
      const proto = HTMLCanvasElement.prototype;
      const orig = proto.getContext;
      proto.getContext = function (type, attrs) {
        let gl = null;
        try { gl = orig.call(this, type, attrs); } catch (e) { gl = "threw:" + e.message; }
        window.__glTrace.push({
          type, attrs: attrs ? JSON.stringify(attrs) : null,
          result: gl && gl.getParameter ? gl.getParameter(gl.VERSION) : String(gl),
          when: Math.round(performance.now()),
        });
        return gl && gl.getParameter ? gl : (gl && gl.startsWith ? null : gl);
      };
      ${overrideTier !== null
        ? `try { localStorage.setItem("ahos.stage.tier.override", ${JSON.stringify(overrideTier)}); } catch {}`
        : ""}
    `,
  });
  await sendTo("Page.navigate", { url });

  // Poll the DOM until the probe has landed (or the budget runs out).
  const poll = `(() => {
    const chip = document.querySelector('.dashi-tier');
    const pending = chip ? chip.className.includes('pending') : true;
    const badge = (() => {
      const b = document.querySelector('.truth-badge');
      if (!b) return null;
      const label = b.querySelector('.truth-badge__label');
      const swatch = b.querySelector('.truth-badge__fill');
      const cs = getComputedStyle(b);
      const cl = label ? getComputedStyle(label) : null;
      const cw = swatch ? getComputedStyle(swatch) : null;
      return JSON.stringify({
        root: cs.backgroundImage === 'none' ? 'none' : 'PATTERN',
        label: !cl ? null : cl.backgroundImage === 'none' ? 'none' : 'PATTERN',
        swatch: !cw ? null : cw.backgroundImage === 'none' ? 'none' : 'PATTERN',
        text: label ? label.textContent.trim() : null,
      });
    })();
    return JSON.stringify({
      chip: chip ? chip.className.replace(/^.*dashi-tier/, 'dashi-tier') : null,
      text: chip ? chip.textContent.trim() : null,
      title: chip ? chip.getAttribute('title') : null,
      canvas: document.querySelectorAll('canvas').length,
      pill: (document.querySelector('.dashi-pill--paper') || {}).textContent?.trim() ?? null,
      badge,
      // StageLazy shows its own loading line while the three.js chunk parses;
      // that is "not ready yet", and distinguishes from the 2D dashi-fallback.
      stageLoading: !!document.querySelector('.stage-fallback'),
      fallback: !document.querySelector('.dashi-fallback') ? null
        : document.querySelector('.dashi-fallback')?.textContent?.replace(/\\s+/g,' ').trim(),
    });
  })()`;

  const deadline = Date.now() + settleMs;
  let state = {};
  do {
    state = JSON.parse(
      (
        await sendTo("Runtime.evaluate", {
          expression: poll,
          returnByValue: true,
        })
      ).result.value,
    );
    // The chip landing is not enough: the stage still has to fetch and parse the
    // three.js chunk, and until it does the owner sees a loading line rather than
    // the scene. Wait for the canvas the verdict allows, or for the 2D fallback
    // when it does not allow one.
    if (
      !state.chip?.includes("pending") &&
      (state.canvas > 0 || state.fallback !== null)
    ) break;
    await new Promise((r) => setTimeout(r, 500));
  } while (Date.now() < deadline);

  // Let the compositor draw whatever the verdict allows.
  await new Promise((r) => setTimeout(r, 1500));

  // What this browser can actually drive — recorded so the verdict the chip
  // shows is known to be real rather than an artifact of detection.
  const glCheck = `(() => {
    const out = {};
    const c1 = document.createElement('canvas');
    const g1 = c1.getContext('webgl2');
    out.webgl2 = g1 ? g1.getParameter(g1.VERSION) : null;
    const c2 = document.createElement('canvas');
    const g2 = c2.getContext('webgl');
    out.webgl1 = g2 ? g2.getParameter(g2.VERSION) : null;
    if (g2) {
      const ext = g2.getExtension('WEBGL_debug_renderer_info');
      out.renderer = ext ? g2.getParameter(ext.UNMASKED_RENDERER_WEBGL) : '(ext blocked)';
    }
    out.cores = navigator.hardwareConcurrency;
    out.mem = navigator.deviceMemory;
    return JSON.stringify(out);
  })()`;
  let capability = null;
  try {
    capability = JSON.parse(
      (
        await sendTo("Runtime.evaluate", {
          expression: glCheck,
          returnByValue: true,
        })
      ).result.value,
    );
  } catch (e) {
    capability = { probeError: e.message };
  }

  // The app's own fill-rate probe, replicated so the verdict's number is printed
  // alongside it. This is what caught the two real defects: a T0 verdict on a
  // machine that reports 60 fps (the probe had been racing the bundle parse),
  // and an "Intel HD" part labelled as a discrete card.
  const frameCheck = `(async () => {
    const PASSES = 2000;
    const canvas = document.createElement('canvas');
    canvas.width = 512; canvas.height = 512;
    const gl = canvas.getContext('webgl2');
    if (!gl) return JSON.stringify({ error: 'no webgl2' });
    const cell = Math.ceil(Math.sqrt(PASSES));
    const cols = Math.max(1, Math.floor(512 / cell));
    return new Promise((resolve) => {
      const start = performance.now();
      let frames = 0;
      const pass = (now) => {
        if (now - start >= 2000) {
          const el = now - start;
          const mean = frames > 0 ? el / frames : null;
          resolve(JSON.stringify({
            frames,
            fps: mean && mean > 0 ? Math.round(1000 / mean) : null,
          }));
          return;
        }
        for (let i = 0; i < PASSES; i++) {
          const x = (i % cols) * cell;
          const y = Math.floor(i / cols) * cell;
          gl.enable(gl.SCISSOR_TEST);
          gl.scissor(x, y, cell, cell);
          gl.clearColor(0, 0, 0, 1);
          gl.clear(gl.COLOR_BUFFER_BIT);
        }
        gl.disable(gl.SCISSOR_TEST);
        frames++;
        requestAnimationFrame(pass);
      };
      requestAnimationFrame(pass);
    });
  })()`;
  let frameProbe = null;
  try {
    frameProbe = JSON.parse(
      (
        await sendTo("Runtime.evaluate", {
          expression: frameCheck,
          awaitPromise: true,
          returnByValue: true,
        })
      ).result.value,
    );
  } catch (e) {
    frameProbe = { probeError: e.message };
  }

  // The order in which contexts were requested, with the attributes each one
  // asked for — this is what reveals whether detectBackend lost a race.
  let glTrace = null;
  try {
    glTrace = JSON.parse(
      (
        await sendTo("Runtime.evaluate", {
          expression: "JSON.stringify(window.__glTrace ?? [])",
          returnByValue: true,
        })
      ).result.value,
    );
  } catch (e) {
    glTrace = { probeError: e.message };
  }

  const shot = await sendTo("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
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
  return { state, capability, frameProbe, glTrace, consoleErrors, bytes: Buffer.from(shot.data, "base64").length };
};

probe().then(
  ({ state, capability, frameProbe, glTrace, consoleErrors, bytes }) => {
    console.log("state:", JSON.stringify(state, null, 2));
    console.log("capability:", JSON.stringify(capability, null, 2));
    console.log("frameProbe:", JSON.stringify(frameProbe, null, 2));
    console.log("glTrace:", JSON.stringify(glTrace, null, 2));
    console.log("console errors:", consoleErrors.length ? consoleErrors : "none");
    console.log(`wrote ${out} (${bytes} bytes)`);
  },
  (err) => {
    console.error("capture failed:", err.message);
    process.exit(1);
  },
);
