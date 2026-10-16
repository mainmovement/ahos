"use client";
import dynamic from "next/dynamic";
import type { ComponentType } from "react";
import { StatusChip } from "../cards/DataCard";
import { formatInteger, recordFreshness } from "../../lib/format";
import { tr } from "../../lib/i18n";
import type { PulseOrbProps } from "../../types/orb";

function OrbPlaceholder({ health, departments, signals, gate, calm, language = "fa" }: PulseOrbProps) {
  const attention = departments.filter((d) => d.health.value !== "OK").length;
  const gateText = gate.engaged.value
    ? tr(language, "pages.overview.cards.killSwitch.engaged")
    : tr(language, "pages.overview.cards.killSwitch.armed");
  const deptText =
    attention === 0
      ? tr(language, "pages.overview.cards.departments.allHealthy")
      : tr(language, "pages.overview.cards.departments.needsAttention").replace(
          "{count}",
          formatInteger(attention, { locale: language }),
        );
  return (
    <div className={`dc-orb-placeholder ${calm ? "is-calm" : ""}`} data-orb="placeholder">
      <div className="dc-orb-circle" aria-hidden="true">
        <span className="dc-orb-core" />
      </div>
      <div className="dc-orb-text">
        <strong>{tr(language, "pages.overview.cards.health.title")}</strong>
        <span>{deptText}</span>
        <span>{gateText}</span>
        <small>
          {formatInteger(signals.length, { locale: language })} {tr(language, "nav.signals")}
        </small>
        <StatusChip status={recordFreshness(health)} language={language} />
      </div>
    </div>
  );
}

// "@arena-orb" -> src/components/orb/PulseOrb.tsx when it exists, otherwise a null stub (see next.config.ts).
const LazyOrb = dynamic<PulseOrbProps>(
  () =>
    import("@arena-orb").then((m) => ({
      default: (m.default ?? OrbPlaceholder) as ComponentType<PulseOrbProps>,
    })),
  { ssr: false, loading: () => null },
);

/** Centered hero slot for the future PulseOrb. Always renders a calm static placeholder first. */
export function OrbSlot(props: PulseOrbProps) {
  return (
    <section className="dc-orb-slot" aria-label={tr(props.language ?? "fa", "pages.overview.cards.health.title")}>
      <LazyOrb {...props} />
    </section>
  );
}