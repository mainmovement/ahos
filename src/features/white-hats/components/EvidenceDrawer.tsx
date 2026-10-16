"use client";
import { tr } from "@/src/lib/i18n";

import { useEffect, useRef } from "react";
import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import type { EvidenceDoc, Finding } from "../types";
import { CopyIdButton } from "./CopyIdButton";
import { CloseIcon, EyeIcon } from "./icons";
import { RelTime } from "./RelTime";

export type DrawerContent =
  | { kind: "finding"; finding: Finding; inspectorTitle: string }
  | { kind: "evidence"; evidence: EvidenceDoc }
  | null;

export interface EvidenceDrawerProps {
  content: DrawerContent;
  onClose: () => void;
  onOpenEvidence: (id: string) => void;
}

/**
 * Detail drawer (verbs: view / open evidence / copy ID). For a finding it
 * shows the rule text, the evidence and what would change the verdict.
 * For an evidence id it shows the mock evidence document.
 */
export function EvidenceDrawer({ content, onClose, onOpenEvidence }: EvidenceDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!content) return;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [content, onClose]);

  if (!content) return null;

  return (
    <div className="fixed inset-0 z-40" data-testid="detail-drawer">
      <div
        className="absolute inset-0 bg-black/55"
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={content.kind === "finding" ? `جزئیات یافته ${content.finding.id}` : `شواهد ${content.evidence.id}`}
        className="wh-drawer-enter absolute inset-y-0 start-auto end-0 flex w-[min(480px,92vw)] flex-col border-s border-line bg-surface shadow-[-30px_0_60px_-30px_rgba(0,0,0,0.9)]"
      >
        <div
          className="wh-demo-edge h-[3px] opacity-80"
          aria-hidden="true"
          style={{
            backgroundImage:
              content.kind === "finding" && content.finding.demo
                ? undefined
                : "linear-gradient(90deg, var(--ah-gold-dim), transparent)",
          }}
        />
        <header className="flex items-start justify-between gap-3 px-4 pb-2 pt-3">
          <div className="flex min-w-0 flex-col">
            <span className="wh-latin text-[12px] uppercase tracking-[0.18em] text-mute">
              {content.kind === "finding" ? "Finding detail" : "Evidence document"}
            </span>
            <h3 className="mt-0.5 flex items-center gap-2 text-[13.5px] font-semibold text-ink">
              <span className="wh-id">
                {content.kind === "finding" ? content.finding.id : content.evidence.id}
              </span>
              <CopyIdButton
                value={content.kind === "finding" ? content.finding.id : content.evidence.id}
              />
            </h3>
          </div>
          <button
            ref={closeRef}
            type="button"
            className="wh-focus grid size-7 shrink-0 place-items-center rounded-sm border border-line text-mute transition-colors hover:border-linestrong hover:text-gold"
            onClick={onClose}
            aria-label={tr("fa", "whiteHats.ui.EvidenceDrawer_1")}
          >
            <CloseIcon />
          </button>
        </header>
        <div className="wh-hairline mx-4" aria-hidden="true" />

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-3.5 text-[12px] leading-6">
          {content.kind === "finding" ? (
            <FindingBody finding={content.finding} inspectorTitle={content.inspectorTitle} onOpenEvidence={onOpenEvidence} />
          ) : (
            <EvidenceBody evidence={content.evidence} />
          )}
        </div>

        <footer className="border-t border-line px-4 py-2.5 text-[12px] text-mute">
          {tr("fa", "whiteHats.ui.EvidenceDrawer_2")}
        </footer>
      </aside>
    </div>
  );
}

function FindingBody({
  finding,
  inspectorTitle,
  onOpenEvidence,
}: {
  finding: Finding;
  inspectorTitle: string;
  onOpenEvidence: (id: string) => void;
}) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-1.5" data-testid="drawer-finding-chips">
        <StatusChip status={finding.severity} />
        <StatusChip status={finding.status} />
        {finding.demo && <StatusChip status="DEMO" />}
      </div>

      <dl className="flex flex-col gap-1.5">
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_3")} value={inspectorTitle} />
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_4")} value={finding.market ?? "—"} mono />
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_5")} value={finding.openedAt ? "" : "—"}>
          {finding.openedAt ? <RelTime iso={finding.openedAt} /> : <span className="wh-num text-unknown">—</span>}
        </Row>
      </dl>

      <Block title={tr("fa", "whiteHats.ui.EvidenceDrawer_6")}>
        <p className="border-s-2 border-[color:var(--ah-gold-dim)] bg-[color:rgba(217,185,119,0.05)] px-3 py-2 text-dim">
          {finding.ruleText}
        </p>
      </Block>

      <Block title={tr("fa", "whiteHats.ui.DecisionQueue_9")}>
        {finding.evidenceId ? (
          <button
            type="button"
            className="wh-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[12px] text-cyan/90 transition-colors hover:border-linestrong hover:text-gold"
            onClick={() => onOpenEvidence(finding.evidenceId as string)}
            aria-label={`مشاهده شواهد ${finding.evidenceId}`}
          >
            <EyeIcon />
            <span className="wh-id">{finding.evidenceId}</span>
            <span>{tr("fa", "whiteHats.ui.EvidenceDrawer_7")}</span>
          </button>
        ) : (
          <span className="wh-num text-mute">—</span>
        )}
      </Block>

      <Block title={tr("fa", "whiteHats.ui.EvidenceDrawer_8")}>
        <p className="rounded-md border border-[color:rgba(120,203,209,0.16)] bg-[color:rgba(120,203,209,0.05)] px-3 py-2 text-cyan/90">
          {finding.verdictImpact}
        </p>
      </Block>
    </>
  );
}

function EvidenceBody({ evidence }: { evidence: EvidenceDoc }) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="wh-chip wh-tone-cyan">
          <span className="wh-latin text-[12px] opacity-75">{evidence.kind}</span>
        </span>
        {evidence.demo && <StatusChip status="DEMO" />}
      </div>
      <dl className="flex flex-col gap-1.5">
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_9")} value={evidence.hash} mono />
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_10")} value={evidence.sourceId} mono />
        <Row label={tr("fa", "whiteHats.ui.EvidenceDrawer_5")} value={evidence.capturedAt ? "" : "—"}>
          {evidence.capturedAt ? <RelTime iso={evidence.capturedAt} /> : <span className="wh-num text-unknown">—</span>}
        </Row>
      </dl>
      <Block title={tr("fa", "whiteHats.ui.EvidenceDrawer_11")}>
        <p className="border-s-2 border-[color:rgba(120,203,209,0.4)] bg-[color:rgba(120,203,209,0.04)] px-3 py-2 text-dim">
          {evidence.excerpt}
        </p>
      </Block>
    </>
  );
}

function Row({
  label,
  value,
  children,
  mono = false,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-mute">{label}</dt>
      <dd className={`text-dim ${mono ? "wh-id" : ""}`}>{children ?? value}</dd>
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[12px] text-mute">{title}</span>
      {children}
    </div>
  );
}
