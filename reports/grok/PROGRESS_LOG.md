# Dashboard progress log

One line per commit: time (UTC), commit, what changed, screenshot. Newest first.

## 2026-10-14

- **02:40Z — M-D1.1: the desktop icon opened nothing.** Two guards in
  `launcher/orchestrator.py` silently suppressed the app window. (1) The
  `not idle` term: `ControlPlane.start()` replays the last START from the ledger
  (closed `SYSTEM_ONLINE` 2026-10-03), so *every* launch was a replay and the
  guard treated that as "do not show anything". The owner clicking the icon is
  asking to *see* AHOS. Term deleted. (2) The strict `HEALTHY` term: a
  hand-started `next dev` on port 3000 made the gateway `foreign_busy` →
  UNHEALTHY (correctly — we do not own that process). New
  `_dashboard_reachable()` asks the URL the window actually depends on, without
  weakening what the component snapshot reports. **Screenshot:**
  `reports/dashboard/screens/M-D1.1/app_window.png` (01:50Z, 447 distinct
  colours) and `app_window_relaunch.png` (02:34Z, 1211 distinct colours) — the
  relaunch is the richer render. Launcher log: `app_window: opened via chrome` at
  01:50:03Z and 02:25:33Z. Tests: 151 passed, 1 skipped. Decision recorded in
  `DECISIONS_LOG.md` (2026-10-14, M-D1.1).
- **02:35Z — screenshot + probe tooling.** `scripts/windows_screenshot.ps1`
  (System.Drawing capture of the primary screen; UTF-8 BOM + CRLF + ASCII per the
  house convention, verified by `test_web_api_auth_gate.py`) and
  `scripts/png_probe.mjs` (minimal PNG decoder: IHDR parse, concatenated IDATs,
  `inflateSync`, unfilter types 0–4 with the Paeth predictor) — needed because
  this agent cannot view images, so a capture is only proof if its pixel
  statistics show a real render.
2026-10-14 00:4x +0330  a5e9f8a  dashboard: template-first shell port + 11 overview panels on one /api/command fetch; tsc clean for all owned files  —
- **03:1xZ — M-D2.1 (part 1):  silently walks to a free port when the one it was asked for is held, and nothing downstream is told.** The stray hand-started server on 3199 (orphaned by a previous session) left the launcher's `gateway_selected.json` advertising a dead 3000, so the health probe, the boot URL and the app window all asked an address with nothing on it — the same class of bug as M-D1.1's closed window. Added `_reconcile_gateway_port()`: the only place the real port is published is the `Local:` line Next prints once it finishes booting, so the boot loop reads it back from the gateway log (using the pid record's `log_offset` so an earlier boot's line is never adopted), then rewrites the live selection, the selection record and the pid record — which is what the probe, `dashboard_url()` and the window-open all read. Tests: 5 new cases in `TestGatewayPortReconcile`; full orchestrator suite 132 passed, 1 skipped.
- **03:15Z — M-D2.1 (part 1): `next dev` silently walks to a free port when the one it was asked for is held, and nothing downstream is told.** The stray hand-started server on 3199 (orphaned by a previous session) left the launcher's `gateway_selected.json` advertising a dead 3000, so the health probe, the boot URL and the app window all asked an address with nothing on it — the same class of bug as M-D1.1's closed window. Added `_reconcile_gateway_port()`: the only place the real port is published is the `Local:` line Next prints once it finishes booting, so the boot loop reads it back from the gateway log (using the pid record's `log_offset` so an earlier boot's line is never adopted), then rewrites the live selection, the selection record and the pid record — which is what the probe, `dashboard_url()` and the window-open all read. Tests: 5 new cases in `TestGatewayPortReconcile`; full orchestrator suite 132 passed, 1 skipped.
- **03:30Z — M-D2.1 (part 2): end-to-end proof the launcher now owns the serving URL.** Stopped the orphaned hand-started `next dev -p 3199` (decision in `DECISIONS_LOG.md`), then one clean `launcher start`: pid record 11420 matches a live `next dev --hostname 127.0.0.1`, `gateway_selected.json` says 3000, port 3000 serves HTTP 200 with the AHOS shell markup, gateway log prints `- Local: http://127.0.0.1:3000` so the new reconcile is the intended no-op, and `app_window: opened via chrome` at 06:24:21. Screenshot `reports/dashboard/screens/M-D2.1/app_window.png` (1536x864, 9875 distinct colours, 26.3% deep navy, 0.20% gold + 0.64% cyan) with `side_by_side.png` against the owner target. Honest self-score NOT claimed at 8+: this agent cannot view images and 9.3% of the capture is unexplained near-white in a dark-theme app, so a CDP capture waiting on the stage's readiness is carried forward. Also carried: `next build` fails and degrades to dev — the failure tail is discarded by `_gateway_mode`, cause unknown. Orchestrator suite 132 passed, 1 skipped.
