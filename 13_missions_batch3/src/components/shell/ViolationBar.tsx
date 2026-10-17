// FILE: 13_missions_batch3/src/components/shell/ViolationBar.tsx
import type { ExecutionMode } from "@/contract/types";

export interface ViolationBarProps {
  executionMode: ExecutionMode | string | null | undefined;
  realTrading: boolean | null | undefined;
}

/**
 * Full-width red VIOLATION bar. Shown when executionMode is anything other
 * than PAPER_ONLY (including UNKNOWN) or realTrading is true. Fail loud.
 */
export function ViolationBar({ executionMode, realTrading }: ViolationBarProps) {
  const violation = executionMode !== "PAPER_ONLY" || realTrading === true;
  if (!violation) return null;
  return (
    <div className="ah-violation" role="alert" data-testid="violation-bar">
      VIOLATION — وضعیت اجرا با «فقط کاغذی» سازگار نیست (executionMode=
      {executionMode ?? "—"} · realTrading={realTrading === true ? "true" : String(realTrading ?? "—")})
      — این صفحه فقط نمایشی/کاغذی است
    </div>
  );
}
