# M-D2.1 — the launcher's boot URL, its health probe and the app window all pointed at a port nothing was listening on

- Date (Tehran): 2026-10-14 · Step: M-D2.1, SOLTAN NOTE 2026-10-13 21:20 item 1:
  *"fix dashboard bootstrap URL port 3199 vs dev server 3000 so the browser opens
  the 3D dashboard."*
- Follows M-D1.1 (the desktop icon that opened nothing). Both are the same
  failure from two ends: M-D1.1 was a window that never appeared; M-D2.1 is a
  window that would have appeared pointed at a dead address.

## The defect

Two facts had drifted apart and nothing reconciled them:

1. A previous session in this repo hand-started `next dev -p 3199`. That was the
   only live dashboard.
2. The launcher's `gateway_selected.json` advertised port **3000** — the port the
   last launcher start had *asked* for, whose process was already dead.

Every downstream consumer reads the selection record: `dashboard_url()`, the
gateway health probe, the boot URL the app window is opened at. So the owner's
window would open at `http://127.0.0.1:3000` with nothing on it, and a gateway
that was genuinely serving would probe UNHEALTHY forever — the probe asks the
address the record names, not the address Next bound.

The trap underneath: `next dev` **silently walks to a free port** when the one it
was asked for is held by another listener. It does not fail, and nothing in our
stack is told. 3199 was not even in the candidate list `(3000, 3500)` — it exists
only because a session typed it.

## What changed

| File | Change |
|---|---|
| `launcher/orchestrator.py` | new `_reconcile_gateway_port()`: the *only* place the port Next actually bound is published is the `Local:` line it prints once booting finishes (`- Local:  http://127.0.0.1:3199`). The health-wait loop reads it back before every probe and, when it differs from the port we asked for, rewrites the live `self.gateway`, `gateway_selected.json` **and** the pid record — which is exactly what the probe, `dashboard_url()` and the window-open all read. The scan starts at the pid record's `log_offset` (captured at spawn, the same way the telegram marker offset already was) so a *previous* boot's `Local:` line is never mistaken for this one's. |
| `launcher/orchestrator.py` | gateway spawn now records `log_offset` into the pid record. |
| `tests/test_launcher_orchestrator.py` | `TestGatewayPortReconcile`, 5 cases: adopt the bound port end to end (selection + pid record + `dashboard_url()`), a matching port is a no-op, no `Local:` line yet is not an error, an earlier boot's line is not adopted, a missing log is not an error. |

`dev` and `prod` modes are both covered by the same read-back — both print the
`Local:` line.

## Verification — end to end, launcher-owned

The stray hand-started tree (pid 6640 → 7920) was stopped; the decision and its
blast-radius reasoning are in `DECISIONS_LOG.md` (2026-10-14). Then one clean
`.venv/Scripts/python.exe -m launcher start`:

| Check | Reading |
|---|---|
| gateway pid record | `pid 11420`, `cmd ...\next dev --hostname 127.0.0.1` — matches a **live** process, so the launcher owns the tree it spawned |
| `gateway_selected.json` | port **3000** |
| port 3000 | `Test-NetConnection` → `True`; `curl /` → **HTTP 200**, 57 981 B containing `ahos-disc`, `ahos-gold`, `ahos-status-unknown` — the AHOS shell markup, at the address the record names |
| gateway log | `- Local:  http://127.0.0.1:3000` — the port Next bound is the port we asked for, so the reconcile is the intended no-op |
| launcher log | `2026-10-14T06:24:21 app_window: opened via chrome` |
| `overall` | `DEGRADED` — the Postgres backend is unavailable on this host (pglite), a pre-existing host condition, unrelated to this fix |

**Screenshot:** `app_window.png` (1536×864, panel-native — this host's primary
screen is not 1080p) — 9 875 distinct sampled colours, 26.3% deep-navy dark,
0.20% gold-family and 0.64% cyan-family pixels, i.e. the dark theme and its
holographic accents rendered rather than a blank or a load placeholder. For
reference the M-D1.1 blank was 447 distinct colours. `side_by_side.png` puts the
capture next to `owner_reference/01_dashboard_target.jpg`.

Full orchestrator suite: **132 passed, 1 skipped** (342 s).

## Honest self-score — and why the visual gate is not claimable here

The mandatory gate wants a 0–10 on layout match / richness / polish / real data /
no visual bugs, with nothing under 8. **I am not scoring this capture at 8+**, and
the reason is evidence, not modesty:

- This agent cannot view images. The pixel statistics above prove a render
  happened; they do not prove it looks like the target.
- **9.3% of the capture is near-white** (123 339 px) in a dark-theme app, which I
  cannot explain from the served markup — possibly screen-level clutter outside
  the app window, possibly an unpainted region while WebGL initialised. A capture
  driven over the DevTools protocol (the `screenshot_dashi.mjs` path) waiting on
  the stage's own readiness signals is the faithful capture; the full-screen
  `CopyFromScreen` capture is the honest fallback this step used.
- The layout itself is the already-committed `a5e9f8a` template-first overview;
  this step changed no component, so any layout score belongs to that commit, not
  this one.

What *is* claimable, and is what the binding note asked for: **the launcher-owned
stack serves the dashboard at the URL the window is opened at, and the record,
the probe, the boot URL and the window can no longer disagree about the port.**

## Not done, carried forward

- **`next build` fails and the orchestrator degrades to `dev`** (`ساخت نسخهٔ
  تولیدی ناموفق بود؛ حالت توسعه (dev) استفاده می‌شود`). The degradation is by
  design and the dashboard was served, but the failure detail is currently
  discarded by `_gateway_mode` (`ok, _tail` — the tail is never recorded), so the
  cause is not yet known. Diagnosing it is the next step; a desktop app should
  ship the production build.
- The faithful CDP capture of the new overview, and with it a real visual
  self-score.
