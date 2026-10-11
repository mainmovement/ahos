# M-D5.1 — Prototype Review

- Date (Tehran): 2026-10-11 · Author: Claude (for Soltan's queue, owner Mehrdad)
- Scope: read-only review of the five excluded prototype directories named in
  `DASHBOARD_DESIGN_SPEC.md` §13 and `TEAM_QUEUE_2026-10-11.md` M-D5.1.
- Reason: owner rule "no duplicates, no blind rewrite" — review before building
  the M-D5 stage so nothing is reimplemented, and so the prototypes' defects are
  not inherited. **No prototype file is imported, copied wholesale, or wired in.**
  `tsconfig.json:30-37` excludes all five; that stays.

## What the five actually are

All five are forks of the same `nextjs-postgresql-template` (identical
`drizzle.config.json`, `eslint.config.mjs`, `postcss.config.mjs`, and the same
`dotenv 17.3.1 / drizzle-orm 0.45.2 / pg 8.20.0 / react 19.2.6 / next 16.2.6`
deps). They diverge only in the 3D/experiment layer. Their `next` and `three`
pins are both older than the root's (`next 16.3.8`, `three 0.186.1`), so their
lockfiles are not a source of truth for ours.

| Dir | Real 3D? | What is actually there |
|---|---|---|
| `advanced-3d-audiovisual-website` | **No** — 2D canvas | `Cyber3DCanvas.tsx` (245 lines) hand-rolls a 2D `getContext("2d")` projector over `ROOTS/TRUNK/BRANCHES/LEAVES/OCEAN` layers. `three@^0.185.1` is in `package.json` but unused in `src/`. Also `utils/audio.ts`, a procedural Web Audio engine. |
| `advanced-3d-audiovisual-website (1)` | **Yes — one file** | `src/components/three/HeroScene.tsx` (~190 lines), the only genuine R3F scene in the five. The rest is a 13-page `/dashboard/*` app with `recharts` + `zod`. |
| `درخت کاملتر immersive-3d-audiovisual-website` | No (README only) | `README.md` + `scripts/seed.ts`. No `src/components/three`. The README documents the "Wise Tree" metaphor and the asset policy (below). |
| `سایت درختadvanced-3d-audiovisual-platform` | No | A 17-route `(app)` route group, no three.js code. |
| `01` | No — 2D canvas | `tree-canvas.tsx` (356 lines), a 2D canvas "Wise Tree"; `atmosphere.tsx`, a time-of-day palette engine; plus `charts/counter/ticker/reveal` primitives. |

So the "five three.js prototypes" is really **one** R3F scene, two 2D-canvas
scenes, and two non-3D app skeletons. The review is correspondingly short, and
the amount of prior art to reconcile is small.

## `HeroScene.tsx` — the one real R3F scene, in detail

Composition: an icosahedral `KnowledgeCore` (`MeshDistortMaterial`, distort 0.38)
inside three tilted `OrbitRing`s (flattened `y` by ×0.28), a shell of 900
`DataParticles` on a flattened sphere, and 14 `Float`-ing node spheres, lit by
cyan and violet point lights at `dpr={[1, 1.75]}`, camera `[0, 0.4, 6.2]` fov 45.

### Worth carrying forward (patterns, rewritten)

1. **The flattened orbit ring.** `OrbitRing` samples 128 points on a circle and
   multiplies `y` by ~0.28, giving an armillary/ecliptic read rather than a
   hula hoop. This is *exactly* the armillary-ring vocabulary spec §1 wants for
   the chain rings around the globe, and it is cheap: one `Line` per ring.
2. **Distorted low-poly core.** `icosahedronGeometry args={[1.35, 4]}` +
   `MeshDistortMaterial` is a plausible seed for the boot emblem's "core" or the
   M-D10 coin backdrop, at a vertex count the 8 GB floor can hold.
3. **Particle shell on a flattened sphere.** Uniform-in-shell placement
   (`phi = acos(2·rand−1)`) then `y *= 0.6` — a galaxy/disc field. Reusable for
   the M-D6 starfield if it is tier-gated and seeded.
4. **The budget shape.** ~900 points + 14 meshes + 3 lines is a real signal that
   the scene fits the §12 draw-call/triangle budgets when instanced.

### Must NOT be carried forward (defects)

1. **`<Environment preset="night" />` — the offline hazard, live in this file.**
   REFERENCE_BOARD ref 9 documents that drei `useEnvironment` presets fetch HDRIs
   from `https://raw.githack.com/pmndrs/drei-assets/...`. This is a hard violation
   of spec §0.5 ("make zero external requests at runtime") and of M-D2's CSP. The
   M-D5 stage uses a **procedural** environment instead, per spec §12 ("No HDR
   environment fetch … A procedural gradient env is used instead"). Any future
   copy of this file fails the M-D2 network-log acceptance test.
2. **`Math.random()` for every position.** Node angles, radii and scales are
   re-randomised on every mount, so the scene reflows between refreshes. Spec §1
   is explicit that a bead's angle is "a deterministic hash of `tokenKey`, so it
   stays stable between refreshes". The stage uses a seeded hash, not `Math.random`.
3. **Palette collides with the truth palette.** `#ff5fae` (pink nodes) sits next
   to CONFLICT's `#E07BE8` and `#35f0d0` next to VERIFIED's `#2EC4A6`, and both are
   used as *decoration*. Spec §2.3 forbids this: "Status colours are identical in
   both themes and are never used as decoration", and §2: "Brand gold and crimson
   are never used as status." The stage takes its colours from
   `dashboard_tokens.ts` only.
4. **No tier gating, no reduced motion, no `frameloop`.** The scene runs the full
   particle count and three rotating rings unconditionally, with no
   `prefers-reduced-motion` check and no `frameloop="demand"` path. Spec §11
   requires a T0/2D mode where "the three.js chunk is never downloaded", §8.1
   requires reduced motion to stop rotation, and §11 Low-power requires
   `frameloop="demand"`. `HeroScene` would fail all three.
5. **Not real data.** 14 decorative nodes, 900 decorative particles. Spec §0.1
   and FREE_HERO_FX_SOURCES v1: "Decorative motion carries no numbers" — so this
   is legal *as* decoration, but it must not be read as prior art for the bead or
   graph layers, which bind to `opportunities[]`.

## `audio.ts` — procedural Web Audio, the right approach

A `SoundEngine` class: `AudioContext` created lazily inside `initCtx()`, resumed
from `suspended` there, `isMuted` defaulting to `true`, volume 0.25, and a
`toggleMute` that plays a click on unmute. Everything is synthesised — "No
external audio files needed". That matches spec §8.2's "generate the signature
tones … procedurally with Web Audio oscillators and filters at runtime. No files
and no licence", and REFERENCE_BOARD ref 25's "zero licence risk" alternative.

**Carry:** the lazy-init + resume-on-gesture pattern, and the no-samples policy.
**Change:** the prototype's truth sounds are not separated into the spec's
palette (a warm fifth for VERIFIED, *no* tonal sound for UNKNOWN, a minor-second
dyad for CONFLICT, a low thud for REJECTED). M-D9 builds those on the
`styleFor(...).soundId` contract from `dashboard_truth_badge.ts` rather than on
ad-hoc names, so a badge and its cue cannot disagree.

## `tree-canvas.tsx` — the seeded-RNG discipline

A 2D canvas Wise Tree whose geometry is grown once by `growTree()` from a
`mulberry32(1377)` seeded PRNG, with an explicit docstring mapping the metaphor
to the system ("roots = data sources · rocks = failures · fruits =
opportunities · golden fruit = exceptional opportunity").

**Carry:** the seeded-PRNG discipline — deterministic output from a fixed seed is
the same invariant spec §1 asks for bead placement, and it is what makes a
screenshot comparable between runs (relevant to the "Soltan screenshots and
compares" QA rule). This file's `mulberry32` is the reference implementation for
the hash the stage will use. It is also a usable **T0 2D fallback** vocabulary:
a canvas scene that needs no WebGL at all.

**Change:** its `TreeVitals` input drives leaf/fruit counts; in the real system
those counts must come from `opportunities[]`, not from a local vitals object, or
the widget is decorative motion implying metrics.

## `atmosphere.tsx` — half real, half fabricated

Interpolates a colour palette over the decimal hour (`STOPS` keyed by hour) to
paint a sky. **The time-of-day half is real** — the hour comes from the clock,
and a dusk gradient is legitimate mood lighting. **The weather half is not**:
`cond: "clear" | "rain" | "storm" | "snow" | "fog"` and `tempC` have no source in
the repo, and spec §15/Q4 leaves geography and weather unavailable. Per D-D07
"never fake live state", the stage takes the **hour** (real astronomy, like the
terminator) and drops the weather. If a weather widget is ever wanted it renders
UNKNOWN until a real source exists.

## `درخت کاملتر` README — the asset policy, stated

The only deliverable here is the README, and its Stack section states the policy
the M-D5 stage adopts verbatim: "**3D**: three.js · React Three Fiber ·
postprocessing (bloom/vignette) — the procedural **Wise Tree scene** (no
textures, no models, 100% geometry + shaders)" and "**Audio**: fully synthesized
Web Audio … **No sample files.**" Combined with `FREE_HERO_FX_SOURCES_v1`
("vendor everything through the npm gate. No CDN, remote fonts, HDRIs or
analytics"), the stage's asset rule is:

> **Procedural geometry and synthesised audio only. No textures, no models, no
> HDRIs, no audio files, no CDN.** The one exception the spec allows is the
> Natural Earth land geometry (public domain, via `world-atlas`), which is data,
> not art.

The Wise Tree metaphor itself ("roots = data sources · stones = errors · golden
fruit = exceptional opportunities") is *not* adopted: spec §1's concept is "The
Imperial Observatory" — a globe, armillary chain rings, a lacquer observatory at
dusk — and OWNER_DECISIONS wins. The tree stays an interesting alternate concept
in the prototypes, not the main view.

## Verdict for M-D5

| Take | From | Into |
|---|---|---|
| Flattened armillary ring pattern | `HeroScene.tsx` `OrbitRing` | `ChainRings` (M-D6), rewritten in gold, seeded, tier-gated |
| Distorted low-poly core pattern | `HeroScene.tsx` `KnowledgeCore` | the M-D10 emblem backdrop, rewritten |
| Lazy `AudioContext` + no samples | `audio.ts` | M-D9 sound, on `soundId` from the badge contract |
| Seeded PRNG (`mulberry32`) | `tree-canvas.tsx` | the deterministic bead-angle hash in M-D6 |
| 2D-canvas-no-WebGL vocabulary | `tree-canvas.tsx` | the T0 fallback path in M-D5.4 |
| Hour-based mood lighting (hour only) | `atmosphere.tsx` | the dusk gradient; **weather dropped** |
| Procedural-only asset policy | `درخت کاملتر` README | the whole stage |
| **Rejected** | `<Environment preset>` | replaced by a procedural environment |
| **Rejected** | `Math.random()` placement | replaced by a seeded hash |
| **Rejected** | cyan/violet/pink decoration | replaced by `dashboard_tokens.ts` |

Nothing above is a copy of prototype source. Each row is a pattern rewritten
into the M-D module that owns it, in the spec's palette, with the honesty rules
applied. The five directories remain excluded from `tsconfig.json` and unwired.
