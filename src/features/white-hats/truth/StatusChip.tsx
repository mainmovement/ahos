import { tr } from "@/src/lib/i18n";
import { STATUS_TONE, type ChipStatus, type Tone } from "./status";

const FA_LABEL: Record<ChipStatus, string> = {
  LIVE: tr("fa", "whiteHats.ui.StatusChip_1"),
  STALE: tr("fa", "whiteHats.ui.StatusChip_2"),
  UNKNOWN: tr("fa", "whiteHats.ui.StatusChip_3"),
  DEMO: tr("fa", "whiteHats.ui.StatusChip_4"),
  CONFLICT: tr("fa", "whiteHats.ui.StatusChip_5"),
  REJECTED: tr("fa", "whiteHats.ui.StatusChip_6"),

  LOADING: tr("fa", "whiteHats.ui.StatusChip_7"),
  EMPTY: tr("fa", "whiteHats.ui.StatusChip_8"),
  ERROR: tr("fa", "whiteHats.ui.StatusChip_9"),
  UNAVAILABLE: tr("fa", "whiteHats.ui.StatusChip_10"),
  PARTIAL: tr("fa", "whiteHats.ui.FindingsLog_4"),
  SIMULATED: tr("fa", "whiteHats.ui.StatusChip_11"),

  CLEAN: tr("fa", "whiteHats.ui.StatusChip_12"),
  FINDING: tr("fa", "whiteHats.ui.StatusChip_13"),
  BLOCKED: tr("fa", "whiteHats.ui.StatusChip_14"),

  ARMED: tr("fa", "whiteHats.ui.StatusChip_15"),
  TRIPPED: tr("fa", "whiteHats.ui.StatusChip_16"),

  OPEN: tr("fa", "whiteHats.ui.FindingsLog_15"),
  RESOLVED: tr("fa", "whiteHats.ui.FindingsLog_16"),

  INFO: tr("fa", "whiteHats.ui.FindingsLog_5"),
  MINOR: tr("fa", "whiteHats.ui.FindingsLog_4"),
  MAJOR: tr("fa", "whiteHats.ui.FindingsLog_3"),
  CRITICAL: tr("fa", "whiteHats.ui.FindingsLog_2"),

  FAIL: tr("fa", "whiteHats.ui.StatusChip_17"),
  PASS: tr("fa", "whiteHats.ui.StatusChip_18"),
};

/** A demo-backed surface can never present LIVE (green). */
export function demoSafeStatus(status: ChipStatus, demo: boolean): ChipStatus {
  return demo && status === "LIVE" ? "DEMO" : status;
}

export function statusFaLabel(status: ChipStatus): string {
  return FA_LABEL[status];
}

export interface StatusChipProps {
  status: ChipStatus;
  size?: "sm" | "lg";
  /** Show the diagonal DEMO striping on the chip itself. */
  striped?: boolean;
  /** Data is mock/demo-backed: a LIVE status is shown as DEMO, never green. */
  demo?: boolean;
  title?: string;
  className?: string;
}

/**
 * The single truth chip used everywhere. Renders `data-status` and `data-tone`
 * so tests (and future e2e) can assert truth rules mechanically:
 * UNKNOWN always carries data-tone="grey" — never "live".
 */
export function StatusChip({
  status: rawStatus,
  size = "sm",
  striped = false,
  demo = false,
  title,
  className = "",
}: StatusChipProps) {
  const status: ChipStatus = demoSafeStatus(rawStatus, demo);
  const tone: Tone = STATUS_TONE[status];
  const isDemo = status === "DEMO" || striped;
  const classes = [
    "wh-chip",
    size === "lg" ? "wh-chip-lg" : "",
    `wh-tone-${tone}`,
    isDemo ? "wh-demo-stripes" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes} data-status={status} data-tone={tone} title={title}>
      <span className="wh-dot" aria-hidden="true" />
      <span>{FA_LABEL[status]}</span>
      <span className="wh-latin text-[12px] opacity-70">{status}</span>
    </span>
  );
}
