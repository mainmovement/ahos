/**
 * AHOS — status chips (`lib/status.ts`)
 * =====================================
 *
 * The five states a value can be in on this dashboard, and how each one is
 * rendered. Text lives in `i18n/fa.json` / `i18n/en.json` under `status.*`;
 * this module owns the mapping, the tone and the Tailwind classes.
 *
 *   LIVE     زنده     observed now, inside the staleness budget
 *   STALE    کهنه     really observed, but out of budget — shown, never trusted silently
 *   UNKNOWN  نامعلوم  not observed — rendered as «—», never as a number
 *   DEMO     نمایشی   synthetic sample data — never a claim about a real market
 *   PAPER    کاغذی    the book itself: simulation money, real trading DISABLED
 *
 * Theme: black + glass + gold. `--color-gold` is the brand accent; the classes
 * below carry a hex fallback so the chips survive a missing theme token.
 *
 * `scripts/validate.mjs` asserts that every `ChipKind` has a non-empty `label`
 * and `hint` in both locales, that the Persian label is short enough for a chip,
 * and that the hint is a single line.
 */

import type { Freshness } from "../types/contract.ts";
import { CHIP_KINDS } from "../types/contract.ts";
import { recordFreshness, worstFreshness } from "./format.ts";
import type { LocaleTag } from "./format.ts";

/** The five chips. `PAPER` is a mode chip, not a freshness. */
export type ChipKind = (typeof CHIP_KINDS)[number];

export const CHIP_KIND_LIST: readonly ChipKind[] = CHIP_KINDS;

/** Chip kinds that can appear in an `Observed<T>.freshness` field. */
export const FRESHNESS_CHIPS: readonly Freshness[] = ["LIVE", "STALE", "UNKNOWN", "DEMO"];

export type ChipTone = "emerald" | "amber" | "zinc" | "gold";

export interface ChipMeta {
  kind: ChipKind;
  /** `status.LIVE.label` — short Persian/English label. */
  labelKey: string;
  /** `status.LIVE.hint` — one-line explanation, used as the tooltip. */
  hintKey: string;
  tone: ChipTone;
  /** Classes for the pill itself. */
  chipClass: string;
  /** Classes for the leading dot. */
  dotClass: string;
  /**
   * Sort/filter priority for legends and "most urgent first" lists: lower =
   * shown first. This is a *display* ordering only — the record-level rollup
   * precedence lives in `FRESHNESS_ROLLUP_ORDER` in `lib/format.ts`.
   */
  priority: number;
  /** Chips that must always be accompanied by the paper-only notice. */
  impliesMoney: boolean;
  /** Accessible label key (`aria-label`), so a screen reader hears the state. */
  ariaKey: string;
}

const PILL =
  "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium leading-4 backdrop-blur-sm whitespace-nowrap";
const DOT = "size-1.5 shrink-0 rounded-full";
const GOLD_TEXT = "text-[var(--color-gold,#E8C37A)]";
const GOLD_BORDER = "border-[var(--color-gold,#E8C37A)]/40";
const GOLD_BG = "bg-[var(--color-gold,#E8C37A)]/10";

export const CHIP_META: Record<ChipKind, ChipMeta> = {
  LIVE: {
    kind: "LIVE",
    labelKey: "status.LIVE.label",
    hintKey: "status.LIVE.hint",
    tone: "emerald",
    chipClass: `${PILL} border-emerald-400/30 bg-emerald-400/10 text-emerald-200`,
    dotClass: `${DOT} bg-emerald-300 shadow-[0_0_6px_theme(colors.emerald.400)]`,
    priority: 3,
    impliesMoney: false,
    ariaKey: "status.LIVE.aria",
  },
  STALE: {
    kind: "STALE",
    labelKey: "status.STALE.label",
    hintKey: "status.STALE.hint",
    tone: "amber",
    chipClass: `${PILL} border-amber-400/30 bg-amber-400/10 text-amber-200`,
    dotClass: `${DOT} bg-amber-300`,
    priority: 2,
    impliesMoney: false,
    ariaKey: "status.STALE.aria",
  },
  UNKNOWN: {
    kind: "UNKNOWN",
    labelKey: "status.UNKNOWN.label",
    hintKey: "status.UNKNOWN.hint",
    tone: "zinc",
    chipClass: `${PILL} border-zinc-500/30 bg-zinc-500/10 text-zinc-300`,
    dotClass: `${DOT} bg-zinc-400`,
    priority: 0,
    impliesMoney: false,
    ariaKey: "status.UNKNOWN.aria",
  },
  DEMO: {
    kind: "DEMO",
    labelKey: "status.DEMO.label",
    hintKey: "status.DEMO.hint",
    tone: "gold",
    chipClass: `${PILL} ${GOLD_BORDER} ${GOLD_BG} ${GOLD_TEXT}`,
    dotClass: `${DOT} bg-[var(--color-gold,#E8C37A)]`,
    priority: 1,
    impliesMoney: true,
    ariaKey: "status.DEMO.aria",
  },
  PAPER: {
    kind: "PAPER",
    labelKey: "status.PAPER.label",
    hintKey: "status.PAPER.hint",
    tone: "gold",
    chipClass: `${PILL} ${GOLD_BORDER} ${GOLD_BG} ${GOLD_TEXT}`,
    dotClass: `${DOT} bg-[var(--color-gold,#E8C37A)]`,
    priority: 1,
    impliesMoney: true,
    ariaKey: "status.PAPER.aria",
  },
};

/** Ordered for legends: most urgent first. */
export const CHIP_ORDER: readonly ChipKind[] = ["UNKNOWN", "STALE", "DEMO", "PAPER", "LIVE"];

export function chipMeta(kind: ChipKind): ChipMeta {
  return CHIP_META[kind];
}

/** `Observed.freshness` → chip kind (identity for the four freshness values). */
export function chipForFreshness(freshness: Freshness): ChipKind {
  return freshness;
}

/**
 * The chip a whole record should show: the worst freshness among its fields.
 *
 * Deliberately *not* re-implemented — it delegates to `worstFreshness()` in
 * `lib/format.ts` so that the record-level rollup, the generator and the
 * validator can never disagree about precedence (`DEMO` dominates, then
 * `UNKNOWN < STALE < LIVE`, empty list = `UNKNOWN`).
 */
export function chipForRecord(freshnesses: readonly Freshness[]): ChipKind {
  return worstFreshness(freshnesses);
}

/**
 * Same rollup, applied straight to a record object: convenience for panels that
 * have the entity in hand and do not want to collect field freshness by hand.
 */
export function chipForEntity(record: unknown): ChipKind {
  return recordFreshness(record);
}

/** Class string for the paper-only banner that has to sit above any money panel. */
export const PAPER_BANNER_CLASS =
  "flex items-start gap-2 rounded-lg border border-[var(--color-gold,#E8C37A)]/25 bg-[var(--color-gold,#E8C37A)]/[0.06] px-3 py-2 text-xs text-zinc-200 backdrop-blur-md";

/** Class string for the black-glass card every panel uses. */
export const GLASS_CARD_CLASS =
  "rounded-xl border border-white/10 bg-black/40 p-4 shadow-[0_1px_0_0_rgba(255,255,255,0.06)_inset] backdrop-blur-xl";

/** Localised chip label/hint lookup signature the UI passes in. */
export type ChipTextResolver = (key: string, locale: LocaleTag) => string;

/** Resolved, render-ready chip text. */
export interface ChipTexts {
  kind: ChipKind;
  label: string;
  hint: string;
  aria: string;
}

/** Pulls label/hint/aria for a chip out of the dictionary. */
export function chipTexts(kind: ChipKind, resolve: ChipTextResolver, locale: LocaleTag): ChipTexts {
  const meta = CHIP_META[kind];
  return {
    kind,
    label: resolve(meta.labelKey, locale),
    hint: resolve(meta.hintKey, locale),
    aria: resolve(meta.ariaKey, locale),
  };
}
