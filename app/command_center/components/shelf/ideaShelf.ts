/**
 * M-D5.5 — the idea shelf: which installed ideas is this machine still waiting on?
 *
 * The shelf itself is Aji's M59.S deliverable. Its registry is
 * `config/idea_shelf.json`, whose entry shape is
 *
 *     { id, title, tier, core, flag, est_ram_mb, priority, depends_on }
 *
 * and M57.T's vetting gives every idea a *hardware tier tag* (T8/T16/T32/GPU).
 * This module answers the one question the dashboard has about that file: which
 * ideas require a stronger machine than the one the probe measured — the ones the
 * panel lists under «منتظر ارتقا» (awaiting upgrade).
 *
 * The split is the same one `quality.ts` uses: **file reading is impure, the
 * selection is pure**. `parseShelf` takes raw text and returns either parsed
 * ideas or an explicit UNAVAILABLE with a reason; `awaitingUpgrade` is a pure
 * function of that list and the measured hardware tier, so the whole rule can be
 * asserted on a machine with no shelf file and no GPU — which is the only way the
 * rule can be proven rather than assumed.
 *
 * Nothing here hard-codes an idea name. The panel may only ever render names that
 * came out of the file; when the file is absent the list is UNKNOWN, not a set of
 * plausible-sounding suggestions, because a fabricated idea list is exactly the
 * failure mode `UNKNOWN > fabricated` exists to prevent. The ideas are also not
 * evidence of anything but themselves — an idea on the shelf is a vetted *tool*,
 * never a token verdict.
 */

import { HARDWARE_TIERS, RAM_FLOOR_GB, type HardwareTier } from "@/components/stage/quality";

/** The entry shape M59.S defines, minus the fields the panel does not consume. */
export interface ShelfIdea {
  id: string;
  title: string;
  /** The hardware tier M57.T's vetting tagged this idea as needing. */
  tier: HardwareTier | null;
  /** Whether M59.S considers this part of the paper core (never shed). */
  core?: boolean;
  /** Estimated resident RAM in MiB, for the panel's RAM line. */
  est_ram_mb?: number;
  priority?: number;
}

export type ShelfParse =
  | { status: "OK"; ideas: ShelfIdea[] }
  | { status: "UNAVAILABLE"; reason: string };

/**
 * Read the shelf from raw file text.
 *
 * Absent and unreadable are both UNAVAILABLE, and so is a file that is not valid
 * JSON or is not an object — a shelf that cannot be parsed is not a shelf with
 * zero ideas, it is a shelf whose contents are unknown. Reporting an empty list
 * instead would let a corrupted registry present itself as "everything fits".
 */
export function parseShelf(raw: string | null | undefined): ShelfParse {
  if (raw === null || raw === undefined || raw === "") {
    return { status: "UNAVAILABLE", reason: "missing" };
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return { status: "UNAVAILABLE", reason: `unparseable: ${(e as Error).message}` };
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { status: "UNAVAILABLE", reason: "not an object" };
  }
  const ideas = (parsed as { ideas?: unknown }).ideas;
  if (!Array.isArray(ideas)) {
    // A registry with no `ideas` array is a shape M59.S does not emit.
    return { status: "UNAVAILABLE", reason: "no ideas array" };
  }
  const known = new Set<string>();
  const out: ShelfIdea[] = [];
  for (const entry of ideas) {
    if (entry === null || typeof entry !== "object") continue;
    const e = entry as Record<string, unknown>;
    const id = typeof e.id === "string" ? e.id : null;
    const title = typeof e.title === "string" ? e.title : null;
    if (id === null || title === null) continue;
    if (known.has(id)) continue; // M59.S registry ids are unique; first wins.
    known.add(id);
    const tierRaw = typeof e.tier === "string" ? e.tier : null;
    out.push({
      id,
      title,
      // An unrecognised tier tag is not a low requirement — it is an unknown one,
      // kept as `null` so the panel shows UNKNOWN rather than "runs on this".
      tier: tierRaw !== null && (HARDWARE_TIERS as readonly string[]).includes(tierRaw)
        ? (tierRaw as HardwareTier)
        : null,
      // Absent optional fields stay absent rather than becoming explicit
      // `false`/`NaN`, so a parsed entry round-trips to the shape it was read from.
      core: e.core === true ? true : undefined,
      est_ram_mb: typeof e.est_ram_mb === "number" && Number.isFinite(e.est_ram_mb)
        ? e.est_ram_mb
        : undefined,
      priority: typeof e.priority === "number" && Number.isFinite(e.priority)
        ? e.priority
        : undefined,
    });
  }
  return { status: "OK", ideas: out };
}

/** Index of a hardware tier on the ladder, T8 the floor and GPU the ceiling. */
export function hardwareOrdinal(t: HardwareTier | null): number | null {
  if (t === null) return null;
  const i = HARDWARE_TIERS.indexOf(t);
  return i < 0 ? null : i;
}

/**
 * The ideas this machine cannot run yet — a strict tier comparison, highest
 * requirement first so the panel reads as a shopping list of upgrades.
 *
 * An idea with an unknown tier tag is *excluded*, not included: listing it as
 * awaiting would claim the machine cannot run something the registry never said
 * it needed, and listing it as available would claim the opposite. Either would
 * be a fabrication from a missing field.
 */
export function awaitingUpgrade(ideas: ShelfIdea[], machine: HardwareTier | null): ShelfIdea[] {
  const mine = hardwareOrdinal(machine);
  if (mine === null) {
    // The machine's own tier is unknown, so no idea can be classified as
    // runnable or not. Nothing is listed, and the panel says why.
    return [];
  }
  return ideas
    .filter((idea) => {
      const need = hardwareOrdinal(idea.tier);
      return need !== null && need > mine;
    })
    .sort((a, b) => {
      const need = (i: ShelfIdea) => hardwareOrdinal(i.tier) ?? -1;
      const byTier = need(b) - need(a);
      if (byTier !== 0) return byTier;
      // Within the same requirement, higher M59.S priority first.
      return (b.priority ?? 0) - (a.priority ?? 0);
    });
}

/**
 * The RAM-guard line the panel shows: where the measured upper bound sits against
 * the 8 GB floor. `null` is UNKNOWN — `navigator.deviceMemory` is coarse and
 * often withheld, and an unreadable value is not "under the floor".
 */
export function ramGuardState(ramGb: number | null): {
  state: "UNDER_FLOOR" | "AT_FLOOR" | "ABOVE_FLOOR" | "UNKNOWN";
  /** Persian, for the panel. */
  fa: string;
} {
  if (ramGb === null) {
    return {
      state: "UNKNOWN",
      fa: "حافظه از سوی مرورگر نامعلوم است — طبقه‌بندی نمی‌شود",
    };
  }
  if (ramGb < RAM_FLOOR_GB) {
    return {
      state: "UNDER_FLOOR",
      fa: `${ramGb} گیگابایت — زیر کفِ ۸ گیگابایت: تنها T1 مجاز است`,
    };
  }
  if (ramGb === RAM_FLOOR_GB) {
    return {
      state: "AT_FLOOR",
      fa: "دقیقاً روی کفِ ۸ گیگابایت — همین ماشینِ مالک",
    };
  }
  return {
    state: "ABOVE_FLOOR",
    fa: `${ramGb} گیگابایت — بالای کفِ ۸ گیگابایت`,
  };
}
