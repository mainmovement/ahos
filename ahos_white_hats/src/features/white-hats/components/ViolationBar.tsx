"use client";

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
      className="relative z-20 flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-[color:rgba(227,148,148,0.45)] bg-[color:rgba(227,148,148,0.10)] px-4 py-2 text-[11.5px] leading-6 text-danger"
    >
      <span
        className="ah-demo-stripes absolute inset-x-0 top-0 h-[3px] opacity-80"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, rgba(227,148,148,.55) 0 10px, rgba(227,148,148,.15) 10px 20px)",
        }}
        aria-hidden="true"
      />
      <strong className="font-semibold">نقض سیاست اجرا</strong>
      <span className="text-danger/85">
        این اسنپ‌شات مدعی معامله‌ی واقعی است؛ صفحه فقط بازبینی می‌ماند و هیچ کنترل اجرایی ندارد.
      </span>
      <span className="ms-auto flex items-center gap-1.5">
        <span className="ah-chip ah-tone-danger">
          <span className="ah-dot" aria-hidden="true" />
          <span>حالت اجرا</span>
          <span className="ah-latin text-[8.5px] opacity-75">{snapshot.executionMode}</span>
        </span>
        <span className="ah-chip ah-tone-danger">
          <span className="ah-dot" aria-hidden="true" />
          <span>معامله واقعی</span>
          <span className="ah-latin text-[8.5px] opacity-75">
            {snapshot.realTrading ? "true" : "false"}
          </span>
        </span>
      </span>
    </div>
  );
}
