"use client";

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
    <div className="ah-evidence-backdrop" data-evidence-drawer="" role="presentation">
      <div
        className="ah-evidence"
        role="dialog"
        aria-modal="true"
        aria-label={`شاهد ${payload.id}`}
        data-evidence-id={payload.id}
      >
        <div className="ah-panel__head">
          <span className="ah-panel__title">شاهد</span>
          <span className="ah-panel__title-en" dir="ltr">
            EVIDENCE · READ-ONLY
          </span>
          <div className="ah-panel__tools">
            <TruthChip status={payload.status} size="sm" />
            <button
              type="button"
              className="ah-btn"
              data-verb="copy_id"
              onClick={() => copy(payload.id)}
              title="کپی شناسهٔ شاهد (کار فقط‌خواندنی)"
            >
              {copiedId === payload.id ? (
                <span className="ah-copy-ok">کپی شد</span>
              ) : failedId === payload.id ? (
                <span className="ah-copy-ok">کپی نشد</span>
              ) : (
                "کپی شناسه"
              )}
            </button>
            <button type="button" className="ah-btn" data-verb="close" onClick={onClose}>
              بستن
              <span className="ah-btn__en" dir="ltr">
                close
              </span>
            </button>
          </div>
        </div>
        <div className="ah-panel__body">
          <div className="ah-kv">
            <Row k="شناسه" v={payload.id} mono />
            <Row k="نوع" v={payload.kind.toUpperCase()} mono />
            <Row k="نماد" v={payload.symbol} mono />
            <Row k="جهان" v={payload.worldLabel} />
            <Row k="منبع" v={payload.sourceId} mono />
            <Row k="آخرین به‌روزرسانی" v={payload.updatedAt ?? "نامشخص"} mono />
            {payload.extra.map((item) => (
              <Row key={item.label} k={item.label} v={item.value} mono />
            ))}
          </div>
          <p className="ah-note" style={{ marginTop: 10 }}>
            <span aria-hidden="true">⛉</span>
            <span>{PAPER_NOTE_FA}</span>
          </p>
          <p className="ah-state__body">
            این پنجره فقط شاهد را نشان می‌دهد: شناسه، منبع، زمان و وضعیت. هیچ عملیاتی از این‌جا
            ممکن نیست و هیچ نتیجه‌ای خوب یا بد خوانده نمی‌شود.
          </p>
        </div>
      </div>
    </div>
  );
}

function Row({ k, v, mono = false }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="ah-kv__row">
      <span className="ah-kv__k">{k}</span>
      <span className={mono ? "ah-kv__v ah-mono" : "ah-kv__v ah-kv__v--muted"} dir="ltr">
        {v}
      </span>
    </div>
  );
}
