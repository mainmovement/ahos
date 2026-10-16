# LICENSES

## Application code

`ahos_white_hats` application source (src/, tests/, configs, docs):
MIT License — Copyright (c) 2026 AHOS contributors.

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Bundled fonts (local, no network at runtime)

| Font       | Files                                  | License                                    | Copyright |
| ---------- | -------------------------------------- | ------------------------------------------ | --------- |
| Vazirmatn  | `@fontsource/vazirmatn` (woff2, 400–700) | SIL Open Font License 1.1                  | © The Vazirmatn Project Authors (Saber Rastikerdar and contributors) |
| Inter      | `@fontsource/inter` (woff2, 400–700)     | SIL Open Font License 1.1                  | © The Inter Project Authors (Rasmus Andersson) |

The SIL OFL 1.1 permits bundling and redistribution with the fonts' license
notice; full texts ship inside the fontsource packages
(`node_modules/@fontsource/{vazirmatn,inter}/LICENSE`).

## Runtime / build dependencies (all MIT unless noted)

| Package                | Version (pinned) | License     |
| ---------------------- | ---------------- | ----------- |
| next                   | 16.4.2           | MIT         |
| react / react-dom      | 19.3.1           | MIT         |
| tailwindcss / @tailwindcss/postcss | 4.3.3 | MIT         |
| @fontsource/inter      | 5.3.0            | MIT (code) + OFL 1.1 (font data) |
| @fontsource/vazirmatn  | 5.3.0            | MIT (code) + OFL 1.1 (font data) |
| typescript             | 5.9.3            | Apache-2.0  |
| vitest / vite          | 5.0.5 / 8.3.4    | MIT         |
| @vitejs/plugin-react   | 6.1.2            | MIT         |
| jsdom                  | 30.1.3           | MIT         |
| @testing-library/react / dom / jest-dom | 16.3.3 / 10.4.2 / 7.0.1 | MIT |
| eslint / @eslint/js    | 9.39.5           | MIT         |
| typescript-eslint      | 8.71.2           | BSD-2-Clause|
| eslint-plugin-react-hooks | 7.1.1         | MIT         |
| @types/react / react-dom / node | 19.3.0 / 19.3.0 / 22.20.5 | MIT |

Full license texts are distributed inside each package under `node_modules/`
(restorable with `npm install` from `package-lock.json`).
