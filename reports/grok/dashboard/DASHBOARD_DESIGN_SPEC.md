# AHOS Dream Dashboard: Design Spec ("فرماندهی")

Version 0.1 · 2026-10-09 (Tehran) · Grok Bot for Mehrdad Ghodrati · **Paper-only design. Reality rung: DESIGN.** Nothing here is built.

Repo facts come from read-only reads of `G:\robat\ahos` on DESKTOP-DH7QOCK: branch `ahos`, HEAD `373516e` (2026-10-09 02:50 Tehran, "feat(identity): multi-provider resolver opens the two-source gate"), with 259 uncommitted or untracked paths in the worktree. No `.env` was opened. References: `REFERENCE_BOARD.md`. Build plan: `CLAUDE_BUILD_MISSIONS.md`.

---

## 0. North star and non-negotiables

**Feeling:** the whole world steered from one screen. One continuous, lit, deep 3D world (Igloo/Lusion bar), wrapped in a calm and dense decision UI that a tired person can read at 3 a.m.

**Non-negotiables.** Each comes from owner decisions in `ahos-continuity.md` or from repo `AGENTS.md`.
1. **Real data only.** Every number on screen traces to a repo endpoint field (§6). With no source, the widget shows UNKNOWN or empty. It never shows a placeholder number. ("UNKNOWN > fabricated", AGENTS.md; D-D07 "Never fake live state".)
2. **PAPER_ONLY is always visible.** The UI has no control that could imply live trading (D-A01).
3. **TypeScript is presentation only.** The UI never creates, upgrades or re-colours a canonical decision. Badges render what `/api/command` and `/api/canonical` already say (AGENTS.md "TypeScript/Next.js is … presentation surface").
4. **UNKNOWN ≠ safe, CONFLICT ≠ success** (D-P08). These states can never borrow success colour, shape, sound or motion (§9).
5. **Local only.** Bind to 127.0.0.1, bundle every asset, make zero external requests at runtime. The window has its own browser profile (Mission 1).
6. **Persian RTL first.** `<html lang="fa" dir="rtl">` already exists in `app/layout.tsx`.
7. **It must run on this laptop:** integrated GPU, 8 GB RAM (D-B13), Windows. A full 2D mode gives the same information.

---

## 1. Visual concept: "The Imperial Observatory" (رصدخانه)

There is one scene. A black-lacquer observatory floats at dusk. Its centre is a slowly turning **globe of the real Earth**: Natural Earth land, with the **real** day/night terminator computed from the clock and a gold "home" mark at Tehran. Crypto **chains orbit** the globe as gold armillary rings, like an astrolabe. Opportunities from the canonical read model sit as beads on their chain's ring. The UI panels are lacquer-and-glass "windows" hung around this world in depth layers.

- From **ref 1** (mood): crimson velvet, gold embroidery edges, warm rim light, mist layers for depth, Faravahar and coin as the visual language.
- From **ref 4** (emblem): the coin is the system's "seal". It is the loader, the app icon, and a "sealed" mark on canonical decisions.
- From **ref 3** (layout): the information architecture and its density.
- From **refs 5 and 6**: two secondary "worlds" reached by camera flights from the globe (Agent Society tower, Evidence pipeline).
- **Persian geometry**: one 10-fold **shamseh** (sun rosette) and a girih edge band, both generated procedurally (no copied art). They appear as panel corner ornaments, the loader halo, and a faint floor engraving under the globe.

**What makes it award-level and not a generic HUD:**
- Real light and material: gold uses PBR metal and roughness with selective bloom. Lacquer gets a clearcoat look. We avoid flat neon outlines.
- One camera moves through one world; there are no page cuts.
- Typographic hierarchy: Lalezar ceremonial numerals, Vazirmatn UI, Markazi dossier text.
- Restraint: at most one moving hero element at a time, and everything else still.

**Honesty about the globe.** The repo's data has **no geographic fields**. A read-only search of `schema.ts`, `snapshot.ts`, `news.ts` and `providers.ts` for country, region, geo, latitude, longitude or exchange returned nothing. So:
- Earth, terminator and Tehran mark are real (astronomy plus a public-domain map).
- Chain rings and opportunity beads are an **abstract layout**, labelled in-scene "چیدمان مفهومی — موقعیت جغرافیایی ندارد" ("conceptual layout — has no geographic position"). A bead's angle on its ring is a deterministic hash of `tokenKey`, so it stays stable between refreshes.
- A **"Geo" layer** exists but is disabled. It shows `UNKNOWN — منبع جغرافیایی موجود نیست` ("UNKNOWN — no geographic source available") until a backend field provides real geography (Open question Q4).

---

## 2. Themes and palette

Two themes share one token system. The default is **Imperial** (refs 1+4). The alternative is **Neon** (ref 3, close to the current `bg-[#040714] text-cyan-50` in `app/layout.tsx`). **Status colours are identical in both themes and are never used as decoration.** Brand gold and crimson are never used as status.

### 2.1 Imperial (default): "شاهنشاهی"
| Token | Hex | Use | Contrast vs `bg` #0B0709 |
|---|---|---|---|
| `bg` | `#0B0709` | Scene clear colour, page | — |
| `panel` | `#160E12` (88% alpha over scene) | Lacquer panels | — |
| `panel-edge` | `#3A2A1C` | 1px hairlines | decorative |
| `text` | `#EFE4CC` (parchment) | Body text | **15.9:1** |
| `text-muted` | `#A99A80` | Secondary text | **7.3:1** |
| `gold` | `#D4AF5A` | Ornament, focus ring, active nav, Lalezar numerals | **9.6:1** |
| `gold-hi` | `#F1D58E` | Specular highlight, hover | 14.0:1 |
| `crimson` | `#9E1C26` | Velvet fills, banner surfaces (**never text**) | 2.5:1 (fill only) |
| `crimson-hi` | `#D2343E` | Large display text ≥24px only, selected-tab underline | 4.1:1 (large text only) |
| `ember` | `#E8834A` | Sunset rim light in 3D, boot horizon (not a status) | 7.4:1 |

### 2.2 Neon (alternative): "نئون"
| Token | Hex | Contrast vs `bg` #040714 |
|---|---|---|
| `bg` | `#040714` (current repo body colour) | — |
| `panel` | `#0A1330` | — |
| `text` | `#E6F6FF` | **18.2:1** |
| `text-muted` | `#8FA6C8` | **8.1:1** |
| `accent` | `#3FD0FF` (cyan) | 11.2:1 |
| `accent-2` | `#4C82FF` | 5.7:1 |
| `gold` | `#D4AF5A` (emblem only) | 9.6:1 |

### 2.3 Truth and status palette (both themes; fixed)
| State | Hex | Shape / pattern (colour is never the only cue) | Contrast vs Imperial bg |
|---|---|---|---|
| **VERIFIED** (تأییدشده) | `#2EC4A6` (Persian turquoise) | Solid border, ✓ check glyph, solid fill at 16% | 9.1:1 |
| **UNKNOWN** (نامعلوم) | `#9AA3B2` (slate) | **Dashed** border, **?** glyph, 45° hatched fill, no glow | 7.9:1 |
| **CONFLICT** (تعارض) | `#E07BE8` (orchid) | **Double** border, ⚠ split-diamond glyph, zig-zag edge, no glow | 7.8:1 |
| **STALE** (کهنه) | `#B8A27A` (faded brass) | Dotted border, clock glyph, 50% desaturated | 8.1:1 |
| **REJECTED / VIOLATION** (رد / نقض) | `#FF5A4E` | Octagon glyph, solid red bar | 6.5:1 |

Contrast ratios were computed with the WCAG 2.x relative-luminance formula against `#0B0709`. Ratios against `#160E12` panels are about 5% lower and all stay ≥4.5:1, except `crimson` and `crimson-hi`, which are fills and large text only.

---

## 3. Typography (Persian RTL plus Latin and numerals)

| Role | Face (all OFL-1.1, bundled via `next/font/local`) | Size / weight |
|---|---|---|
| UI text (fa + en) | **Vazirmatn** variable | 14–16px body, 400/500. Labels 12–13px, 500. |
| Ceremonial numerals and titles | **Lalezar** | ≥28px only. The big counts (e.g. canonical decisions) use it **only when the value is real**. Otherwise show the "—" glyph in Vazirmatn muted. |
| Dossier / evidence quotes | **Markazi Text** | 16–18px, line-height 1.9 |
| One ceremonial line | **Noto Nastaliq Urdu** | Boot motto only |
| Latin wordmark "AHOS" | **Orbitron** (already in `app/layout.tsx`) | Wordmark only |
| Addresses, hashes, tickers, logs | **IBM Plex Mono** | 12–13px |

**Rules:**
- **Digits.** Persian prose uses Persian digits (۰–۹) via `Intl.NumberFormat('fa-IR')`. Prices, percentages and counts in data tables also use **Persian digits, with tabular alignment** (verify Vazirmatn's `tnum` support in M-D3; if absent, use fixed-width cells).
- **Exceptions:** token addresses, tx hashes, tickers (SOL, ETH), chain IDs and version strings stay **Latin**. Wrap them in `<bdi dir="ltr">` in Plex Mono so mixed bidi never scrambles them.
- **Time.** Show Tehran time with a short "تهران" tag, using `Intl.DateTimeFormat('fa-IR-u-ca-persian', {timeZone:'Asia/Tehran'})`. A toggle offers Gregorian.
- **Letter-spacing.** Never letter-space Persian (it breaks joining). Latin captions may use +0.08em.
- **3D text.** No Persian text is rendered as WebGL text. All Persian labels in 3D are DOM via drei `<Html>`, which gives correct shaping, selection and screen-reader access. Troika text, if ever used, gets a local font and a local `unicodeFontsURL`.

---

## 4. Layout (RTL), main view "فرماندهی" (Command)

The layout follows ref 3, mirrored for RTL. Base canvas is 1600×900 and it is fluid down to 1280×720.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR (56px): [ساعت تهران] [تازگی شواهد] [سلامت سیستم] [● PAPER ONLY]  ...  AHOS ◉ │  ← emblem on the RIGHT (RTL start)
├──────────┬──────────────────────────────────────────────────────┬─────────────┤
│ LEFT     │                                                      │ RIGHT NAV   │
│ COLUMN   │            3D STAGE: globe + chain rings              │ (72/240px)  │
│ (360px)  │       (opportunity beads, terminator, Tehran)         │ فرماندهی     │
│ تصمیم    │                                                      │ فرصت‌ها      │
│ کانونی   │   floating cards hang in depth around the globe:     │ جهان         │
│ (Canon.  │   • selected opportunity dossier (on click)          │ جامعه عامل‌ها │
│ Decision)│   • alert banner (only when /api/alerts active)      │ خط شواهد     │
│ ─────    │                                                      │ دانشگاه      │
│ خوراک    │                                                      │ گفتگو        │
│ زنده     │                                                      │ سامانه       │
│ (news)   │                                                      │ تنظیمات      │
├──────────┴──────────────────────────────────────────────────────┴─────────────┤
│ TELEMETRY STRIPS (ref 6) 120px: [چرخه‌ها] [ارائه‌دهندگان] [پوشش شواهد] [دفتر کاغذی] [هشدارها] │
└───────────────────────────────────────────────────────────────────────────────┘
```

- RTL means nav is on the **right**. Primary reading starts at the top-right: emblem, then PAPER ONLY, then health. The canonical-decision column sits on the left as the "conclusion" end of the reading path.
- Panels take ≤40% of the viewport, so the globe is always the hero. At 1280px the left column collapses to a drawer.
- Keyboard: `G` globe, `A` agents, `E` evidence, `/` chat, `M` mute, `Esc` closes dossier, `F2` toggles 2D mode.

---

## 5. Views

| # | View (fa) | Reference | Purpose | 3D scene (High tier) | 2D fallback |
|---|---|---|---|---|---|
| V0 | **ورود** Boot / onboarding | ref 2 + ref 4 | Covers launcher latency with honest progress from `/api/launcher`. | Dark desk silhouette → cracked-gold path draws across the floor → coin seal assembles → camera rises to the globe. ≤4 s, skippable (`Esc`, click). Plays fully on first launch of the day, otherwise in 1 s. | Static emblem plus a stepper of launcher components (`stores, db_backend, gateway, telegram, engine`) with real statuses |
| V1 | **فرماندهی** Command | ref 3 | Default overview. | Globe + rings + beads + terminator | Same panels; the globe becomes an SVG ring diagram plus a table |
| V2 | **فرصت‌ها** Opportunities | ref 3 cards | Ranked list with truth badges and a dossier. | Camera focuses the selected bead; its ring brightens | Sortable table |
| V3 | **جامعه عامل‌ها** Agent Society | ref 5 | Who exists and their **real maturity**. | Isometric lacquer tower, one floor per team (orthographic camera) | Grid of team cards |
| V4 | **خط شواهد** Evidence pipeline | ref 6 | Where each item is in DATA → IDENTITY → EVIDENCE → SECURITY → LIQUIDITY → SCORE → RISK → CANONICAL DECISION → PAPER. | Fixed-layout node graph on a dark floor; edge particles show real counts | React Flow SVG |
| V5 | **دانشگاه** University | ref 3 | Research / skills / failures. | Library hall (later) | List |
| V6 | **گفتگو** Chat with AHOS | ref 3 | Existing chat. | none (2D drawer) | same |
| V7 | **سامانه** System / launcher | — | Component health, restart (existing gated control). | none | same |
| V8 | **تنظیمات** Settings | — | Theme, sound, motion, quality, digits, calendar. | none | same |

### V3 Agent Society detail
- **Floors = the 10 council teams** from `council.ts` `TEAM_META` (`security, liquidity, onchain, news, social, macro, probability, risk, discovery, learning`). Each has a Persian name (e.g. "تیم امنیت قرارداد", "تیم نقدینگی و ریزساختار", "تیم آن‌چین و نهنگ") and a `size` (role count). Snapshot field: `teams`.
- **Desks = roles** (`roles[]` in `council.ts`).
- **Maturity state per team or agent**, using the owner's reality ladder (VISION < DESIGN < PROPOSED < PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < ACCEPTED < OPERATIONAL). **No endpoint exposes maturity today**, so the source is **UNKNOWN**, and every floor shows an UNKNOWN maturity badge until a read-only endpoint exists (Mission D8, source TO-CONFIRM: `ahos_org/registry.py`, `agent_org/projections.py`).
- **Taxonomy caveat.** Several agent taxonomies exist (council teams vs the 19 roles vs persona roster). The canonical namespace is a **human-gated decision** (C-201 / D-H262). The view shows a caption saying which taxonomy it displays: "نمای تیم‌های شورا (council.ts)" ("council teams view (council.ts)"). It never merges taxonomies.
- **Activity:** a desk glows only if runtime evidence for that agent is fresh (`council`/`votes` rows with a timestamp inside the freshness window). It is **never** animated as "thinking" without evidence (D-D07).

### V4 Evidence pipeline detail (ref 6)
- Nodes are fixed positions in RTL order, right to left. Node counts come from `opportunities[]` grouped by `canonicalStatus`, `identityState` and `securityState`, plus `overlayCensus` and `canonicalDecisions`.
- Edge particle density is proportional to the real count. Zero gives no particles and a dim edge.
- A "JEV"-style central hub becomes the **Canonical Decision Authority** node, labelled "مرجع تصمیم کانونی (پایتون)" ("canonical decision authority (Python)") so it is clear that TS doesn't decide.

---

## 6. Data source per widget

Endpoints are under `app/api/*/route.ts`. All are guarded by `authorizeDashboardEndpoint` in `web_api_auth.ts` (modes RESTRICTED / OPEN_ACCESS / LOCKED_NO_TOKEN). The client calls them through `webApiFetch` in `web_api_client.ts`. The session is bootstrapped by `POST /api/auth/session` with the launcher's one-time `#boot=` token.

`GET /api/command` returns `commandSnapshot()` from `snapshot.ts`, or `failClosedCommandSnapshot` on error. Top-level fields: `generatedAt, executionMode, realTrading, state{running,startedAt,stoppedAt,lastCycleAt,lastCycleStatus,cycleCount,lastError,intervalSec}, cycle, market, opportunities[], canonicalReadModel, overlayCensus, canonicalDecisions, news[], providers[], providerCensus{total,success,degraded}, watchlist, paper, lessons, findings, outcomes, council, votes, teams, health{dimensions[]}, blocked[]`.

| Widget | Source (exact) | Fields | Notes / truth |
|---|---|---|---|
| PAPER ONLY pill | `/api/command` | `executionMode`, `realTrading` | `executionModeStatus()` in `dashboard_truth.ts`: PAPER_ONLY → OK; other → **VIOLATION** (full-screen red bar); missing → UNKNOWN |
| System health pill | `/api/launcher` (reads `reports/launcher/status.json`) | `overall` (ONLINE/DEGRADED/…), `components{stores,db_backend,gateway,telegram,engine}.status`, `cp_status`, `paper_only` | Example of a real current value: `overall=DEGRADED` because `db_backend=UNAVAILABLE` (status.json 2026-10-08 20:23 Tehran). Show DEGRADED honestly. |
| Evidence freshness | `/api/command` | `generatedAt`, `state.lastCycleAt`, `state.intervalSec` | `deriveViewTruth()`, `freshnessStatus()`, `evidenceFreshnessLimitMs()` in `dashboard_truth.ts`. If view age >90 s, everything green becomes STALE (`presentStatus`). |
| Engine run state | `/api/command` | `state.running` | `presentRunning()`: UNKNOWN when stale |
| Globe beads / Opportunities list | `/api/command` | `opportunities[]`: `symbol, chain, decision, rankScore, confidence, securityStatus, evidenceCoverage, canonicalStatus, canonicalOutcome, identityState, securityState, paperAllowed, canonicalUnavailable, disagreement` | Bead badge from §9 mapping. `canonicalUnavailable=true` → UNKNOWN. |
| Chain rings | derived from `opportunities[].chain` | distinct chains | A ring exists only if ≥1 opportunity is on it |
| Canonical decision column | `/api/canonical` (or `canonicalDecisions` in snapshot) | `ok`, `status`, `decisions[]`; on failure `{ok:false,status:"UNAVAILABLE",no_invented_evidence:true}` | UNAVAILABLE → UNKNOWN panel |
| Opportunity dossier | `/api/command` per item | `reasonsFa, risksFa, unknownsFa, invalidationFa, missingFa, councilVerdict, disagreement, payload` | `unknownsFa` and `missingFa` are shown **as prominently as** `reasonsFa`. Danger discovery has equal weight (D-A206). |
| Alert banner | `/api/alerts` (reads `reports/pump_alert_state.json` + canonical re-check) | `active, reason, ageSec, payload{symbol,chain,decision,canonicalSecurityState}, disclaimerFa` | Fail-closed `BANNER_EVAL_FAILED` → banner hidden plus a small UNKNOWN chip |
| Live feed (news) | `/api/command` | `news[]`: `source, sourceUrl, titleFa, summaryFa, publishedAt, importance, category, sentiment` | `sourceUrl` opens **outside** the app window only on explicit click (the app profile blocks it, so copy it to the clipboard instead; Q6) |
| Providers strip | `/api/command` `providers[]`, `providerCensus`; `/api/metrics` `provider_health` | `provider, category, status, latencyMs, itemCount, messageFa` | `COST_BLOCKED` / `OUT_OF_POLICY` (e.g. X/Twitter, Instagram, TikTok in `providers.ts`) shown as neutral grey "خارج از سیاست" ("out of policy"), not as errors |
| Cycles strip (run log) | `/api/metrics` | `current_cycle`, `recent_cycles` (15), `timestamp` | Bars = real cycle durations/status only |
| Paper ledger strip | `/api/command` | `paper[]`, `watchlist[]`, `outcomes[]` | The register reports 0 closed paper exits (REMAINING_REALITY_REGISTER). The strip says "۰ معامله کاغذیِ بسته" ("0 closed paper trades"), real zero, not empty |
| Health dimensions | `/api/command` | `health.dimensions[]` (`nameFa, status, evidenceFa`), `blocked[]` | |
| Agent Society floors | `/api/command` | `teams[]` (`id, fa, size`), `council[]`, `votes[]` | Maturity: **UNKNOWN** (no endpoint; Mission D8) |
| University | — | — | **UNKNOWN / not built.** Owner rule U5: surface only after real records exist. The empty state explains this. |
| Chat | `POST /api/chat`, `GET/POST /api/chat/pending` | existing | Owner commands are confirm-gated (6-char code, 5-min TTL, D-D13) |
| Engine actions | `POST /api/engine` (`cycle`; `start`/`stop` only propose) | existing | Never one-click start/stop; always propose → confirm |
| Watch / paper actions | `POST /api/watch`, `POST /api/paper` | existing | `/api/paper` is denied unless Python canonical allows it (`CANONICAL_PAPER_DENIED`). The button is shown disabled with the server's `hintFa`. |
| Spend / ledger cost (ref 6) | — | — | **UNKNOWN.** No spend endpoint was found. The widget is omitted, not faked. |
| Terminator / sun position | client clock (computed) | — | Real astronomy, computed |
| Tehran home mark | constant (35.69°N, 51.39°E) | — | Static fact |

---

## 7. Component states (every widget implements all of them)

| State | Visual | Copy (fa) | Sound |
|---|---|---|---|
| **Loading** | Gold shamseh halo rotates slowly (static in reduced-motion), skeleton lines in `panel-edge`. **No fake numbers.** | "در حال دریافت…" ("fetching…") | none |
| **Empty (real zero)** | The real "۰" in Vazirmatn muted with a one-line reason | e.g. "هنوز فرصتی ثبت نشده" ("no opportunity recorded yet") | none |
| **UNKNOWN** | Dashed slate border, hatch, "?" | "نامعلوم — منبع: …" plus what is missing ("unknown — source: …") | neutral tick (optional) |
| **STALE** | Dotted brass, clock, age shown ("۳ دقیقه پیش", "3 minutes ago") | "کهنه — آخرین به‌روزرسانی …" ("stale — last update …") | none |
| **Error** | Red octagon chip; message from `sanitizePublicError` (never raw stack) | "خطا — داده نمایش داده نمی‌شود" ("error — data not shown") + retry | low thud once |
| **Locked (auth)** | Lock glyph; `WEB_API_LOCKED_NO_TOKEN` → "از آیکون AHOS دوباره باز کنید" ("reopen from the AHOS icon") | | none |
| **Provider credit exhausted** | Amber-free neutral panel | Persian message required by D-D07: credit ran out, mission paused, checkpoint kept, new key needed | none |

---

## 8. Motion and sound

### 8.1 Motion principles
- **One hero motion at a time.** Idle shows the globe at 0.5°/s, with the terminator updating every 60 s and nothing else moving.
- **Durations:** micro 120–180 ms; panel 240–320 ms (`cubic-bezier(.2,.8,.2,1)`); camera flights 900–1400 ms. Flights are interruptible, and a second click cancels.
- **Meaning-bound motion:** only *new real events* animate (a new canonical decision, a new alert). VERIFIED arrival plays a gold ring pulse once. UNKNOWN and CONFLICT never pulse or glow; they appear by a 200 ms fade.
- **Reduced motion** (`prefers-reduced-motion: reduce` **or** the in-app toggle): no camera flights (cut instead), no particles, no rotation, boot replaced by a static seal. WCAG 2.3.3 and 2.2.2 apply (any loop >5 s gets a pause control; the top bar has a ⏸).

### 8.2 Sound design
- **Starts muted.** The top bar has a 🔇 toggle (shortcut `M`) and a volume slider (0–100, default 40 when first unmuted), persisted in localStorage. The AudioContext is created only on the first unmute (a user gesture).
- **Engine:** Web Audio API. One `AudioContext` with master gain, three buses (ambience / UI / events) and a compressor. Spatial events use `PannerNode` with `panningModel:'HRTF'`, attached to 3D objects (three.js `PositionalAudio`). A conflict on the left ring sounds from the left.
- **Palette:** a low drone tuned to D (ambience, −30 LUFS integrated, filtered by camera altitude), with soft santur-like plucks for UI focus. Plucks are procedural (Karplus-Strong) or Kenney CC0.
- **Truth sounds** (hard rule, mirrors §9):
  - VERIFIED: a warm perfect-fifth chime, once.
  - UNKNOWN: **no** tonal sound, or a dry neutral tick.
  - CONFLICT: a **dissonant low minor-second dyad**, short.
  - REJECTED / VIOLATION: a low thud.
  - **No success-sounding cue may ever play for UNKNOWN or CONFLICT.**
- **Rate limit:** at most 1 event sound per 2 s, with batching ("۳ رویداد جدید", "3 new events"). Silent when the window is hidden (`visibilitychange`).
- **Assets:** ≤3 MB total, OGG (Opus/Vorbis), bundled under `public/audio/` (TO-CONFIRM: the repo has **no `public/` dir** today). Credits go in `SOUND_CREDITS.md`. CC0 only.

---

## 9. Truth badge rules (normative)

The `TruthBadge` component accepts **only** these states: `VERIFIED | UNKNOWN | CONFLICT | STALE | REJECTED`. Mapping from server fields is a **pure function** with a selftest, in the style of `dashboard_truth.ts`.

1. **VERIFIED** only when *all* hold: the server reports a canonical status equivalent to PASS/verified for that item, the view is fresh (`deriveViewTruth().stale === false`), and `canonicalUnavailable !== true`. Exact enum values are TO-CONFIRM in M-D3 from `canonical_read_model.ts`.
2. **CONFLICT** when `disagreement === true`, or identity/security states report conflict (e.g. the identity two-source gate disagrees; exact enum TO-CONFIRM). **CONFLICT outranks VERIFIED.**
3. **UNKNOWN** when any required field is null/missing, the canonical model is UNAVAILABLE, or a security overlay is INCOMPLETE. Local OBSERVED/UNKNOWN is "not security authority" (AGENTS.md).
4. **STALE** when the item or view exceeds freshness limits. A stale VERIFIED shows **STALE**, never green (`presentStatus`).
5. **REJECTED** when canonical says REJECT or the security gate rejects.
6. **Precedence:** REJECTED > CONFLICT > UNKNOWN > STALE > VERIFIED.
7. **Styling invariants (tested):**
   - UNKNOWN and CONFLICT never use `#2EC4A6`, the gold accent, a ✓ glyph, glow or bloom layers, pulse animation, or the VERIFIED sound.
   - Badge text is always present (fa label + Latin code), so colour is never the only cue.
8. The UI may **downgrade** display (e.g. to STALE) but never **upgrade** a server state.

---

## 10. Accessibility

- Text contrast ≥4.5:1 (all text tokens §2 pass) and focus ring 2px `gold` with 2px offset.
- Every 3D-only affordance has a DOM equivalent. Globe beads mirror into a hidden-but-focusable list ordered by `rankScore`, and Tab cycles beads.
- Screen readers get `aria-live="polite"` for new events and `assertive` only for VIOLATION.
- Full keyboard operation (§4 shortcuts). Hit targets ≥32px.
- A font-size scale of 90–130% in Settings, and a layout that survives 130%.
- Never flash more than 3 times/s (WCAG 2.3.1). Bloom pulses use ≤2 Hz.

---

## 11. Modes: reduced motion, low power, 2D fallback

| Mode | Trigger | Behaviour |
|---|---|---|
| **High** | detect-gpu tier ≥2 and measured ≥50 fps | DPR ≤1.5, bloom + vignette + SMAA, particles on, shadows baked |
| **Low-power** | Battery not charging (`navigator.getBattery` if available), tier 1, `PerformanceMonitor` decline, or user toggle | DPR 1.0, no postprocessing except vignette, no particles, `frameloop="demand"` (render only on change), 30 fps cap |
| **Reduced motion** | OS `prefers-reduced-motion` or toggle | See §8.1. Combinable with any tier. |
| **2D** | Tier 0, WebGL2 unavailable, context loss twice, fps <24 for 5 s, or `F2`/toggle | No WebGL context at all; SVG ring diagram + tables + React Flow graph. **Same data, same badges.** The three.js chunk is never downloaded. |

- On a `webglcontextlost` event, fall to 2D immediately with a Persian toast, and offer a retry.
- When the window is hidden or minimised, the render loop stops completely.

---

## 12. Performance budget (laptop integrated GPU, 8 GB RAM)

| Metric | Budget | How measured |
|---|---|---|
| First 2D paint (production `next start`, not `next dev`, per D-B13) | ≤1.5 s after the window opens (gateway already up) | Performance API mark |
| 3D chunk (three + r3f + drei + postprocessing + scene) | ≤650 KB gzip, lazy `dynamic(() => import(...), {ssr:false})` | `next build` output |
| Steady FPS, High tier, 1920×1080 | ≥50 fps target, ≥30 fps floor | r3f-perf (dev) and an in-app FPS meter (Settings → diagnostics) |
| Frame time GPU | ≤12 ms High / ≤8 ms Low | r3f-perf |
| Draw calls | ≤120 | r3f-perf |
| Triangles | ≤250k | r3f-perf |
| GPU textures | ≤64 MB total; max texture 2048² | r3f-perf / Chrome GPU memory |
| Renderer process RAM | ≤400 MB | Chrome task manager (Shift+Esc) |
| CPU while idle (window visible, no new data) | ≤5% of one core (Low: ≤2%) | Windows Task Manager |
| CPU while hidden | ~0% render (loop stopped) | Task Manager |
| Audio assets | ≤3 MB | file sizes |
| Fonts | ≤600 KB woff2 total (subset Lalezar/Markazi/Nastaliq to used glyphs) | file sizes |

**Techniques:**
- InstancedMesh for beads and land dots, one merged ring geometry per chain, and baked lighting for the tower.
- One postprocessing composer, an adaptive DPR, and no realtime shadows.
- No HDR environment fetch (drei presets fetch from raw.githack; forbidden). A procedural gradient env is used instead.

---

## 13. Stack recommendation (evaluated against the repo)

- **Inside the existing Next.js 16.3.8 app** (`app/page.tsx` renders the root-level `CommandCenter.tsx`, 1,371 lines). Add `three`, `@react-three/fiber` 9.x (peer `react >=19 <19.4`, which matches the repo's 19.2.6), `@react-three/drei` 10.x, `@react-three/postprocessing` 3.x + `postprocessing` 6.x (peer `three <0.187`, so pin `three@0.186.x`), `three-globe`, `world-atlas` + `topojson-client`, `detect-gpu` (self-hosted benchmarks), `zustand`, and `reactflow`/`@xyflow/react` for 2D. Use plain Web Audio, no Howler. **Adding dependencies needs owner approval** (the continuity notes say an npm install needs approval).
- **Prior art in the repo:** five excluded prototype folders (`advanced-3d-audiovisual-website`, `advanced-3d-audiovisual-website (1)`, `درخت کاملتر immersive-3d-audiovisual-website`, `سایت درختadvanced-3d-audiovisual-platform`, `01`) already use `three@^0.185`, r3f 9.7, drei 10.7 and react-postprocessing 3.1. They are excluded from `tsconfig.json` and are not wired in. Review them before building (M-D5) so nothing is duplicated (owner rule: no duplicates, no blind rewrite).
- **Window:** Chrome or Edge `--app` with a dedicated `--user-data-dir`, launched by the existing launcher (Mission 1). Both are installed: `C:\Program Files\Google\Chrome\Application\chrome.exe` and `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`. Tauri only if a hard need appears (single-instance focus, tray, no browser at all). Electron is not justified on 8 GB RAM.
- **Fonts:** move from `next/font/google` (downloads from Google at build time) to `next/font/local`.

---

## 14. Emblem and icon

- A 3D coin (procedural geometry, no external model): lathe-turned black-lacquer disc with clearcoat, a gold rim (metalness 1, roughness 0.28), and an extruded five-point star with the abstract figure from ref 4. A specular sweep plays once on load.
- A Faravahar wing motif (our own vector) is engraved faintly on the rim's reverse, visible when the coin flips in the loader.
- The app icon refresh goes through the existing `launcher/make_icon.py` → `launcher/ahos.ico` path. That is a separate, owner-approved step, because the `.lnk` points at `G:\robat\ahos\launcher\ahos.ico,0`.

---

## 15. Open questions (for Mehrdad)

See the list at the end of `CLAUDE_BUILD_MISSIONS.md` (Q1–Q10).
