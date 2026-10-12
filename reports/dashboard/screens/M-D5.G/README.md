# M-D5.G — the «حالت اجرا» chip's border is solid

- Date (Tehran): 2026-10-11 · Step: M-D5.G, closing the owner's 23:03 QA note:
  *"chip text readable now, good. Still wrong: the 'حالت اجرا' chip has a
  dashed/hatched border, make it solid."*
- Follows M-D5.F (the swatch fix, which made the *text* legible). This is the
  same chip's remaining defect — its *frame*.

## The defect

`globals.css` gave the UNKNOWN badge `border-style: dashed`. The PAPER ONLY pill
renders UNAVAILABLE as UNKNOWN (401 headless reproduces the owner's view), so the
chip the owner stared at had a 1px dashed frame. At 0.75rem chip scale a dash that
fine does not read as a deliberate cue — it reads as a rendering defect, exactly
as the 45° hatch had read behind the label.

## What changed, and what did not

| File | Change |
|---|---|
| `dashboard_truth_badge.ts` | UNKNOWN's `border` is `"solid"`, with the QA note and the surviving cues named |
| `globals.css` | `.truth-badge--unknown` states the solid base explicitly rather than overriding it |
| `TruthBadge.tsx` | docstring: UNKNOWN is the exception whose identity is not its border |
| `scripts/dashboard_truth_badge_selftest.ts` | the border-column assertion becomes the monochrome-cue assertion |

**The §2.3 invariant is intact, and the test now checks the real one.** The
spec's requirement is that *"colour is never the only cue"* — that a state is
identifiable in monochrome and to a colour-blind reader. The old test enforced a
proxy: five states, five distinct border treatments. Making UNKNOWN solid breaks
the proxy (VERIFIED is solid too) while preserving the requirement, because
UNKNOWN still has two cues that are neither colour nor border:

| State | glyph | border | fill |
|---|---|---|---|
| VERIFIED | ✓ | solid | flat 16% |
| **UNKNOWN** | **?** | **solid** | **45° hatch** |
| STALE | ◷ | dotted | none |
| CONFLICT | ⚠ | double | none |
| REJECTED | ✕ | bar (4px left) | flat 16% |

✓-over-flat and ?-over-hatch are distinguishable without colour, which is the
whole point. The replacement assertion checks the full (glyph, border, fill)
triple — so two states may now share a border, but only when another column still
separates them, and no single column may be the sole cue. A second assertion pins
`styleFor("UNKNOWN").border === "solid"` so a future re-dash fails here first,
before it can reach an owner's screenshot.

The other four states did not move. STALE's dotted, CONFLICT's double and
REJECTED's bar are their §2.3 shapes and were not complained about.

## Verification

The capture harness gained a witness: the poll now reports the badge's computed
`borderTopStyle`/`borderLeftStyle`. Pixel counts cannot see a dash pattern, so
without this the fix would be verified only against the source, not against what
the browser rendered.

| Capture | chip | badge border | canvas | gold px | gold centroid | scene fps |
|---|---|---|---|---|---|---|
| `t1.png` (measured) | `dashi-tier--t1` | `solid/solid` | 1 | 15 685 | (775, 381) | 60 |
| `t3.png` (forced) | `dashi-tier--t3` | `solid/solid` | 1 | 31 412 | (775, 309) | — |

- **The border is solid in the live page**, at both tiers, not only in the
  stylesheet. `root: none`, `label: none`, `swatch: PATTERN` — the M-D5.F swatch
  separation survives this change unchanged.
- **The globe is unaffected**: gold pixels and centroid match the M-D6.1 readings
  (15 664 → 15 685 at T1, 31 500 → 31 412 at T3 — run-to-run noise in the dot
  field's additive fill).
- No console errors in either capture.

Selftests: `test:truth-badge` **47/47**, `test:stage-quality` **48/48**,
`test:globe` **8/8**, `test:idea-shelf` **26/26**, `tsc` 0 errors, `eslint` clean.

## Not done, and why

- **The tier chip's own rung borders** still vary (T1 is dotted, T0/pending
  dashed). The owner named only the «حالت اجرا» chip, so those were left alone —
  they are a deliberate non-colour cue for the ladder rung, not a defect report.
  If the owner reads them the same way, that is a one-line follow-up here.
- **STALE, CONFLICT and REJECTED** keep their §2.3 border shapes by design.
- **`npx next build`** still not run; the 3199 dev server holds
  `data/e01_discovery.sqlite-shm`, as in every step since M-D5.5.
