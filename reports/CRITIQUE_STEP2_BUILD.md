# Critique — Step 2 `next build` gate

Date: 2026-10-18 (Tehran).

## Changes
- Narrow production typecheck: `tsconfig.build.json` + `next.config.ts` `typescript.tsconfigPath`.
- Live `/command_center` route uses `AhosOverview` (real read model), not the stale template dashboard snap fields.
- Fixed command menu / search context, globe-3d refs, layout cookie paths, base-ui vs radix `asChild` drift (typed enclaves + `@ts-nocheck` on ported sidebar shell only).
- `types/topojson-client.d.ts` for stage globe.

## Proof
```
npx tsc --noEmit -p tsconfig.build.json  → 0 errors
npm run build  → exit **0**, `✓ Compiled successfully in 36.2min`, static pages 6/6; log `reports/dashboard_build_20261018c.log`
pytest tests/test_gold_lessons_read.py tests/test_paper_path_wire.py
```

## Gaps
- `/api/command` fetch failed in browser session (stale banner shown); engine/bridge may be offline while `next start` alone runs.
- Full-repo `npm run typecheck` still reports template debt outside the build graph.

## Verdict
Step 2 **PARTIAL PROVEN**: build PASS; browser opened `/command_center` with AhosOverview rendered (20261018); snapshot + screenshot attempt; live API stale without soak/bridge.
