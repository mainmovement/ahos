import type { ReactNode } from "react";
import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import type { ViolationReport } from "@/src/features/trade-venue/logic/truth";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { StateBlock } from "@/src/components/truth/StateBlock";
import { DemoRibbon } from "@/src/components/truth/DemoRibbon";
import { PaperOnlyPill, PaperOnlyNote } from "@/src/features/trade-venue/components/PaperOnlyGuard";
import { ViolationBar } from "@/src/features/trade-venue/components/ViolationBar";
import { Expander } from "@/src/features/trade-venue/components/Expander";
import { MISSING, tehranStamp, type Highlight, type PageState } from "../lib/model";

export interface FrameProps {
  pageId: string;
  title: string;
  subtitle: string;
  status: ChipStatus;
  demo: boolean;
  sourceText: string;
  generatedAt: string | null;
  violation: ViolationReport | null;
  /** when set, replaces the body with an explicit state block (no data shown) */
  block: { state: ChipStatus; bodyFa?: string } | null;
  note?: string | null;
  children: ReactNode;
}

export function PageFrame(p: FrameProps) {
  return (
    <div className="tv-venue-root mb-root" lang="fa" dir="rtl" data-tier="t1" data-mb-page={p.pageId}>
      {p.violation ? <ViolationBar report={p.violation} fixtureProvenance={p.demo} /> : null}
      <header className="mb-head">
        <div>
          <h1 className="mb-title">{p.title}</h1>
          <p className="mb-sub">{p.subtitle}</p>
        </div>
        <div className="mb-head__chips">
          <PaperOnlyPill />
          <TruthChip status={p.status} />
        </div>
      </header>
      <p className="mb-source" data-mb-source="">
        <span>{tr("fa", "missionsB2.ui.source")}:</span> <span dir="ltr" className="tv-mono">{p.sourceText}</span>
        <span className="mb-dot">|</span>
        <span>{tr("fa", "missionsB2.ui.generatedAt")}:</span> <span dir="ltr" className="tv-mono">{tehranStamp(p.generatedAt)}</span>
        {p.generatedAt ? <span className="tv-faint"> ({tr("fa", "missionsB2.ui.tehran")})</span> : null}
      </p>
      {p.note ? <p className="mb-note">{p.note}</p> : null}
      <section className="mb-body">
        {p.demo ? <DemoRibbon /> : null}
        {p.block ? <StateBlock state={p.block.state} bodyFa={p.block.bodyFa} hintFa={tr("fa", "missionsB2.ui.readOnly")} lastUpdateText={p.generatedAt ? tehranStamp(p.generatedAt) : null} /> : p.children}
      </section>
      <PaperOnlyNote />
    </div>
  );
}

export function HighlightList({ items, hidden, empty }: { items: Highlight[]; hidden: number; empty: string }) {
  if (items.length === 0) return <p className="mb-empty">{empty}</p>;
  return (
    <div>
      <h2 className="mb-h2">
        {tr("fa", "missionsB2.ui.highlights")} <span className="tv-faint mb-count" dir="ltr">{items.length}/7</span>
      </h2>
      <ul className="mb-highlights" data-mb-highlights={items.length}>
        {items.map((h) => (
          <li key={h.id} className="mb-hl" data-status={h.status}>
            <div className="mb-hl__top">
              <TruthChip status={h.status} size="sm" />
              {h.tag ? <span className="mb-tag" dir="ltr">{h.tag}</span> : null}
            </div>
            <strong className="mb-hl__title" dir="auto">{h.title}</strong>
            {h.detail ? <span className="mb-hl__detail" dir="auto">{h.detail}</span> : null}
          </li>
        ))}
      </ul>
      {hidden > 0 ? (
        <p className="mb-more">{tr("fa", "missionsB2.ui.moreInDetails")} <span dir="ltr" className="tv-mono">+{hidden}</span></p>
      ) : null}
    </div>
  );
}

export function Details({ open, children, meta }: { open: boolean; children: ReactNode; meta?: string }) {
  return (
    <Expander id="details" title={tr("fa", "missionsB2.ui.details")} meta={meta} defaultOpen={open}>
      {children}
    </Expander>
  );
}

export function Cell({ v }: { v: string | number | null | undefined }) {
  const t = v === null || v === undefined || v === "" ? MISSING : String(v);
  return <span dir="auto" className={t === MISSING ? "tv-faint" : undefined}>{t}</span>;
}

export type { PageState };
