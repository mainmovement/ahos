/**
 * AHOS icon pack — type declarations.
 *
 * Included by `react/index.ts`; also safe to reference from an app-level
 * `d.ts` if you import the raw .svg files instead of the React components.
 */

import type { FC, SVGProps } from 'react';

/** A .svg import is a React component (works with @svgr/webpack, SVGR + Turbopack, Vite's svgr plugin). */
declare module '*.svg' {
  const ReactComponent: FC<SVGProps<SVGSVGElement> & { title?: string }>;
  export default ReactComponent;
}

export type AhosIconVariant = 'outline' | 'gold' | 'color';

/** Every icon id shipped in the pack (52 glyphs). */
export type AhosIconName =
  | 'nav/command-center'
  | 'nav/digital-world'
  | 'nav/earth'
  | 'nav/market-prices'
  | 'nav/opportunities'
  | 'nav/oil'
  | 'nav/gold'
  | 'nav/us-equities'
  | 'nav/eu-equities'
  | 'nav/asia-equities'
  | 'nav/crypto-market'
  | 'nav/token-intelligence'
  | 'nav/newsroom'
  | 'nav/security'
  | 'nav/tech-workshop'
  | 'nav/university'
  | 'nav/exams'
  | 'nav/research'
  | 'nav/kian-chat'
  | 'nav/agents'
  | 'nav/paper-trading'
  | 'nav/portfolio'
  | 'nav/memory-learning'
  | 'nav/errors-recovery'
  | 'nav/reports-evidence'
  | 'nav/system-runtime'
  | 'nav/governance-audit'
  | 'nav/settings'
  | 'status/live'
  | 'status/stale'
  | 'status/unknown'
  | 'status/unavailable'
  | 'status/demo'
  | 'status/verified'
  | 'status/warning'
  | 'status/critical'
  | 'status/blocked'
  | 'status/running'
  | 'status/failed'
  | 'status/planned'
  | 'agents/oil'
  | 'agents/gold'
  | 'agents/us'
  | 'agents/eu'
  | 'agents/asia'
  | 'agents/token'
  | 'agents/crypto-market'
  | 'agents/newsroom'
  | 'agents/security'
  | 'agents/university'
  | 'agents/research'
  | 'agents/kian';

/** Categories shipped in the pack. */
export type AhosIconCategory = 'nav' | 'status' | 'agents';

/** One row of ICON_MANIFEST.json. */
export interface AhosIconManifestEntry {
  /** Icon id, e.g. `'nav/oil'`. */
  name: string;
  /** Path relative to `ahos_assets/02_icons/`. */
  file: string;
  category: 'navigation' | 'status' | 'agents' | 'logo' | 'logo-raster' | 'react' | 'preview' | 'sprite' | 'docs';
  variant: string;
  /** Intrinsic size: number in px, or a "WxH" string for lockups and the ico. */
  size: number | string;
  license: string;
  bytes?: number;
  title?: string;
  titleFa?: string;
  color?: string;
  shape?: string;
}

export interface AhosIconManifest {
  pack: string;
  packNumber: string;
  version: string;
  generated: string;
  license: string;
  grid: { icons: string; emblems: string; stroke: number; strokeEmblem: number; strokeCaps: string; strokeJoins: string };
  tokens: Record<string, string>;
  gold: string[];
  counts: { icons: number; files: number; byCategory: Record<string, number> };
  totalBytes: number;
  assets: AhosIconManifestEntry[];
}
