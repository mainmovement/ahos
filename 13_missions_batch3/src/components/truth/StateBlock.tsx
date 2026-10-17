// FILE: 13_missions_batch3/src/components/truth/StateBlock.tsx
import type { ReactNode } from "react";
import type { ChipStatus } from "@/contract/types";
import { TruthChip } from "./TruthChip";

export interface StateBlockProps {
  state: ChipStatus;
  note?: string | null;
  children?: ReactNode;
}

const MESSAGE: Record<string, string> = {
  LOADING: "در حال بارگذاری…",
  EMPTY: "داده‌ای برای نمایش نیست",
  ERROR: "خطا در نمایش داده",
  UNAVAILABLE: "داده در دسترس نیست",
  UNKNOWN: "وضعیت نامشخص",
  PARTIAL: "نمایش ناقص",
  STALE: "داده قدیمی است",
  LIVE: "داده تازه",
  SIMULATED: "داده شبیه‌سازی‌شده",
};

/**
 * Standard component-state block. Every page supports LOADING, EMPTY, ERROR,
 * UNKNOWN, UNAVAILABLE, STALE, PARTIAL, LIVE, SIMULATED.
 */
export function StateBlock({ state, note, children }: StateBlockProps) {
  return (
    <div className="ah-state" data-state={state} data-testid="state-block">
      <TruthChip status={state} />
      <span>{MESSAGE[state] ?? "وضعیت نامشخص"}</span>
      {note ? <span className="ah-muted">{note}</span> : null}
      {children}
    </div>
  );
}
