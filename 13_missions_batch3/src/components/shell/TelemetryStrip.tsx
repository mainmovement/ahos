// FILE: 13_missions_batch3/src/components/shell/TelemetryStrip.tsx
"use client";
import { createContext, useContext, type ReactNode } from "react";
import { dash, faNum, tehranDateTime } from "@/lib/format";

export interface Telemetry {
  source: string | null;
  lastRead: string | null;
  rowCount: number | null;
}

export const TelemetryContext = createContext<Telemetry>({
  source: null,
  lastRead: null,
  rowCount: null,
});

export interface TelemetryStripProps {
  source?: string | null;
  lastRead?: string | null;
  rowCount?: number | null;
  children?: ReactNode;
}

/**
 * Bottom telemetry strip: source id, last read, row count. Falls back to the
 * Shell telemetry context when called without props. Missing values render
 * «—» — never a fabricated 0.
 */
export function TelemetryStrip(props: TelemetryStripProps) {
  const ctx = useContext(TelemetryContext);
  const source = props.source !== undefined ? props.source : ctx.source;
  const lastRead = props.lastRead !== undefined ? props.lastRead : ctx.lastRead;
  const rowCount = props.rowCount !== undefined ? props.rowCount : ctx.rowCount;

  return (
    <footer className="ah-panel ah-tele" data-testid="telemetry-strip">
      <div className="flex flex-wrap items-center gap-3" style={{ fontSize: 13 }}>
        <span className="ah-chip ah-chip-muted">منبع: {dash(source)}</span>
        <span className="ah-chip ah-chip-muted">آخرین خوانش: {tehranDateTime(lastRead)}</span>
        <span className="ah-chip ah-chip-muted">
          ردیف‌ها: {rowCount === null || rowCount === undefined ? "—" : faNum(rowCount)}
        </span>
        <span className="ah-pill-paper">فقط کاغذی · PAPER_ONLY</span>
        <span className="ah-muted">موقعیت کاغذی؛ پول واقعی در کار نیست</span>
        {props.children}
      </div>
    </footer>
  );
}
