"use client";
import { tr } from "@/src/lib/i18n";

import type { WhiteHatsSnapshot } from "../types";

/**
 * Full-width red VIOLATION bar. Rendered when `executionMode ≠ PAPER_ONLY`
 * or `realTrading` is true. It only reports the violation — the page has no
 * control to approve, override or enable anything.
 */
export function ViolationBar({ snapshot }: { snapshot: WhiteHatsSnapshot }) {
  return (
    <div
      role="alert"
      data-testid="violation-bar"
      className="relative z-20 flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-[color:rgba(227,148,148,0.45)] bg-[color:rgba(227,148,148,0.10)] px-4 py-2 text-[12px] leading-6 text-danger"
    >
      <span
        className="wh-demo-stripes absolute inset-x-0 top-0 h-[3px] opacity-80"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, rgba(227,148,148,.55) 0 10px, rgba(227,148,148,.15) 10px 20px)",
        }}
        aria-hidden="true"
      />
      <strong className="font-semibold">{tr("fa", "whiteHats.ui.ViolationBar_1")}</strong>
      <span className="text-danger/85">
        {tr("fa", "whiteHats.ui.ViolationBar_2")}
      </span>
      <span className="ms-auto flex items-center gap-1.5">
        <span className="wh-chip wh-tone-danger">
          <span className="wh-dot" aria-hidden="true" />
          <span>{tr("fa", "whiteHats.ui.ViolationBar_3")}</span>
          <span className="wh-latin text-[12px] opacity-75">{snapshot.executionMode}</span>
        </span>
        <span className="wh-chip wh-tone-danger">
          <span className="wh-dot" aria-hidden="true" />
          <span>{tr("fa", "whiteHats.ui.ViolationBar_4")}</span>
          <span className="wh-latin text-[12px] opacity-75">
            {snapshot.realTrading ? "true" : "false"}
          </span>
        </span>
      </span>
    </div>
  );
}
