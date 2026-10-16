"use client";

/**
 * Persian tooltip for a hovered or focused signal arc. Rendered in the HTML layer (not SVG) so the
 * glass blur works, and positioned each frame by `AhosGlobe#drawOverlay` through a ref.
 */

import type { RefObject } from "react";
import type { Dictionary } from "../../lib/i18n";
import { asOfText } from "../../lib/i18n";
import type { Lang, MarketNode, Signal } from "../../types/globe";

export type ArcTooltipProps = {
  signal: Signal | null;
  nodes: ReadonlyMap<string, MarketNode>;
  lang: Lang;
  dict: Dictionary;
  now: number | null;
  elementRef: RefObject<HTMLDivElement | null>;
};

export function ArcTooltip({ signal, nodes, lang, dict, now, elementRef }: ArcTooltipProps) {
  if (!signal) return null;
  const from = nodes.get(signal.fromNodeId);
  const to = nodes.get(signal.toNodeId);
  const fromName = from ? (lang === "fa" ? from.nameFa : from.nameEn) : signal.fromNodeId;
  const toName = to ? (lang === "fa" ? to.nameFa : to.nameEn) : signal.toNodeId;
  const outcomeLabel =
    signal.outcome === "absorbed"
      ? dict.outcomeAbsorbed
      : signal.outcome === "dissipated"
        ? dict.outcomeDissipated
        : dict.outcomePending;
  const stamp = asOfText(signal.at, now, lang);

  return (
    <div className="ahos-tooltip ahos-tooltip-arc" ref={elementRef} role="tooltip">
      <span className="ahos-tooltip-title">
        {fromName} ← {toName}
        <span className="ahos-chip" data-outcome={signal.outcome}>
          {outcomeLabel}
        </span>
      </span>
      <span className="ahos-tooltip-row">
        {dict.columnAsOf}: {stamp.display ?? dict.unknownValue}
      </span>
      <span className="ahos-tooltip-row">{signal.reasonFa ?? (lang === "fa" ? "دلیلی ثبت نشده" : "no reason recorded")}</span>
    </div>
  );
}
