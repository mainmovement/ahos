# M-D5.F — the 19:42 QA list, items 1 and 2

- Date (Tehran): 2026-10-11 · Step: M-D5.F (owner QA, `README_FOR_CLAUDE.md` 19:26)
- Item 1: *"Top-left chip text STILL hatched/unreadable. M-D5.F (solid text,
  Vazirmatn, contrast >= 4.5:1) was step one and is not done. Do it now."*
- Item 2: *"'Waiting for upgrade' row shows a hatched error ('reading idea shelf
  failed'). Create a seed config/idea_shelf.json from real approved items … so the
  panel shows real content. If the file is missing, show clean grey UNKNOWN text,
  never a hatched box."*

## The defect

`globals.css` painted §2.3's fill as **the badge's own background**:

```css
.truth-badge { background: var(--badge-fill, transparent); }
```

For UNKNOWN that fill is the spec's 45° hatch — `repeating-linear-gradient(45deg,
var(--ahos-status-unknown) 0 1px, transparent 1px 6px)`. A background on the badge
span is a background *behind the label*, so 1px grey lines every 6px crossed the
Persian word at 0.75rem and the chip read as struck-through.

The top-left chip **is** that badge. In the owner's window the PAPER ONLY pill
holds `<TruthBadge state="UNAVAILABLE" label="حالت اجرا">` whenever
`/api/command` does not report a known execution mode, and the headless capture
reproduces exactly that (`/api/command` → 401, no session). So the hatched text
the owner saw was the UNKNOWN hatch through its own label.

## The fix

§2.3's pattern is a cue, not a text background. It is now painted on a swatch
beside the label, and the label sits on a solid surface:

| Piece | Change |
|---|---|
| `TruthBadge.tsx` | Renders `truth-badge__fill` only when the state has a fill, and wraps the label in `truth-badge__label`. The glyph span is unchanged. |
| `globals.css` | `.truth-badge` is `background: transparent`; `.truth-badge__fill` is a `0.7em` swatch reading `var(--badge-fill)`; `.truth-badge__label` is explicitly transparent so no caller can pattern it. |

The hatch survives — spec §2.3 still requires it as UNKNOWN's non-colour cue, and
`dashboard_truth_badge.ts`'s `fill` values are untouched. Only the surface they
are painted on changed.

**Vazirmatn** was already wired (`app/layout.tsx` → `next/font/google` under
`--font-vazir`, used by `.dashi`, `.dashi-pill` and `.truth-badge`). next/font
self-hosts the file at build, so there is no runtime fetch. The illegibility was
the hatch, not the typeface; no font binary was vendored.

**Contrast.** The label takes the state's own status colour. M-D5.F's 4.5:1 floor
is now asserted (below) for every state against both themes' `bg` and `panel`. The
tightest case is UNKNOWN's `#9AA3B2` on Imperial's `#160E12` panel at **7.46:1**.

## Verification

- `npm run test:truth-badge` — **47/47** (was 44/44). The three new assertions
  live in a new `M-D5.F` suite:
  1. the `.truth-badge` rule carries no `--badge-fill` and is `background:
     transparent` — the regression cannot return through the stylesheet;
  2. the CSS has a `__fill` swatch reading the fill var, a `__label` rule, and
     the component renders both;
  3. every state's label clears 4.5:1 on all four surfaces (WCAG luminance, not
     an eyeball).
- `npx tsc --noEmit` — 0 errors.
- `npx eslint` on the touched files — clean (`globals.css` is outside the lint
  config, as in M-D5.5).
- `scripts/screenshot_dashi.mjs` now reports the badge's computed backgrounds, so
  the capture proves the property mechanically rather than by looking:

  | Capture | chip | canvas | badge root | badge label | swatch |
  |---|---|---|---|---|---|
  | `t1.png` (measured) | `dashi-tier--t1` | 1 | `none` | `none` | `PATTERN` |
  | `t3.png` (forced) | `dashi-tier--t3` | 1 | `none` | `none` | `PATTERN` |

  Before the fix the root column read `PATTERN`; the hatch was the text's
  background. `canvas: 1` in both means the stage mounted, not its loading line.

- `badge-sheet-imperial.png` — the fixture page renders all 17 fixture states of
  the contract in one frame, fed by the same `styleFor` the dashboard uses.

## Harness change

`screenshot_dashi.mjs` took two fixes the standing "screenshot at T1 and forced
T3" instruction needs:

- an optional 4th arg `overrideTier` (T0..T3) seeds the app's own
  `ahos.stage.tier.override` before boot. It uses the same path the Tier Panel
  uses, so `resolveTier` still applies the machine's real limits and the chip's
  title says the pick was manual — nothing is fabricated about the hardware.
- the poll waited only for the chip to leave `pending`, which fires ~6s in, while
  `StageLazy` was still fetching and parsing the three.js chunk. It now waits for
  the canvas the verdict allows (or the 2D `dashi-fallback`), which is what
  stopped the earlier captures from showing the scene at all.

## Not done, and why

- **Neon-theme capture.** The badge sheet and the shell switch theme by client
  state, not URL, so a headless capture cannot select neon. The contrast
  assertion covers neon numerically (all four surfaces); a neon screenshot needs
  a hash-init on the fixture page, deferred.
- **Items 3–6 of the 19:42 list** are untouched: the T1 wow pass, M-D6 globe, and
  the Settings Force-T3 control. This step was items 1 and 2 only.
- **`npx next build`** not run; the 3199 dev server holds `data/e01_discovery.sqlite-shm`
  open, as in M-D5.5. `tsc` covers the changed surfaces and the live dev capture
  exercises them.

---

# Item 2 — the registry seed

## What shipped

`config/idea_shelf.json` — the shelf the panel reads, seeded from Asi's
2026-10-11 vetting and the owner's named list. It existed as a requirement until
now and the file was absent, so the panel could only ever show its UNKNOWN
branch. Nine entries, every tier tag a tier the vetting actually assigned:

| id | title | tier | where the tag came from |
|---|---|---|---|
| `vane` | Vane | T16 | «APPROVE-SHELF T16 for M18.N cited search», ex-Perplexica, MIT, 127.0.0.1 only |
| `opensandbox` | OpenSandbox | T16 | «SHELF T16», Apache-2.0; Docker/K8s may exceed the 8 GB floor |
| `browser-use` | Browser Use | T16 | «SHELF T16», MIT |
| `anythingllm` | AnythingLLM | T16 | «AnythingLLM shelf T16» (v1.36) |
| `uptime-kuma` | Uptime Kuma | T8 | «Uptime Kuma T8 shelf» (v1.41), 127.0.0.1:3001, notifications off |
| `light-ocr` | light-ocr | T8 | «APPROVE-SHELF … T8 sidecar (M18.N)» (v1.43), entry only, no install |
| `bitnet-b158` | BitNet b1.58 2B4T | T8 | «APPROVE shelf. T8 = BitNet b1.58 2B4T local helper» (v1.46) |
| `laya` | Laya | **null** | APPROVE-SHELF, but «RAM unverified» — no tier was assigned |
| `kev` | Kev | **null** | APPROVE for M35.1, but «verify … Windows CPU fit» — no tier was assigned |

On this machine (T8) the panel's «منتظر ارتقا» now lists the four T16 tools and
nothing the vetting tagged T8, which is the honest reading of the list: those are
the ideas the measured hardware does not reach.

**The two `null` tags are the load-bearing part.** Laya (a 421M local model) and
Kev (0.8B–27B decision models) sound like they should fit in 8 GB, and the
DEDUP notes even guess «Kev-0.8B likely T8, 4B T16». But Asi's verdict left both
open, and the panel's rule is explicit that an untagged idea is *neither* runnable
nor awaiting — listing it as awaiting would claim a requirement the registry never
recorded. So a `T8` there would be a plausible-looking hardware fact the vetting
never issued, which is the exact fabrication the shelf's own docstring forbids.
The selftest pins this: an edit that tags `laya` or `kev` fails the suite unless
the expectation is updated with it, which is the prompt to fix the vetting record
this file is seeded from.

`est_ram_mb` is absent from every entry. No vetting line gave a number, and the
panel renders the RAM count only when one is present — inventing megabyte figures
would put a measurement in the panel that Asi never made.

## The hatched box is gone, and why

Item 2's second clause — «clean grey UNKNOWN text, never a hatched box» — is
satisfied by item 1, not by the seed. `.tier-panel__unknown` has no background of
its own; the hatch the owner saw was the `TruthBadge` UNKNOWN *inside* it, whose
§2.3 fill was painted behind its own label. With the fill on a swatch the
UNKNOWN branch renders grey text on the panel, which the capture below shows.

## Verification

- `npm run test:idea-shelf` — **26/26** (was 22/22). Four new assertions read the
  *committed* registry rather than a fixture: it parses as a shelf, its ids are
  unique, every tier tag is a real ladder rung or `null`, the `null` tags are
  exactly Laya and Kev, and `awaitingUpgrade(shelf, "T8")` lists exactly the four
  T16 tools.
- `npx tsc --noEmit` — 0 errors; `npx eslint` on the touched files — clean.
- `node scripts/screenshot_tierpanel.mjs` — the panel opens on the live dev
  server with the registry present: four hardware rows, the measured reason, the
  RAM line, no override, and one grey UNKNOWN for the shelf. `canvas: 1`, no
  console errors. `/idea_shelf.json` → **404** (the registry stays out of
  `public/`, so the browser cannot fetch a second copy that could drift from the
  one the route reads).

## Not verified, and why

- **The OK branch of the route, in a browser.** The headless browser holds no
  dashboard session, so `/api/idea_shelf` answers **401 RESTRICTED** and the
  panel renders its error branch — the same gate every dashboard route sits
  behind, and the same reason the topbar pill reads UNKNOWN in these captures.
  The owner's launcher establishes the session, so the OK branch is what renders
  in their window; its content is asserted directly by the selftest against the
  committed file, and the route itself is unchanged since M-D5.5. Capturing the
  OK branch would have meant starting a second dev server with
  `AHOS_WEB_API_ALLOW_OPEN_ACCESS=1`, which weakens the auth gate even locally —
  declined as the less safe of the two options; the selftest carries the proof
  instead.
