# M10.1 MODEL BLOCKER

Written: 2026-10-07 Asia/Tehran (Grok autopilot unblock pass)
HEAD: ca4ac83 (box security merge present; see verify_merge / BOX_PATCHES_MERGED.md)
Mission: M10.1 (PGlite init in launcher) — **paused / NEEDS_REVIEW**

## Exact errors (from `reports/grok/_claude_ap_M10_1_result_fail13.txt` and siblings)

```
[claude-code:unrecognized_model] {"model":"Atria-Dawn-Preview","query_source":"sdk"}
API Error: Request rejected (429) · Token quota exhausted.
```

Env in use (names only; no secrets):
- `ANTHROPIC_BASE_URL=https://api.atria-asi.ai` (User)
- `ANTHROPIC_MODEL=Atria-Dawn-Preview` (User)
- Auth present via User `ANTHROPIC_AUTH_TOKEN` / `ATRIA_API_KEY` (values not recorded here)

## What was checked (no invented model names)

1. **Project docs**: `.env.example`, `reports/grok/run_mission.ps1`, `CLAUDE_REVIEW_20261007.md`, continuation guide, orchestration log — **no alternate working Atria model string documented**. Prior review already noted the same.
2. **Atria API**: authenticated `GET https://api.atria-asi.ai/v1/models` → HTTP 200, **single** model id: `Atria-Dawn-Preview` (already set). Other common paths 404.
3. **Dry probe (not a mission)**: child process with same base URL + auth, **`ANTHROPIC_MODEL` unset** → `API Error: 400 A supported model is required.` So blanking the model is not a workable autopilot fix.

## Strategy chosen: (c) pause — not (a)/(b)

- (a) Documented good name for this proxy **is** `Atria-Dawn-Preview` (from `/v1/models`), already in User env — does not clear Claude Code `unrecognized_model` + 429.
- (b) Unset fails with 400 as above.
- (c) **Applied**: refreshed `reports/grok/autopilot/HOLD.flag` (prior HOLD was empty/stale from 2026-10-04 and past the 6h window) and set queue **M10.1 → NEEDS_REVIEW** so the runner stops burning 429 retries. Interactive Claude GUI (`claude --model` without `-p`) was not touched.

## What the owner must set / do

1. Confirm with Atria UI/docs (or Claude Code settings) a **model string Claude Code accepts** for this gateway — do not guess from Anthropic marketing names if Atria does not list them.
2. If quota is exhausted, wait for / restore Atria token quota (429).
3. Optionally set User `ANTHROPIC_MODEL` to the confirmed string (or fix Claude Code allowlisting for `Atria-Dawn-Preview` if that is intended).
4. Then clear/refresh: delete or expire `reports/grok/autopilot/HOLD.flag`, set M10.1 back to `PENDING` or `PARTIAL` in `CLAUDE_AUTOPILOT_QUEUE.md`, and let Startup VBS / autopilot resume.

## Not done (by design)

- No inventing model names
- No push / no commit of `.env`
- Did not kill interactive Claude (PID 9580 `--model` without `-p`) or historical PID 4708

---

## CORRECTION 2026-10-09 21:00 (Claude, night run) — the model name was never the blocker

This page's title has misled two separate investigations toward the model string.
The live evidence collected since says the opposite:

1. **The `unrecognized_model` line is cosmetic.** It is printed to **stderr** on
   *every* `claude -p` run against this gateway, on successes as well as
   failures. Proven directly 2026-10-09: `claude -p --model <derived>` replied
   with the notice on stderr and a correct reply on stdout, in one process.
2. **The real failure was the 429.** The M34 headless attempts of 19:55 and 20:11
   (`reports/grok/_claude_ap_M34_result.txt`) died on
   `API Error: Request rejected (429), Token quota exhausted` — account quota,
   not the model id.
3. **That quota death is transient.** The gateway serves `Atria-Dawn-Preview`
   normally now; it is the *only* id `GET /v1/models` returns, so there is no
   "better" string to switch to, and the 400-with-blank probe above still holds.

What actually changed to make the runner reliable (both in `bd93360` and now):
streams are separated so the stderr notice can never be folded into a verdict,
and `IsInfraFailure` matches the CLI's real quota wording, so a quota death is
classified INFRA and charges no attempt instead of escalating to an owner gate.

Consequence for the "owner must set" list above: **item 1 and 3 are not needed.**
The model is correctly configured. Only item 2 (quota availability) ever
mattered, and it self-heals.

What was done on this pass: `run_mission.ps1` now derives the model from the
same source the interactive session uses (User `ANTHROPIC_MODEL`, falling back
to the User `settings.json` `model` field) and passes it as an explicit
`--model`, aborting loudly if it cannot be derived. No model name is hard-coded
in the repo anymore, so no future investigation can chase it.
