# Stage 1 dependency and asset notices

This inventory covers the Stage 1 interface and the existing root project's direct dependencies. Package versions are pinned in `package-lock.json`; upstream license text is included in installed package distributions. This document does not relicense the original AHOS repository.

| Dependency / asset | License / notice |
|---|---|
| Next.js, eslint-config-next | MIT (Vercel) |
| React, React DOM | MIT (Meta and contributors) |
| TypeScript | Apache-2.0 (Microsoft) |
| Tailwind CSS, @tailwindcss/postcss | MIT |
| PostCSS | MIT |
| lucide-react icons | ISC; Lucide includes Feather-derived work under MIT; see package LICENSE |
| ESLint | MIT |
| @types/node, @types/react, @types/react-dom, @types/pg | MIT (DefinitelyTyped contributors) |
| dotenv | BSD-2-Clause |
| drizzle-orm, drizzle-kit | Apache-2.0 |
| pg (node-postgres) | MIT |
| Vazirmatn font | SIL Open Font License 1.1, Saber Rastikerdar and contributors; copied text: `public/fonts/LICENSE-Vazirmatn.txt` |
| Inter font | SIL Open Font License 1.1, Rasmus Andersson and contributors; copied text: `public/fonts/LICENSE-Inter.txt` |
| @fontsource/vazirmatn, @fontsource/inter distribution | Font files use OFL-1.1; see the bundled licenses above |
| Star symbol, orbital illustration, UI styles | Original project assets created for this implementation; no stock photography or third-party reference images embedded |
| Confirmation audio | Synthesized sine tone with WebAudio; no audio recordings or copyrighted music |

All fonts needed by this stage are local WOFF2 files. No Google Fonts requests, remote imagery, paid services, or other external runtime assets are used by the new shell. The user's reference images served as visual direction only.
