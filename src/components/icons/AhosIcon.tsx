'use client';

/**
 * <AhosIcon /> — AHOS brand & icon pack, React binding.
 *
 *   <AhosIcon name="nav/command-center" variant="gold" size={32} title="مرکز فرمان" />
 *   <AhosIcon name="status/live" variant="color" size={16} />
 *
 * * no runtime fetch: every glyph is inlined at build time (see components.tsx)
 * * tree-shakeable: import the named component you need from './components'
 * * RTL-safe: the component is presentation-only, so it composes with the app's
 *   dir="rtl" layout without extra handling
 */

import * as React from 'react';
import type { SVGProps } from 'react';

import { AhosGlyph } from './icons';
import type { AhosIconName, AhosIconVariant } from './icons.d';

export type { AhosIconName, AhosIconVariant };

export interface AhosIconProps extends Omit<SVGProps<SVGSVGElement>, 'name' | 'children'> {
  /** Icon id, e.g. `'nav/oil'`, `'status/live'`, `'agents/kian'`. */
  name: AhosIconName;
  /** `outline` (currentColor), `gold` (brand gradient + halo) or `color` (semantic status). */
  variant?: AhosIconVariant;
  /** Number = px. Any CSS length string is accepted too. Defaults to the glyph grid. */
  size?: number | string;
  className?: string;
  /** Accessible name. Without it the glyph is hidden from assistive tech. */
  title?: string;
}

/**
 * Renders any icon from the pack by name. The variant falls back to the icon's first
 * available variant (`outline`), and the accessible name follows `title`.
 */
export const AhosIcon = ({ name, variant = 'outline', size, className, title, ...rest }: AhosIconProps) => (
  <AhosGlyph name={name} variant={variant} size={size} className={className} title={title} {...rest} />
);

export default AhosIcon;
