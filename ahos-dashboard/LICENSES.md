# Licenses — AHOS Dashboard

This document lists every dependency and every asset shipped with `ahos-dashboard/`.
No paid APIs, no external fonts/images/CDNs and no runtime network calls are used.

## 1. Assets

| Asset | Location | Source | License |
|---|---|---|---|
| Vazirmatn (variable woff2) | `public/fonts/Vazirmatn-Variable.woff2` | `vazirmatn@33.0.3` npm package (Saber Rastikerdar & contributors) | SIL Open Font License 1.1 — full text: `public/fonts/OFL-Vazirmatn.txt` |
| Inter (variable woff2, latin subset) | `public/fonts/Inter-Variable-latin.woff2` | `@fontsource-variable/inter@5.3.0` (The Inter Project Authors) | SIL Open Font License 1.1 — full text: `public/fonts/OFL-Inter.txt` |
| World land / countries (TopoJSON) | `public/geo/land-50m.json`, `land-110m.json`, `countries-110m.json` | Natural Earth via `world-atlas@2.0.2` (Mike Bostock) | Natural Earth data: **public domain**; world-atlas package: ISC — `public/geo/LICENSE-world-atlas.txt` |
| Iran outline (GeoJSON) | `public/geo/iran-50m.geo.json` | Extracted from Natural Earth 1:50m countries (`scripts/sync-assets.mjs`) | public domain (Natural Earth) |
| City light positions | `src/components/globe/city-lights.ts` | Hand-compiled approximate coordinates/populations of major metro areas (public geographic facts) | part of this project |
| Globe textures (day / night / mask) | generated at runtime | Procedural canvas rendering in `src/components/globe/textures.ts` | part of this project (no imagery) |
| AHOS emblem (gold star + figure) | `src/components/layout/logo.tsx`, `src/app/icon.svg` | Vector re-drawing inspired by the brand reference supplied in the brief | AHOS brand asset (owner: AHOS project) |
| Sounds | generated at runtime | WebAudio oscillators/noise in `src/lib/audio/engine.ts` | part of this project (no audio files) |
| Icons | bundled code | `lucide-react@1.57.0` | ISC |
| Brief + reference images | `docs/brief/` | Supplied by the project owner for this build (provenance only; **not** used at runtime) | owner's material |

## 2. Direct dependencies

| Package | Version | License | Scope |
|---|---|---|---|
| class-variance-authority | 0.7.1 | Apache-2.0 | runtime |
| clsx | 2.1.1 | MIT | runtime |
| cmdk | 1.1.1 | MIT | runtime |
| d3-geo | 3.1.1 | ISC | runtime |
| echarts | 6.1.0 | Apache-2.0 | runtime |
| echarts-for-react | 3.0.6 | MIT | runtime |
| lucide-react | 1.57.0 | ISC | runtime |
| next | 16.2.6 | MIT | runtime |
| radix-ui | 1.8.1 | MIT | runtime |
| react | 19.2.6 | MIT | runtime |
| react-dom | 19.2.6 | MIT | runtime |
| tailwind-merge | 3.7.0 | MIT | runtime |
| three | 0.186.1 | MIT | runtime |
| three-globe | 2.45.6 | MIT | runtime |
| topojson-client | 3.1.0 | ISC | runtime |
| world-atlas | 2.0.2 | ISC | runtime |
| @fontsource-variable/inter | 5.3.0 | OFL-1.1 | dev |
| @tailwindcss/postcss | 4.1.17 | MIT | dev |
| @types/d3-geo | 3.1.1 | MIT | dev |
| @types/geojson | 7946.0.16 | MIT | dev |
| @types/node | 22.19.15 | MIT | dev |
| @types/react | 19.2.14 | MIT | dev |
| @types/react-dom | 19.2.3 | MIT | dev |
| @types/three | 0.186.0 | MIT | dev |
| @types/topojson-client | 3.1.5 | MIT | dev |
| eslint | 9.39.4 | MIT | dev |
| eslint-config-next | 16.2.6 | MIT | dev |
| postcss | 8.5.8 | MIT | dev |
| tailwindcss | 4.1.17 | MIT | dev |
| typescript | 5.9.3 | Apache-2.0 | dev |
| vazirmatn | 33.0.3 | OFL | dev |

`radix-ui` is the meta-package that re-exports the individual `@radix-ui/react-*` primitives (MIT).
`@fontsource-variable/inter` and `vazirmatn` are only used by `scripts/sync-assets.mjs` to copy the font files into `public/fonts`.

## 3. Full production dependency tree

Generated with `node scripts/licenses.mjs` (direct + transitive production packages, read from `node_modules`).

Notes on non-MIT/ISC entries:
* **Apache-2.0** — echarts, class-variance-authority, h3-js (three-globe), @swc/helpers, sharp, detect-libc, baseline-browser-mapping. Attribution/NOTICE obligations apply when redistributing.
* **BSD-3-Clause** — zrender (ECharts renderer), source-map-js.
* **0BSD** — tslib. **Unlicense** — robust-predicates (d3-geo).
* **CC-BY-4.0** — caniuse-lite (browser-support data used by Next.js tooling; not shipped to the browser).
* **LGPL-3.0-or-later** — `@img/sharp-libvips-*`: optional, dynamically linked native library used by Next.js server-side image optimization (`sharp`). It is not bundled into client code and this app does not use `next/image`; it can be removed by uninstalling the optional `sharp` dependency if desired.

| Package | Version | License |
|---|---|---|
| @emnapi/core | 1.10.0 | MIT |
| @emnapi/runtime | 1.11.3 | MIT |
| @emnapi/wasi-threads | 1.2.1 | MIT |
| @floating-ui/core | 1.8.0 | MIT |
| @floating-ui/dom | 1.8.0 | MIT |
| @floating-ui/react-dom | 2.1.9 | MIT |
| @floating-ui/utils | 0.2.12 | MIT |
| @img/colour | 1.1.0 | MIT |
| @img/sharp-libvips-linux-x64 | 1.2.4 | LGPL-3.0-or-later |
| @img/sharp-linux-x64 | 0.34.5 | Apache-2.0 |
| @napi-rs/wasm-runtime | 1.2.5 | MIT |
| @next/env | 16.2.6 | MIT |
| @next/swc-linux-x64-gnu | 16.2.6 | MIT |
| @radix-ui/number | 1.1.3 | MIT |
| @radix-ui/primitive | 1.2.0 | MIT |
| @radix-ui/react-accessible-icon | 1.2.0 | MIT |
| @radix-ui/react-accordion | 1.3.1 | MIT |
| @radix-ui/react-alert-dialog | 1.2.1 | MIT |
| @radix-ui/react-arrow | 1.1.17 | MIT |
| @radix-ui/react-aspect-ratio | 1.2.0 | MIT |
| @radix-ui/react-avatar | 1.3.1 | MIT |
| @radix-ui/react-checkbox | 1.4.1 | MIT |
| @radix-ui/react-collapsible | 1.2.1 | MIT |
| @radix-ui/react-collection | 1.2.0 | MIT |
| @radix-ui/react-compose-refs | 1.1.5 | MIT |
| @radix-ui/react-context | 1.3.0 | MIT |
| @radix-ui/react-context-menu | 2.4.1 | MIT |
| @radix-ui/react-dialog | 1.3.1 | MIT |
| @radix-ui/react-direction | 1.2.0 | MIT |
| @radix-ui/react-dismissable-layer | 1.2.1 | MIT |
| @radix-ui/react-dropdown-menu | 2.2.1 | MIT |
| @radix-ui/react-focus-guards | 1.2.0 | MIT |
| @radix-ui/react-focus-scope | 1.3.1 | MIT |
| @radix-ui/react-form | 0.3.0 | MIT |
| @radix-ui/react-hover-card | 1.2.1 | MIT |
| @radix-ui/react-id | 1.1.4 | MIT |
| @radix-ui/react-label | 2.1.17 | MIT |
| @radix-ui/react-menu | 2.2.1 | MIT |
| @radix-ui/react-menubar | 1.2.1 | MIT |
| @radix-ui/react-navigation-menu | 1.4.1 | MIT |
| @radix-ui/react-one-time-password-field | 0.2.1 | MIT |
| @radix-ui/react-password-toggle-field | 0.2.1 | MIT |
| @radix-ui/react-popover | 1.3.1 | MIT |
| @radix-ui/react-popper | 1.4.0 | MIT |
| @radix-ui/react-portal | 1.2.0 | MIT |
| @radix-ui/react-presence | 1.1.11 | MIT |
| @radix-ui/react-primitive | 2.2.0 | MIT |
| @radix-ui/react-progress | 1.2.1 | MIT |
| @radix-ui/react-radio-group | 1.5.1 | MIT |
| @radix-ui/react-roving-focus | 1.2.1 | MIT |
| @radix-ui/react-scroll-area | 1.4.0 | MIT |
| @radix-ui/react-select | 2.4.1 | MIT |
| @radix-ui/react-separator | 1.2.0 | MIT |
| @radix-ui/react-slider | 1.6.1 | MIT |
| @radix-ui/react-slot | 1.5.0 | MIT |
| @radix-ui/react-switch | 1.4.1 | MIT |
| @radix-ui/react-tabs | 1.2.1 | MIT |
| @radix-ui/react-toast | 1.3.1 | MIT |
| @radix-ui/react-toggle | 1.2.1 | MIT |
| @radix-ui/react-toggle-group | 1.2.1 | MIT |
| @radix-ui/react-toolbar | 1.2.1 | MIT |
| @radix-ui/react-tooltip | 1.4.1 | MIT |
| @radix-ui/react-use-callback-ref | 1.1.5 | MIT |
| @radix-ui/react-use-controllable-state | 1.3.0 | MIT |
| @radix-ui/react-use-effect-event | 0.0.5 | MIT |
| @radix-ui/react-use-escape-keydown | 1.1.6 | MIT |
| @radix-ui/react-use-is-hydrated | 0.1.3 | MIT |
| @radix-ui/react-use-layout-effect | 1.1.4 | MIT |
| @radix-ui/react-use-previous | 1.1.4 | MIT |
| @radix-ui/react-use-rect | 1.1.4 | MIT |
| @radix-ui/react-use-size | 1.1.5 | MIT |
| @radix-ui/react-visually-hidden | 1.2.13 | MIT |
| @radix-ui/rect | 1.1.3 | MIT |
| @swc/helpers | 0.5.15 | Apache-2.0 |
| @turf/boolean-point-in-polygon | 7.4.0 | MIT |
| @turf/helpers | 7.4.0 | MIT |
| @turf/invariant | 7.4.0 | MIT |
| @tweenjs/tween.js | 23.1.3 | MIT |
| @tybys/wasm-util | 0.10.4 | MIT |
| @types/geojson | 7946.0.16 | MIT |
| @types/react | 19.2.14 | MIT |
| @types/react-dom | 19.2.3 | MIT |
| accessor-fn | 1.5.3 | MIT |
| aria-hidden | 1.2.6 | MIT |
| baseline-browser-mapping | 2.11.29 | Apache-2.0 |
| caniuse-lite | 1.0.30001816 | CC-BY-4.0 |
| class-variance-authority | 0.7.1 | Apache-2.0 |
| client-only | 0.0.1 | MIT |
| clsx | 2.1.1 | MIT |
| cmdk | 1.1.1 | MIT |
| commander | 2.20.3 | MIT |
| csstype | 3.2.3 | MIT |
| d3-array | 3.2.4 | ISC |
| d3-color | 3.1.0 | ISC |
| d3-delaunay | 6.0.4 | ISC |
| d3-format | 3.1.2 | ISC |
| d3-geo | 3.1.1 | ISC |
| d3-geo-voronoi | 2.1.0 | ISC |
| d3-interpolate | 3.0.1 | ISC |
| d3-octree | 1.1.0 | MIT |
| d3-scale | 4.0.2 | ISC |
| d3-scale-chromatic | 3.1.0 | ISC |
| d3-time | 3.1.0 | ISC |
| d3-time-format | 4.1.0 | ISC |
| d3-tricontour | 1.1.0 | ISC |
| data-bind-mapper | 1.0.3 | MIT |
| delaunator | 5.1.0 | ISC |
| detect-libc | 2.1.2 | Apache-2.0 |
| detect-node-es | 1.1.0 | MIT |
| earcut | 3.2.4 | ISC |
| echarts | 6.1.0 | Apache-2.0 |
| echarts-for-react | 3.0.6 | MIT |
| fast-deep-equal | 3.1.3 | MIT |
| frame-ticker | 1.0.3 | MIT |
| get-nonce | 1.0.1 | MIT |
| h3-js | 4.5.0 | Apache-2.0 |
| index-array-by | 1.4.2 | MIT |
| internmap | 2.0.3 | ISC |
| kapsule | 1.16.3 | MIT |
| lodash-es | 4.18.1 | MIT |
| lucide-react | 1.57.0 | ISC |
| nanoid | 3.3.20 | MIT |
| next | 16.2.6 | MIT |
| picocolors | 1.1.1 | ISC |
| point-in-polygon-hao | 1.2.4 | MIT |
| postcss | 8.4.31 | MIT |
| radix-ui | 1.8.1 | MIT |
| react | 19.2.6 | MIT |
| react-dom | 19.2.6 | MIT |
| react-remove-scroll | 2.7.2 | MIT |
| react-remove-scroll-bar | 2.3.8 | MIT |
| react-style-singleton | 2.2.3 | MIT |
| robust-predicates | 3.0.3 | Unlicense |
| scheduler | 0.27.0 | MIT |
| semver | 7.8.5 | ISC |
| sharp | 0.34.5 | Apache-2.0 |
| simplesignal | 2.1.7 | MIT |
| size-sensor | 1.0.3 | ISC |
| source-map-js | 1.2.2 | BSD-3-Clause |
| styled-jsx | 5.1.6 | MIT |
| tailwind-merge | 3.7.0 | MIT |
| three | 0.186.1 | MIT |
| three-conic-polygon-geometry | 2.1.3 | MIT |
| three-geojson-geometry | 2.1.1 | MIT |
| three-globe | 2.45.6 | MIT |
| three-slippy-map-globe | 1.0.6 | MIT |
| tinycolor2 | 1.6.0 | MIT |
| topojson-client | 3.1.0 | ISC |
| tslib | 2.8.1 | 0BSD |
| tslib | 2.3.0 | 0BSD |
| use-callback-ref | 1.3.3 | MIT |
| use-sidecar | 1.1.3 | MIT |
| world-atlas | 2.0.2 | ISC |
| zrender | 6.1.0 | BSD-3-Clause |

## 4. Development-only dependencies

ESLint, TypeScript, Tailwind CSS, PostCSS and `@types/*` packages (see §2) are build-time tools and are not shipped to users.
Their transitive trees are permissively licensed (MIT / ISC / Apache-2.0 / BSD); run `npm ls --all` for the complete list.
