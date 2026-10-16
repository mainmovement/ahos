import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";

const LEGEND: readonly { status: ChipStatus; note: string }[] = [
  { status: "LIVE", note: "فید متصل و تازه" },
  { status: "STALE", note: "تازه نیست؛ زمان دارد" },
  { status: "UNKNOWN", note: "خاکستری، هرگز سبز" },
  { status: "DEMO", note: "نمایشی؛ در جمع نمی‌آید" },
  { status: "CONFLICT", note: "منابع ناسازگار" },
  { status: "REJECTED", note: "ردشده در داوری" },
];

/**
 * Footer: the Reality Map link (PLANNED is acceptable) plus the legend that
 * defines the visual language. The legend is part of the page's honesty story:
 * a reader who only sees a chip colour still learns that grey means unknown.
 */
export function RealityMapFooter({ treeSha, tier }: { treeSha: string; tier: string }) {
  return (
    <footer className="ah-footer" data-footer="">
      <a className="ah-footer__link" href="#reality-map" data-verb="link" data-state="PLANNED">
        <span aria-hidden="true">◎</span>
        نقشهٔ واقعیت
        <TruthChip status="PLANNED" size="sm" hideCode />
      </a>
      <span className="ah-faint">·</span>
      <span className="ah-footer__tree">
        ahos_trade_venue → src/features/trade-venue · src/mock/trade_venue · src/components/truth
      </span>
      <span className="ah-faint">·</span>
      <span className="ah-footer__tree">{treeSha}</span>
      <span className="ah-faint">·</span>
      <span className="ah-footer__tree">TIER {tier}</span>

      <div className="ah-footer__legend">
        {LEGEND.map((item) => (
          <span key={item.status} className="ah-legend__item" title={item.note}>
            <TruthChip status={item.status} size="sm" />
          </span>
        ))}
      </div>
    </footer>
  );
}
