"use client";
import { tr } from "@/src/lib/i18n";

import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { useCopyId } from "./useCopyId";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { PAPER_NOTE_FA } from "@/src/features/trade-venue/logic/truth";

/**
 * Read-only evidence viewer.
 *
 * "Open evidence" is one of the five verbs this page is allowed to offer. The
 * drawer shows provenance only (ids, source, status, timestamps) and offers
 * exactly one control: close. It never summarises a result as good or bad.
 */
export interface EvidencePayload {
  id: string;
  kind: "position" | "fill" | "outcome" | "opportunity";
  symbol: string;
  status: ChipStatus;
  sourceId: string;
  updatedAt: string | null;
  worldLabel: string;
  extra: { label: string; value: string }[];
}

export function EvidenceDrawer({
  payload,
  onClose,
}: {
  payload: EvidencePayload | null;
  onClose: () => void;
}) {
  const { copy, copiedId, failedId } = useCopyId();

  if (!payload) return null;

  return (
    <div className="tv-evidence-backdrop" data-evidence-drawer="" role="presentation">
      <div
        className="tv-evidence"
        role="dialog"
        aria-modal="true"
        aria-label={`شاهد ${payload.id}`}
        data-evidence-id={payload.id}
      >
        <div className="tv-panel__head">
          <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.EvidenceDrawer_1")}</span>
          <span className="tv-panel__title-en" dir="ltr">
            EVIDENCE · READ-ONLY
          </span>
          <div className="tv-panel__tools">
            <TruthChip status={rowDisplay({ status: payload.status, updatedAt: payload.updatedAt, sourceId: payload.sourceId }).status} size="sm" />
            <button
              type="button"
              className="tv-btn"
              data-verb="copy_id"
              onClick={() => copy(payload.id)}
              title={tr("fa", "tradeVenue.ui.EvidenceDrawer_2")}
            >
              {copiedId === payload.id ? (
                <span className="tv-copy-ok">{tr("fa", "tradeVenue.ui.EvidenceDrawer_3")}</span>
              ) : failedId === payload.id ? (
                <span className="tv-copy-ok">{tr("fa", "tradeVenue.ui.EvidenceDrawer_4")}</span>
              ) : (
                tr("fa", "tradeVenue.ui.EvidenceDrawer_5")
              )}
            </button>
            <button type="button" className="tv-btn" data-verb="close" onClick={onClose}>
              {tr("fa", "tradeVenue.ui.EvidenceDrawer_6")}
              <span className="tv-btn__en" dir="ltr">
                close
              </span>
            </button>
          </div>
        </div>
        <div className="tv-panel__body">
          <div className="tv-kv">
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_7")} v={payload.id} mono />
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_8")} v={payload.kind.toUpperCase()} mono />
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_9")} v={payload.symbol} mono />
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_10")} v={payload.worldLabel} />
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_11")} v={payload.sourceId} mono />
            <Row k={tr("fa", "tradeVenue.ui.EvidenceDrawer_12")} v={payload.updatedAt ?? tr("fa", "tradeVenue.ui.StateBlock_4")} mono />
            {payload.extra.map((item) => (
              <Row key={item.label} k={item.label} v={item.value} mono />
            ))}
          </div>
          <p className="tv-note" style={{ marginTop: 10 }}>
            <span aria-hidden="true">⛉</span>
            <span>{PAPER_NOTE_FA}</span>
          </p>
          <p className="tv-state__body">
            {tr("fa", "tradeVenue.ui.EvidenceDrawer_13")}
            {tr("fa", "tradeVenue.ui.EvidenceDrawer_14")}
          </p>
        </div>
      </div>
    </div>
  );
}

function Row({ k, v, mono = false }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="tv-kv__row">
      <span className="tv-kv__k">{k}</span>
      <span className={mono ? "tv-kv__v tv-mono" : "tv-kv__v tv-kv__v--muted"} dir="ltr">
        {v}
      </span>
    </div>
  );
}
