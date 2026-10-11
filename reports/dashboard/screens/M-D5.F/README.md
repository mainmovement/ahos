# M-D5.F — the chip's text is solid, not hatched

- Date (Tehran): 2026-10-11 · Step: M-D5.F (owner QA, 19:42 list item 1)
- From `README_FOR_CLAUDE.md` (2026-10-11 19:26): *"Top-left chip text STILL
  hatched/unreadable. M-D5.F (solid text, Vazirmatn, contrast >= 4.5:1) was step
  one and is not done. Do it now."*

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
- **Items 2–6 of the 19:42 list** are untouched: the `config/idea_shelf.json`
  seed, the T1 wow pass, M-D6 globe, and the Settings Force-T3 control. This step
  was item 1 only.
- **`npx next build`** not run; the 3199 dev server holds `data/e01_discovery.sqlite-shm`
  open, as in M-D5.5. `tsc` covers the changed surfaces and the live dev capture
  exercises them.
