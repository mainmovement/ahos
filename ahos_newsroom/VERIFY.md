# VERIFY.md — commands actually run, and their real output

Environment: **Node v22.22.3 · npm 10.9.8** · Linux x86_64 · offline (npm registry only, no other network).
Workspace: `ahos_newsroom/` — built from scratch in this folder, nothing imported from the parent repo.

```
$ npm ci --no-audit --no-fund
npm warn deprecated eslint@9.39.5: This version is no longer supported. Please see https://eslint.org/version-support for other options.

added 456 packages in 11s
exit=0
```

(The lockfile is committed, so `npm ci` and `npm install` produce the same tree. The dev server and
every screenshot below were produced from this clean install.)

---

## 1 · Type check

```
=== npm run typecheck ===

> ahos-newsroom@0.1.0 typecheck
> tsc --noEmit

exit=0
```

## 2 · Lint

```
=== npm run lint ===

> ahos-newsroom@0.1.0 lint
> eslint .

exit=0
```

## 3 · Tests

```
=== npm test ===

> ahos-newsroom@0.1.0 test
> vitest run


 RUN  v5.0.5 /home/user/ahos/ahos_newsroom

 ✓ src/features/newsroom/__tests__/NewsroomPage.test.tsx (16 tests) 1208ms
 ✓ src/features/newsroom/lib/__tests__/truth.test.ts (29 tests) 539ms
 ✓ src/features/newsroom/__tests__/PaperOnlyGuard.test.tsx (8 tests) 71ms
 ✓ src/components/truth/__tests__/TruthChip.test.tsx (8 tests) 63ms
 ✓ tests/forbidden-controls.test.ts (5 tests) 21ms
 ✓ src/features/newsroom/lib/__tests__/pipeline.test.ts (9 tests) 7ms
 ✓ src/features/newsroom/lib/__tests__/format.test.ts (8 tests) 9ms

 Test Files  7 passed (7)
      Tests  83 passed (83)
   Start at  17:31:39
   Duration  7.86s (environment 58%, tests 27%, setup 11%, import 1%, transform 1%, worker 1%)

Environment  jsdom was created 7 times · 4.16s total, 58% of tracked time
             create it once per worker with pool: 'vmThreads' (keeps per-file isolation) or isolate: false (shares it across files)
             learn more: https://vitest.dev/guide/improving-performance#test-environments

exit=0
```

## 4 · Production build

```
=== npm run build ===

> ahos-newsroom@0.1.0 build
> next build

▲ Next.js 16.4.2 (Turbopack)
✓ Running next.config.ts took 31ms

  Creating an optimized production build ...
✓ Compiled successfully in 4.9s
  Running TypeScript ...
  Finished TypeScript in 3.9s ...
  Collecting page data using 1 worker ...
  Generating static pages using 1 worker (0/3) ...
✓ Generating static pages using 1 worker (3/3) in 131ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
└ ○ /_not-found


○  (Static)  prerendered as static content

exit=0
```

## 5 · Run + screenshot

Dev server:

```
$ npm run dev

> ahos-newsroom@0.1.0 dev
> next dev -H 0.0.0.0 -p 3000

▲ Next.js 16.4.2 (Turbopack)
- Local:         http://localhost:3000
- Network:       http://0.0.0.0:3000
✓ Ready in 331ms
```

Screenshots were captured with headless Chromium at **1600×900**, waiting for the relevant
`data-testid` and for `document.fonts.ready` on every shot:

```
$ node shoot.mjs
✓ 01-calm-demo-oil-gold.png  /
✓ 02-conflict-board.png  /?story=nws-oil-0143
✓ 03-violation-bar.png  /?violation=1
✓ 04-empty.png  /?state=empty
✓ 05-unavailable.png  /?state=unavailable
✓ 06-tier0.png  /?tier=0
✓ 07-details-table.png  /?details=1
✓ 08-error.png  /?state=error
✓ 09-forced-demo-all.png  /?demo=1
✓ 10-tier2-glass.png  /?tier=2
done
```

Automated rendering checks (Chromium, DOM measured after `document.fonts.ready`):

| Check | Result |
| --- | --- |
| `document.fonts.status` | `loaded` |
| loaded families | `AH Vazirmatn Latin`, `AH Vazirmatn FA`, `AH Inter` |
| `document.fonts.check('14px "AH Vazirmatn FA"')` | `true` |
| document `scrollHeight` vs viewport (1600×900) | `900 / 900` — no overflow, in every scenario |
| elements clipped by `overflow:hidden` | `0` |
| console errors | `0` |
| computed colour of a `[data-status="UNKNOWN"]` chip | `rgb(107, 116, 128)` (grey) |
| computed colour of a `[data-status="LIVE"]` chip | `rgb(139, 191, 166)` |
| computed colour of a `[data-status="CONFLICT"]` chip | `rgb(227, 148, 148)` |
| computed colour of a `[data-status="DEMO"]` chip | `rgb(217, 185, 119)` (gold) |
| story cards on the calm view | `7` |
| conflict cards | `2` |
| reporter rows | `6` |
| pipeline stages | `5` |
| market pills | `4` (2 connected · 2 PLANNED) |
| DEMO ribbons | `7` (one per mock-backed panel) |
| pipeline stage states for the conflict story | `DONE · DONE · DONE · CURRENT · PLANNED` |
| pipeline stage states for a DEMO story | `DONE · DONE · UNKNOWN · UNKNOWN · PLANNED` |

## 6 · Files delivered

```
./.gitignore
./LICENSES.md
./README.md
./README_MERGE.md
./eslint.config.mjs
./next-env.d.ts
./next.config.ts
./package-lock.json
./package.json
./postcss.config.mjs
./public/fonts/LICENSE-Inter.txt
./public/fonts/LICENSE-Vazirmatn.txt
./public/fonts/inter-latin-400-normal.woff2
./public/fonts/inter-latin-500-normal.woff2
./public/fonts/inter-latin-600-normal.woff2
./public/fonts/inter-latin-700-normal.woff2
./public/fonts/inter-latin-ext-400-normal.woff2
./public/fonts/inter-latin-ext-500-normal.woff2
./public/fonts/inter-latin-ext-600-normal.woff2
./public/fonts/inter-latin-ext-700-normal.woff2
./public/fonts/vazirmatn-arabic-300-normal.woff2
./public/fonts/vazirmatn-arabic-400-normal.woff2
./public/fonts/vazirmatn-arabic-500-normal.woff2
./public/fonts/vazirmatn-arabic-600-normal.woff2
./public/fonts/vazirmatn-arabic-700-normal.woff2
./public/fonts/vazirmatn-arabic-800-normal.woff2
./public/fonts/vazirmatn-latin-300-normal.woff2
./public/fonts/vazirmatn-latin-400-normal.woff2
./public/fonts/vazirmatn-latin-500-normal.woff2
./public/fonts/vazirmatn-latin-600-normal.woff2
./public/fonts/vazirmatn-latin-700-normal.woff2
./public/fonts/vazirmatn-latin-800-normal.woff2
./screenshots/01-calm-demo-oil-gold.png
./screenshots/02-conflict-board.png
./screenshots/03-violation-bar.png
./screenshots/04-empty.png
./screenshots/05-unavailable.png
./screenshots/06-tier0.png
./screenshots/07-details-table.png
./screenshots/08-error.png
./screenshots/09-forced-demo-all.png
./screenshots/10-tier2-glass.png
./src/app/globals.css
./src/app/layout.tsx
./src/app/page.tsx
./src/components/truth/TruthChip.tsx
./src/components/truth/__tests__/TruthChip.test.tsx
./src/components/truth/index.tsx
./src/features/newsroom/NewsroomPage.tsx
./src/features/newsroom/__tests__/NewsroomPage.test.tsx
./src/features/newsroom/__tests__/PaperOnlyGuard.test.tsx
./src/features/newsroom/components/CapsuleDock.tsx
./src/features/newsroom/components/ConflictBoard.tsx
./src/features/newsroom/components/JudgeHandoffTile.tsx
./src/features/newsroom/components/MarketFocusPills.tsx
./src/features/newsroom/components/PaperOnlyGuard.tsx
./src/features/newsroom/components/ReporterRoster.tsx
./src/features/newsroom/components/SourceStrip.tsx
./src/features/newsroom/components/StoryDossier.tsx
./src/features/newsroom/components/StoryInbox.tsx
./src/features/newsroom/components/TelemetryStrip.tsx
./src/features/newsroom/components/Topbar.tsx
./src/features/newsroom/components/VerificationPipeline.tsx
./src/features/newsroom/components/ViolationBar.tsx
./src/features/newsroom/components/icons.tsx
./src/features/newsroom/components/primitives.tsx
./src/features/newsroom/lib/__tests__/format.test.ts
./src/features/newsroom/lib/__tests__/pipeline.test.ts
./src/features/newsroom/lib/__tests__/truth.test.ts
./src/features/newsroom/lib/format.ts
./src/features/newsroom/lib/labels.ts
./src/features/newsroom/lib/pipeline.ts
./src/features/newsroom/lib/selectors.ts
./src/features/newsroom/lib/tier.ts
./src/features/newsroom/lib/truth.ts
./src/features/newsroom/lib/types.ts
./src/mock/newsroom/adapters.ts
./src/mock/newsroom/fixtures.ts
./src/mock/newsroom/index.ts
./tests/forbidden-controls.test.ts
./tsconfig.json
./tsconfig.tsbuildinfo
./vitest.config.mts
./vitest.setup.ts
```

---

Everything above is a verbatim transcript. `npm run verify` (typecheck → lint → test → build) exits **0**.

---

## 7 · Zip round-trip

The deliverable `ahos_newsroom.zip` was unpacked into a clean directory and run end-to-end, so the
transcript above is not just about the working copy:

```
$ rm -rf /tmp/zipcheck && mkdir -p /tmp/zipcheck && cd /tmp/zipcheck
$ unzip -q ahos_newsroom.zip && cd ahos_newsroom
$ npm ci --no-audit --no-fund
added 456 packages in 10s

$ npm run typecheck
> tsc --noEmit
(no output, exit 0)

$ npm test
 Test Files  7 passed (7)
      Tests  83 passed (83)

$ npm run build
Route (app)
┌ ○ /
└ ○ /_not-found
○  (Static)  prerendered as static content

$ npx next dev -H 0.0.0.0 -p 3100
▲ Next.js 16.4.2 (Turbopack)
✓ Ready in 397ms
 GET / 200 in 377ms
```

Contents of the archive: **102 files**, 20 `woff2` fonts, 10 `1600×900` PNG screenshots, zero
`node_modules`, zero `.next`.

```
3.4M  ahos_newsroom.zip
```
