import { STATUS_TONE, type ChipStatus, type Tone } from "./status";

const FA_LABEL: Record<ChipStatus, string> = {
  LIVE: "زنده",
  STALE: "کهنه",
  UNKNOWN: "نامشخص",
  DEMO: "نمایشی",
  CONFLICT: "تعارض",
  REJECTED: "ردشده",

  LOADING: "در حال بارگذاری",
  EMPTY: "خالی",
  ERROR: "خطا",
  UNAVAILABLE: "در دسترس نیست",
  PARTIAL: "جزئی",
  SIMULATED: "شبیه‌سازی",

  CLEAN: "پاک",
  FINDING: "یافته",
  BLOCKED: "مسدود",

  ARMED: "مسلح",
  TRIPPED: "فعال‌شده",

  OPEN: "باز",
  RESOLVED: "برطرف",

  INFO: "اطلاع",
  MINOR: "جزئی",
  MAJOR: "مهم",
  CRITICAL: "بحرانی",

  FAIL: "شکست",
  PASS: "گذشت",
};

export function statusFaLabel(status: ChipStatus): string {
  return FA_LABEL[status];
}

export interface StatusChipProps {
  status: ChipStatus;
  size?: "sm" | "lg";
  /** Show the diagonal DEMO striping on the chip itself. */
  striped?: boolean;
  title?: string;
  className?: string;
}

/**
 * The single truth chip used everywhere. Renders `data-status` and `data-tone`
 * so tests (and future e2e) can assert truth rules mechanically:
 * UNKNOWN always carries data-tone="grey" — never "live".
 */
export function StatusChip({
  status,
  size = "sm",
  striped = false,
  title,
  className = "",
}: StatusChipProps) {
  const tone: Tone = STATUS_TONE[status];
  const isDemo = status === "DEMO" || striped;
  const classes = [
    "ah-chip",
    size === "lg" ? "ah-chip-lg" : "",
    `ah-tone-${tone}`,
    isDemo ? "ah-demo-stripes" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes} data-status={status} data-tone={tone} title={title}>
      <span className="ah-dot" aria-hidden="true" />
      <span>{FA_LABEL[status]}</span>
      <span className="ah-latin text-[8.5px] opacity-70">{status}</span>
    </span>
  );
}
