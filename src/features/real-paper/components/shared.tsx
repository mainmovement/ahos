import type { ReactNode } from "react";
import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { tehranStamp } from "@/src/features/missions-b2/lib/model";

export const nz = (n: number | null | undefined, digits = 2): string => (typeof n === "number" && Number.isFinite(n) ? n.toFixed(digits) : "-");
export const ni = (n: number | null | undefined): string => (typeof n === "number" && Number.isFinite(n) ? String(n) : "-");
export const stamp = (iso: string | null): string => tehranStamp(iso);
export function ageText(min: number | null): string {
  if (min === null) return "-";
  return min < 120 ? `${min} min` : `${Math.round((min / 60) * 10) / 10} h`;
}
export function Kpi({ k, v, chip }: { k: string; v: string; chip?: ChipStatus }) {
  return <div className="mb-kpi"><span className="mb-kpi__k">{k}</span><span className="mb-kpi__v" dir="auto">{v}</span>{chip ? <TruthChip status={chip} size="sm" /> : null}</div>;
}
export function Tbl({ heads, children }: { heads: string[]; children: ReactNode }) {
  return (
    <div className="mb-tablewrap">
      <table className="tv-table tv-table--dense">
        <thead><tr>{heads.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
