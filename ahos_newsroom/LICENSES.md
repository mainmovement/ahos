# LICENSES.md — third-party notices

## Fonts

| Font | Version | Licence | Files |
| --- | --- | --- | --- |
| **Vazirmatn** | 33.003 (via `@fontsource/vazirmatn` 5.x) | SIL Open Font License 1.1 | `public/fonts/vazirmatn-*.woff2` |
| **Inter** | 4.x (via `@fontsource/inter` 5.x) | SIL Open Font License 1.1 | `public/fonts/inter-*.woff2` |

Full licence texts are shipped next to the binaries:
`public/fonts/LICENSE-Vazirmatn.txt` and `public/fonts/LICENSE-Inter.txt`.

Both fonts are bundled locally as `woff2` — **no font is fetched at runtime**, and the app renders
identically with the network unplugged.

## Runtime dependencies

| Package | Version | Licence |
| --- | --- | --- |
| `next` | 16.4.2 | MIT — © Vercel, Inc. |
| `react` | 19.3.1 | MIT — © Meta Platforms, Inc. |
| `react-dom` | 19.3.1 | MIT — © Meta Platforms, Inc. |

## Development dependencies

| Package | Version | Licence |
| --- | --- | --- |
| `typescript` | 5.9.3 | Apache-2.0 — © Microsoft Corporation |
| `tailwindcss` | 4.3.3 | MIT — © Tailwind Labs, Inc. |
| `@tailwindcss/postcss` | 4.3.3 | MIT — © Tailwind Labs, Inc. |
| `eslint` | 9.x | MIT — © OpenJS Foundation |
| `eslint-config-next` | 16.4.2 | MIT — © Vercel, Inc. |
| `vitest` | 5.0.5 | MIT — © Vitest contributors |
| `@vitejs/plugin-react` | 6.1.2 | MIT — © Vite contributors |
| `jsdom` | 30.1.3 | MIT — © jsdom contributors |
| `@testing-library/react` | 16.3.3 | MIT — © Testing Library contributors |
| `@testing-library/dom` | 10.4.2 | MIT — © Testing Library contributors |
| `@testing-library/jest-dom` | 7.0.1 | MIT — © Testing Library contributors |
| `@types/node`, `@types/react`, `@types/react-dom` | — | MIT — © Microsoft Corporation / DefinitelyTyped |

## Application code

The Newsroom page in this folder is part of the AHOS project and follows the licence of the
`mainmovement/ahos` repository. It contains **no** copied third-party source: every component,
fixture and helper here was written for this screen.

## Screenshots

`screenshots/*.png` (1600×900) are renders of this application captured with a headless Chromium
(Chromium is licensed under the BSD-3-Clause / Chromium terms). They are provided as evidence, not
as artwork, and may be reproduced freely.

## Licence compliance notes

* SIL OFL 1.1 requires the licence text to travel with the font files — it does (see above), and
  the fonts are **not** renamed or subset-modified: the `@fontsource` woff2 files are shipped
  byte-for-byte.
* No GPL/AGPL/LGPL code is linked into this bundle.
