import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";

/**
 * Right-edge capsule dock: the «جهان AHOS» slot where sibling pages land when
 * they are built. Today the venue is the only live surface; every other capsule
 * is explicitly PLANNED so the dock never pretends to be a working nav.
 */
interface DockEntry {
  code: string;
  titleFa: string;
  href: string | null;
  state: ChipStatus;
  current?: boolean;
}

const ENTRIES: readonly DockEntry[] = [
  { code: "VENUE", titleFa: "میدان معامله", href: "/trade-venue", state: "LIVE", current: true },
  { code: "TRUTH", titleFa: "نقشهٔ واقعیت", href: "/reality-map", state: "PLANNED" },
  { code: "RISK", titleFa: "ریسک", href: "/risk", state: "PLANNED" },
  { code: "QUANT", titleFa: "کوانت", href: "/quant", state: "PLANNED" },
  { code: "NEWS", titleFa: "اتاق خبر", href: "/news", state: "PLANNED" },
];

export function AhosWorldDock() {
  return (
    <aside className="ah-rail" data-rail="ahos-world" aria-label="جهان AHOS">
      <span className="ah-rail__label">جهان AHOS</span>
      <div className="ah-rail__slot">
        {ENTRIES.map((entry) => {
          const content = (
            <>
              <span className="ah-rail__cap-code ah-mono" dir="ltr">
                {entry.code.slice(0, 2)}
              </span>
              <span className="ah-sr">{entry.titleFa}</span>
            </>
          );
          return (
            <span
              key={entry.code}
              className="ah-rail__cap"
              data-dock-entry={entry.code}
              data-state={entry.state}
              data-current={entry.current ? "true" : "false"}
              title={`${entry.titleFa} · ${entry.state}`}
              aria-current={entry.current ? "page" : undefined}
            >
              {content}
            </span>
          );
        })}
      </div>
      <div className="ah-rail__slot">
        {ENTRIES.filter((entry) => !entry.current).map((entry) => (
          <TruthChip
            key={entry.code}
            status={entry.state}
            size="sm"
            hideCode
            labelFa={entry.code}
          />
        ))}
      </div>
      <span className="ah-rail__note">
        اسلات جهان AHOS
        <br />
        فقط «میدان معامله» زنده است؛ بقیه برنامه‌ریزی‌شده‌اند.
      </span>
    </aside>
  );
}
