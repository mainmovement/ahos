/**
 * AHOS · Trade Venue — query parsing.
 * Query strings are read-only switches for the state gallery and the DEMO
 * force; nothing here can change execution mode or enable anything.
 */

import { MISSING_GLYPH } from "./truth";
import type { QualityTier, VenueQuery, ViewState, World } from "./model";
import { VIEW_STATES, WORLDS } from "./model";

const TIERS: readonly QualityTier[] = ["T0", "T1", "T2"];

function first(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

function isTrue(value: string | null): boolean {
  if (value === null) return false;
  const normalised = value.toLowerCase();
  return normalised === "1" || normalised === "true" || normalised === "yes";
}

export function readVenueSearchParams(
  params: Record<string, string | string[] | undefined>,
): VenueQuery {
  const rawState = first(params.state);
  const state: ViewState =
    rawState && (VIEW_STATES as readonly string[]).includes(rawState.toUpperCase())
      ? (rawState.toUpperCase() as ViewState)
      : "DEFAULT";

  const rawTier = first(params.tier);
  const tier: QualityTier =
    rawTier && (TIERS as readonly string[]).includes(rawTier.toUpperCase())
      ? (rawTier.toUpperCase() as QualityTier)
      : "T2";

  const rawWorld = first(params.world);
  const world: World =
    rawWorld && (WORLDS as readonly string[]).includes(rawWorld.toUpperCase())
      ? (rawWorld.toUpperCase() as World)
      : "REAL_PAPER";

  return {
    forceDemo: isTrue(first(params.demo)),
    state,
    tier,
    world,
    forceViolation: isTrue(first(params.violation)),
    gallery: isTrue(first(params.all)),
    resolvedFrom: first(params.state) ?? MISSING_GLYPH,
  };
}

/** Tile-side "mode" copy: the run mode never claims more than PAPER_ONLY. */
export function modeBadge(query: VenueQuery): { fa: string; en: string } {
  return query.world === "SIMULATION"
    ? { fa: "کاغذی · شبیه‌سازی", en: "PAPER_ONLY · SIMULATION" }
    : { fa: "کاغذی", en: "PAPER_ONLY" };
}
