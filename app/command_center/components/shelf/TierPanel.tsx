"use client";

/**
 * M-D5.5 — the Hardware Tier Panel.
 *
 * Five things, all read from the measured verdict and the shelf registry:
 *
 *   1. the hardware tier T8/T16/T32/GPU as the main label;
 *   2. the render tier beside it, with the ladder the spec spells out
 *      (T8 → T0/T1, T16 → T2, T32/GPU → T3);
 *   3. the measured reason the tier is what it is;
 *   4. the override, with a way to clear it back to measurement;
 *   5. the RAM-guard state against the 8 GB floor;
 *   6. the ideas «منتظر ارتقا» — awaiting an upgrade this machine has not got.
 *
 * Presentation only (AGENTS.md). Nothing here derives a token verdict, and the
 * tier never decides what a piece of evidence is worth. The panel says what the
 * hardware measured and which vetted tools are waiting on stronger hardware.
 *
 * The idea list comes only from `config/idea_shelf.json` via `/api/idea_shelf`.
 * There is no fallback list: a missing registry renders grey UNKNOWN, because
 * inventing idea names would fabricate a roadmap the registry never issued.
 */
import { useEffect, useState } from "react";

import { TruthBadge } from "@/TruthBadge";
import { webApiFetch } from "@/web_api_client";
import {
  HARDWARE_LABELS,
  HARDWARE_TIERS,
  RAM_FLOOR_GB,
  TIER_LABELS,
  writeOverride,
  type HardwareTier,
  type TierVerdict,
} from "@/components/stage/quality";
import { awaitingUpgrade, ramGuardState, type ShelfIdea } from "@/components/shelf/ideaShelf";

/**
 * The static reach of each hardware tier, per CLAUDE_DASHBOARD_2050 rule 3 and
 * the queue's M-D5.5 line. Shown beside the *measured* render tier, which is
 * what the chip actually landed on — the range is the context, not the claim.
 */
const REACH: Record<HardwareTier, string> = {
  T8: "T0 / T1",
  T16: "T2",
  T32: "T3",
  GPU: "T3",
};

type ShelfState =
  | { status: "loading" }
  | { status: "ok"; ideas: ShelfIdea[] }
  | { status: "unavailable"; reason: string }
  | { status: "error" };

export interface TierPanelProps {
  verdict: TierVerdict | null;
  /** Re-probe after the override is cleared, so the chip and panel stay in step. */
  onReprobe: () => void;
}

export default function TierPanel({ verdict, onReprobe }: TierPanelProps) {
  const [shelf, setShelf] = useState<ShelfState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    void webApiFetch("/api/idea_shelf")
      .then(async (res) => {
        if (!res.ok) return { status: "error" as const };
        const body = (await res.json()) as {
          status?: string;
          ideas?: ShelfIdea[];
          reason?: string;
        };
        if (body.status === "OK" && Array.isArray(body.ideas)) {
          return { status: "ok" as const, ideas: body.ideas };
        }
        return {
          status: "unavailable" as const,
          reason: typeof body.reason === "string" ? body.reason : "missing",
        };
      })
      .catch(() => ({ status: "error" as const }))
      .then((next) => {
        if (!cancelled) setShelf(next);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (verdict === null) {
    // Not "everything unknown": the measurements have not landed, so the panel
    // says so rather than rendering an empty ladder as if one had.
    return (
      <aside className="tier-panel" role="region" aria-label="پنل طبقهٔ سخت‌افزار" dir="rtl" lang="fa">
        <p className="tier-panel__title">پنل طبقهٔ سخت‌افزار</p>
        <p className="tier-panel__pending">در حال اندازه‌گیریِ توان…</p>
      </aside>
    );
  }

  const hw = verdict.hardware;
  const ram = ramGuardState(verdict.ramGb);
  const waiting =
    shelf.status === "ok" ? awaitingUpgrade(shelf.ideas, hw) : [];

  const clearOverride = () => {
    writeOverride(null);
    onReprobe();
  };

  return (
    <aside
      className="tier-panel"
      id="dashi-tier-panel"
      role="region"
      aria-label="پنل طبقهٔ سخت‌افزار"
      dir="rtl"
      lang="fa"
    >
      <p className="tier-panel__title">پنل طبقهٔ سخت‌افزار</p>

      <div className="tier-panel__row">
        <span className="tier-panel__key">سخت‌افزار</span>
        <span className="tier-panel__hw">
          {hw === null ? (
            <TruthBadge state="UNKNOWN" label="سخت‌افزار نامعلوم" />
          ) : (
            <>
              <b className="tier-panel__tier-id">{hw}</b>
              <span className="tier-panel__band"> {HARDWARE_LABELS[hw].fa}</span>
              <span className="tier-panel__reach"> — {REACH[hw]}</span>
            </>
          )}
        </span>
      </div>

      <div className="tier-panel__row">
        <span className="tier-panel__key">طبقهٔ نمایش</span>
        <span className="tier-panel__tier">
          <b>{TIER_LABELS[verdict.tier].fa}</b>
          <span className="tier-panel__hint"> ({TIER_LABELS[verdict.tier].en})</span>
        </span>
      </div>

      <p className="tier-panel__reason">{verdict.reasonFa}</p>

      <div className="tier-panel__row">
        <span className="tier-panel__key">حافظه</span>
        <span>
          {verdict.ramGb === null ? (
            <TruthBadge state="UNKNOWN" label="حافظه نامعلوم" />
          ) : (
            <span className={ram.state === "UNDER_FLOOR" ? "tier-panel__warn" : ""}>
              {ram.fa}
            </span>
          )}
        </span>
      </div>

      <div className="tier-panel__row">
        <span className="tier-panel__key">انتخاب دستی</span>
        {verdict.override === null ? (
          <span className="tier-panel__muted">اندازه‌گیری — انتخاب دستی ثبت نشده</span>
        ) : (
          <button
            type="button"
            className="tier-panel__clear"
            onClick={clearOverride}
            title="پاک کردن انتخاب دستی و اندازه‌گیریِ دوباره"
          >
            {TIER_LABELS[verdict.override].fa} — پاک کن
          </button>
        )}
      </div>

      <div className="tier-panel__divider" />

      <p className="tier-panel__subtitle">منتظر ارتقا</p>
      {shelf.status === "loading" ? (
        <p className="tier-panel__pending">در حال خواندن قفسهٔ ایده‌ها…</p>
      ) : shelf.status === "ok" ? (
        waiting.length === 0 ? (
          // Only honest if the registry really has no ideas above this machine —
          // an UNAVAILABLE shelf must never reach this branch.
          <p className="tier-panel__muted">هیچ ایده‌ای بالاتر از این ماشین نیست.</p>
        ) : (
          <ul className="tier-panel__ideas">
            {waiting.map((idea) => (
              <li key={idea.id} className="tier-panel__idea">
                <span className="tier-panel__idea-title">{idea.title}</span>
                <span className="tier-panel__idea-meta">
                  {idea.tier === null
                    ? "طبقهٔ نامعلوم"
                    : HARDWARE_LABELS[idea.tier].fa}
                  {typeof idea.est_ram_mb === "number" ? ` · ${idea.est_ram_mb} مگابایت` : ""}
                  {idea.core ? " · هستهٔ اصلی" : ""}
                </span>
              </li>
            ))}
          </ul>
        )
      ) : (
        // The registry is missing or unreadable. This is the load-bearing branch:
        // the panel must show UNKNOWN here, never a substituted list of names.
        <div className="tier-panel__unknown">
          <TruthBadge state="UNKNOWN" label="قفسهٔ ایده‌ها نامعلوم" />
          <p className="tier-panel__muted">
            {shelf.status === "unavailable"
              ? "config/idea_shelf.json هنوز ساخته نشده — M59.S"
              : "خواندن قفسهٔ ایده‌ها ناموفق بود"}
          </p>
        </div>
      )}

      <p className="tier-panel__footnote">
        کفِ حافظه {RAM_FLOOR_GB} گیگابایت. پله‌ها: {HARDWARE_TIERS.join(" / ")}.
      </p>
    </aside>
  );
}
