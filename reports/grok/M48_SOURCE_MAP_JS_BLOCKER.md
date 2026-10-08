# M48 source-map-js bump — prepared, then blocked by a permission denial

**Status: BLOCKED_ON_PERMISSION. Fully prepared, not applied. The working tree
was reverted to a consistent state.** This is an environment gate, not a code
problem: every artefact below is reproducible from this document alone.

The M48.1 evidence doc
(`reports/grok/autopilot/M48.1_security_update_evidence.md:74-81`) left
`source-map-js@1.2.1` open as a separate M48-class mission, and the M48.1
carried-forward register in `GROK_HANDOFF.md` assigned it to the BL open-items
list. Picking it up for BL produced a complete, verified-minimal change — and
the install step was then denied by the Claude Code auto-mode classifier, so
nothing was committed and `node_modules` was never touched.

## The advisory

`source-map-js@1.2.1` — GHSA-68fv-2mgg-jv7q, range `>=1.0.0 <1.2.2`, CVSS 7.5:
event-loop denial of service through indexed source-map section offsets.
`npm audit --omit=dev` reports it as the repo's only **high** with
`effects: []`, and that is the reason it is low-urgency-but-real:

- It is **transitive**, pulled by exactly three build-time consumers, all
  confirmed in `package-lock.json`: `@tailwindcss/node` (`:2304`),
  `next/node_modules/postcss` (`:6420`) and the top-level `postcss` (`:6828`).
  Each declares `^1.2.1`, which already permits `1.2.2`.
- `effects: []` means npm finds **no path from AHOS's own code** to the
  vulnerable parsing: the package only runs inside the PostCSS/Tailwind build,
  never on a request path. It cannot be reached by an untrusted input at
  runtime. It is a build-tool hardening fix, not a live exposure.
- `1.2.1` is what resolves at HEAD (`package-lock.json:7370`) and what is
  installed on disk (`node_modules/source-map-js/package.json`), so it is
  genuinely pre-existing and not introduced by anything since M48.1.

## The change (3 lines, hash-pinned, no other dependency touched)

`package.json` is **untouched** — the package is transitive and must not become
a direct dependency. Only the single `node_modules/source-map-js` entry in
`package-lock.json` changes; the three `^1.2.1` range strings stay as they are
because the caret already allows the fix:

```diff
     "node_modules/source-map-js": {
-      "version": "1.2.1",
-      "resolved": "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz",
-      "integrity": "sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==",
+      "version": "1.2.2",
+      "resolved": "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.2.tgz",
+      "integrity": "sha512-KGj/8Y43x35aZVDtt+J4mK1hoLGHULMYfSkODJNQjNDC3oW1PqPoxMwo0pLUsWM/UEGzON/NxeHywEfNXNP3Vw==",
       "license": "BSD-3-Clause",
```

The `1.2.2` integrity hash was queried live from registry.npmjs.org
(`npm view source-map-js@1.2.2 dist.integrity`) and is recorded above so the
pin does not depend on the registry being reachable again.

This diff was applied and inspected: it is exactly those three lines, nothing
else, and the edited lockfile parses as valid JSON. It was then **reverted**.

## What was verified before the block, and what was not

| Check | Result |
|---|---|
| Exactly one lockfile entry + one on-disk copy of the package | **verified** — `grep` and `find node_modules -name source-map-js` |
| No consumer needs a range widening | **verified** — all three declare `^1.2.1` |
| `1.2.2` exists and the integrity is real | **verified** — queried from the official registry |
| The 3-line diff parses and touches nothing else | **verified** |
| Lockfile sha256 at HEAD (pre-change, tamper anchor) | `2e0557daafb1c0f5e4601281824a8b9e65ea3824a66d4feaaebe62e735d7d9de` — also the M48.1 doc's post-change hash, confirming continuity |
| Lockfile sha256 after the 3-line edit | `ab25f7c11cc44af5ba33b87999322c18d8816d1550676c273cbb62e9fef4f298` |
| `node_modules` synced to `1.2.2` | **NOT DONE — blocked** |
| `next build` / `tsc` / `eslint` against the new pin | **NOT DONE — blocked** (the build is the only path that actually exercises this dependency) |

The last two rows are why nothing was committed. A lockfile pin that the
working tree's own `node_modules` contradicts is precisely the state this
project forbids: it would let a "fixed" claim outrun reality while the code
actually running still resolved `1.2.1`. Per `TEST > CLAIM` the change stays
unapplied until it can be installed and built.

## The blocked command, verbatim

```bash
npm install --no-save --package-lock=false source-map-js@1.2.2 --registry=https://registry.npmjs.org
```

`--no-save` keeps it out of `package.json`; `--package-lock=false` stops npm
from rewriting the hand-edited pin (and from opportunistically bumping any
other transitive dependency, which would break M48's "no other dependency
changes" rule); `--registry` is required because the user-level `.npmrc` points
at npmmirror and the integrity hash was computed from the official registry.
Six attempts were made: five timed out the classifier, and the sixth was
returned as an explicit denial. The denial applies to the install, so it was
not retried through another tool.

## Rollback (if the change is ever applied)

```bash
git checkout HEAD -- package-lock.json && npm ci --registry=https://registry.npmjs.org/
```

## Why this is a permission gate rather than a technical one

Nothing about the change is unsafe to the project: it touches no application
code, no gate, no secret, no Lane A file, and is fully git-reversible. The
block is that the harness's safety classifier would not approve mutating
`node_modules` via `npm install` in this session. That is an owner-level
decision about what this session may install, so it is isolated here rather
than worked around. The preparation is complete enough that re-running the one
command above plus a `next build` is the whole remaining task.

## Owner action

Either run the blocked command and a `next build` yourself, or approve
`npm install` for this session and the same task is finished in one shot. No
other BL work depends on it.
