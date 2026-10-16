"use client";

/**
 * Market markers + the "+N" chip.
 *
 * Markers are real DOM buttons so they can be tabbed to, hovered and read by assistive tech. Their
 * positions are written imperatively once per frame by `AhosGlobe#drawOverlay` (a transform-only
 * write keeps this off React's render path). The glyph shape encodes freshness so meaning never
 * depends on colour alone.
 */

import type { CSSProperties, RefObject } from "react";
import type { Dictionary } from "../../lib/i18n";
import { asOfText, formatPercent } from "../../lib/i18n";
import { attentionChrome, freshnessChrome } from "../../lib/style";
import type { Lang, MarketNode } from "../../types/globe";

/** Hit area of a marker button, in CSS px. */
export const MARKER_HIT_SIZE = 30;

export type VisibleMarker = {
  node: MarketNode;
  /** `highlight` = bright and (for LIVE) pulsing; `recessed` = low-emphasis but present. */
  state: "highlight" | "recessed";
};

export type MarkerLayerProps = {
  markers: readonly VisibleMarker[];
  /** Filled by the layer, then positioned imperatively each frame by `AhosGlobe#drawOverlay`. */
  markerRefs: RefObject<Map<string, HTMLButtonElement>>;
  lang: Lang;
  dict: Dictionary;
  /** Reference time for the Persian relative timestamps; `null` renders dashes. */
  now: number | null;
  activeId: string | null;
  onActivate: (id: string) => void;
  onDeactivate: () => void;
  onSelect?: (id: string) => void;
};

function MarkerGlyph({ node, state, lang }: { node: MarketNode; state: VisibleMarker["state"]; lang: Lang }) {
  const chrome = freshnessChrome(node.freshness);
  const attention = attentionChrome(node.needsAttention);
  const home = node.id === "tehran";
  const scale = (home ? 1.18 : 1) * attention.scale * (state === "recessed" ? 0.86 : 1);
  const radius = chrome.radius * scale;
  const haloRadius = attention.haloRadius * (state === "highlight" ? 1 : 0.8);

  return (
    <span className="ahos-marker-glyph" aria-hidden="true">
      <svg width={MARKER_HIT_SIZE} height={MARKER_HIT_SIZE} viewBox="-15 -15 30 30">
        {haloRadius > 0 ? <circle r={haloRadius} fill="none" stroke={attention.haloStroke} strokeWidth={1} opacity={attention.haloOpacity} /> : null}
        {chrome.shape === "disc" ? (
          <circle r={radius} fill={chrome.fill} stroke={chrome.stroke} strokeWidth={chrome.strokeWidth} opacity={chrome.opacity} />
        ) : null}
        {chrome.shape === "ring" || chrome.shape === "dashed" ? (
          <circle
            r={radius}
            fill={chrome.fill}
            stroke={chrome.stroke}
            strokeWidth={chrome.strokeWidth}
            strokeDasharray={chrome.strokeDasharray ?? undefined}
            opacity={chrome.opacity}
          />
        ) : null}
        {chrome.shape === "diamond" ? (
          <rect
            x={-radius * 0.86}
            y={-radius * 0.86}
            width={radius * 1.72}
            height={radius * 1.72}
            transform="rotate(45)"
            fill={chrome.fill}
            stroke={chrome.stroke}
            strokeWidth={chrome.strokeWidth}
            opacity={chrome.opacity}
          />
        ) : null}
        {node.freshness === "LIVE" ? (
          <circle
            r={radius + 1.5}
            fill="none"
            stroke={chrome.fill}
            strokeWidth={0.9}
            className="ahos-marker-pulse"
            opacity={0.45}
          />
        ) : null}
      </svg>
      {node.needsAttention ? (
        <span className="ahos-marker-attention-flag" aria-hidden="true" data-lang={lang} />
      ) : null}
    </span>
  );
}

export function MarkerLayer({
  markers,
  markerRefs,
  lang,
  dict,
  now,
  activeId,
  onActivate,
  onDeactivate,
  onSelect,
}: MarkerLayerProps) {
  return (
    <div className="ahos-marker-layer" data-direction={lang === "fa" ? "rtl" : "ltr"}>
      {markers.map(({ node, state }) => {
        const active = activeId === node.id;
        const stamp = asOfText(node.asOf, now, lang);
        const change = formatPercent(node.changePct, lang);
        const style: CSSProperties = { width: MARKER_HIT_SIZE, height: MARKER_HIT_SIZE };
        return (
          <button
            key={node.id}
            ref={(element) => {
              const map = markerRefs.current ?? new Map<string, HTMLButtonElement>();
              if (element) map.set(node.id, element);
              else map.delete(node.id);
              markerRefs.current = map;
            }}
            type="button"
            className="ahos-marker"
            data-marker={node.id}
            data-freshness={node.freshness}
            data-state={state}
            data-attention={node.needsAttention ? "true" : "false"}
            data-home={node.id === "tehran" ? "true" : "false"}
            data-active={active ? "true" : "false"}
            style={style}
            tabIndex={0}
            aria-label={dict.markerAria(
              lang === "fa" ? node.nameFa : node.nameEn,
              node.freshness,
              stamp.display,
            )}
            title={`${lang === "fa" ? node.nameFa : node.nameEn} · ${dict.freshness[node.freshness]}${
              stamp.absolute ? ` · ${stamp.absolute}` : ` · ${dict.unknownValue}`
            }`}
            onMouseEnter={() => onActivate(node.id)}
            onMouseLeave={onDeactivate}
            onFocus={() => onActivate(node.id)}
            onBlur={onDeactivate}
            onClick={() => onSelect?.(node.id)}
          >
            <MarkerGlyph node={node} state={state} lang={lang} />
            {active ? (
              <span className="ahos-tooltip" role="tooltip">
                <span className="ahos-tooltip-title">
                  {lang === "fa" ? node.nameFa : node.nameEn}
                  <span className="ahos-chip" data-freshness={node.freshness}>
                    {dict.freshness[node.freshness]}
                  </span>
                </span>
                <span className="ahos-tooltip-row">
                  {dict.columnAsOf}: {stamp.display ?? dict.unknownValue}
                </span>
                {change ? (
                  <span className="ahos-tooltip-row" data-sign={node.changePct && node.changePct < 0 ? "down" : "up"}>
                    {dict.columnChange}: {change}
                  </span>
                ) : (
                  <span className="ahos-tooltip-row ahos-tooltip-muted">
                    {dict.columnChange}: {dict.unknownValue}
                  </span>
                )}
                {node.needsAttention ? (
                  <span className="ahos-tooltip-row ahos-tooltip-attention">{dict.columnAttention}</span>
                ) : null}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
