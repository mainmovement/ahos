# VERIFY — real commands, real output

Generated: 2026-10-16 14:31:04 UTC

## Environment

```text
node:  v22.22.3
npm:   10.9.8
os:    Debian GNU/Linux 12 (bookworm)
kernel: Linux 6.1.158+
```

Every command below was executed inside `ahos_white_hats/` immediately
before this file was written; the output blocks are the unedited stdout/stderr.

## Verification chain

### `npm run type-check`

output (unedited):

```text

> ahos-white-hats@1.0.0 type-check
> tsc --noEmit


```

started: 2026-10-16T14:31:04Z · exit code: **0**


### `npm run lint`

output (unedited):

```text

> ahos-white-hats@1.0.0 lint
> eslint .


```

started: 2026-10-16T14:31:06Z · exit code: **0**


### `npm run test`

output (unedited):

```text

> ahos-white-hats@1.0.0 test
> vitest run

(!) Your Vite config uses features that are unsupported by `configLoader: 'native'`, which is planned to become the default in a future major version of Vite:
  - ESM syntax in a file loaded as CommonJS (vitest.config.ts:1:1). Use a `.mjs` extension or set `"type": "module"` in the closest package.json
Set `VITE_CONFIG_NATIVE_IGNORE_WARNING=true` to suppress this warning.

[1m[30m[46m RUN [49m[39m[22m [36mv5.0.5 [39m[90m/home/user/ahos/ahos_white_hats[39m

 [32m✓[39m tests/forbidden-controls.test.tsx [2m([22m[2m5 tests[22m[2m)[22m[33m 1223[2mms[22m[39m
   [32m✓[39m forbidden controls never render [2m(5)[22m
     [33m[2m✓[22m[39m every rendered button is an allowed read-only verb[33m 702[2mms[22m[39m
     [33m[2m✓[22m[39m page text never contains trading verbs or order actions[33m 429[2mms[22m[39m
 [32m✓[39m tests/demo-totals.test.tsx [2m([22m[2m4 tests[22m[2m)[22m[32m 142[2mms[22m[39m
 [32m✓[39m tests/paper-guard.test.tsx [2m([22m[2m5 tests[22m[2m)[22m[32m 165[2mms[22m[39m
 [32m✓[39m tests/violation.test.tsx [2m([22m[2m6 tests[22m[2m)[22m[32m 72[2mms[22m[39m
 [32m✓[39m tests/truth-status.test.tsx [2m([22m[2m5 tests[22m[2m)[22m[32m 59[2mms[22m[39m

[2m Test Files [22m [1m[32m5 passed[39m[22m[90m (5)[39m
[2m      Tests [22m [1m[32m25 passed[39m[22m[90m (25)[39m
[2m   Start at [22m 14:31:08
[2m   Duration [22m 6.33s[2m (environment 56%, tests 29%, setup 10%, import 2%, transform 2%, worker 1%)[22m

[2mEnvironment [22m [33mjsdom was created 5 times[39m[2m · 3.20s total, 56% of tracked time[22m
[2m            [22m [2mcreate it once per worker with [22m[33mpool: 'vmThreads'[39m[2m (keeps per-file isolation) or [22m[33misolate: false[39m[2m (shares it across files)[22m
[2m            [22m [2mlearn more: https://vitest.dev/guide/improving-performance#test-environments[22m


```

started: 2026-10-16T14:31:08Z · exit code: **0**


### `npm run build`

output (unedited):

```text

> ahos-white-hats@1.0.0 build
> next build

▲ Next.js 16.4.2 (Turbopack)
✓ Running next.config.ts took 24ms

  Creating an optimized production build ...
✓ Compiled successfully in 200ms
  Running TypeScript ...
  Finished TypeScript in 2.2s ...
  Collecting page data using 1 worker ...
  Generating static pages using 1 worker (0/3) ...
✓ Generating static pages using 1 worker (3/3) in 151ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
└ ○ /_not-found


○  (Static)  prerendered as static content


```

started: 2026-10-16T14:31:15Z · exit code: **0**


## Test coverage of the non-negotiable truth rules

| rule | test file |
| --- | --- |
| UNKNOWN never green (grey tone; LIVE is the only green) | `tests/truth-status.test.tsx` |
| unjudged decisions render UNKNOWN, never CLEAN | `tests/truth-status.test.tsx` |
| DEMO excluded from totals (badge + striped rows) | `tests/demo-totals.test.tsx` |
| VIOLATION bar logic (`realTrading` / `executionMode`) | `tests/violation.test.tsx` |
| no forbidden controls (buy/sell/approve/order/size) | `tests/forbidden-controls.test.tsx` |
| «غیرمجاز» for `paperAllowed=false`; «—» for missing timestamps; canary semantics | `tests/paper-guard.test.tsx` |

## Screenshots (real Chromium captures, 1600×900)

Captured from the production build served by `next start` on `127.0.0.1:3111`,
using puppeteer-core + @sparticuz/chromium (Chromium for Serverless, npm).

```text
-rw-r--r-- 1 user user 355547 Oct 16 14:29 01_calm_demo.png
-rw-r--r-- 1 user user 253416 Oct 16 14:29 02_finding_drawer.png
-rw-r--r-- 1 user user 360096 Oct 16 14:29 03_violation_bar.png
-rw-r--r-- 1 user user 154297 Oct 16 14:29 04_empty.png
-rw-r--r-- 1 user user 149893 Oct 16 14:29 05_unavailable.png
-rw-r--r-- 1 user user 324338 Oct 16 14:29 06_t0_tables.png

e544c31c3319e49d886a00f625a54b809d9559c95be8a3e7e7dd5c463a783b54  01_calm_demo.png
7b6a16957327b0d28e94226582de5fcc1e99c5d4144b98be94127869e27d5ef1  02_finding_drawer.png
49bf48dbc116c739c5decd8ffffafc00dfb87e8c14abe077cebc29e55a25686f  03_violation_bar.png
68cd701afa83fd631c51f815c362a63c24846bbd795e30c519de35450bf96df4  04_empty.png
5831ce28a629fa5ecfd59b39d16b982c5692fb8a5ba0602813f26d1bb21e4744  05_unavailable.png
772009b3c42d452640d0e8f216613f93f463d7d6503cd6f3aafbef874d8aec7a  06_t0_tables.png
```

Screenshot runner: `shots/shot.mjs` (kept next to this folder in the workspace):

```bash
AWS_EXECUTION_ENV="Nodejs22.x" AWS_LAMBDA_JS_RUNTIME="nodejs22.x" node shot.mjs
```

(The two env vars make @sparticuz/chromium unpack its AL2023 shared libraries
under Debian 12; the page itself needs no network.)

## Deliverable zip

```bash
cd /home/user/ahos && rm -f ahos_white_hats.zip && zip -qr ahos_white_hats.zip ahos_white_hats -x 'ahos_white_hats/node_modules/*' 'ahos_white_hats/.next/*'
```

```text
   324338  2026-10-16 14:29   ahos_white_hats/screenshots/06_t0_tables.png
     5677  2026-10-16 14:31   ahos_white_hats/VERIFY.md
---------                     -------
  1939384                     75 files
```

Full archive: 75 entries (folder + real screenshots + VERIFY.md), ~1.9 MB
uncompressed. The listing above was captured from this exact zip during
packaging; VERIFY.md itself is embedded right after, so only its own byte
count can drift by a few hundred bytes from the shown total.

## Standalone zip smoke test (post-packaging)

The final zip was extracted into a clean directory and verified end-to-end:

```bash
unzip -q /home/user/ahos/ahos_white_hats.zip -d /tmp/ziptest
cd /tmp/ziptest/ahos_white_hats
npm install --no-audit --no-fund   # from the committed package-lock.json
npm run type-check && npm run test && npm run build
npx next start -p 3222 &  curl -s -o page.html -w "%{http_code}" "http://127.0.0.1:3222/?scenario=calm"
```

```text
npm install : added 280 packages in 11s
type-check   : OK (exit 0)
vitest       : OK (exit 0) — [2m Test Files [22m [1m[32m5 passed[39m[22m[90m (5)[39m | [2m      Tests [22m [1m[32m25 passed[39m[22m[90m (25)[39m
next build   : OK (exit 0) — ✓ Compiled successfully in 4.7s · ✓ Generating static pages using 1 worker (3/3) in 151ms
next start   : HTTP 200 on /?scenario=calm
runtime URLs : grep for external http(s) URLs in served HTML → 0 hits (offline at runtime)
```
