"use client";

/**
 * Signal arcs.
 *
 * Every arc is drawn on the visible hemisphere only (`pathFromSamples` drops samples that fall
 * behind the sphere) and is split into a head and a tail segment so dissipated signals can fade out
 * mid-flight. Geometry is written imperatively once per frame; React only owns the structure.
 */

import type { RefObject } from "react";
import type { Dictionary } from "../../lib/i18n";
import { signalChrome } from "../../lib/style";
import type { Lang, MarketNode, Signal } from "../../types/globe";

export type ArcLayerProps = {
  signals: readonly Signal[];
  nodes: ReadonlyMap<string, MarketNode>;
  lang: Lang;
  dict: Dictionary;
  activeId: string | null;
  /** `${signalId}:head` | `:tail` | `:hit` → path element. */
  pathsRef: RefObject<Map<string, SVGPathElement>>;
  /** Signal id → flash circle at the destination (absorbed signals only). */
  flashesRef: RefObject<Map<string, SVGCircleElement>>;
  onActivate: (id: string) => void;
  onDeactivate: () => void;
};

export function arcElementId(signalId: string, part: "head" | "tail" | "hit"): string {
  return `${signalId}:${part}`;
}

export function ArcLayer({
  signals,
  nodes,
  lang,
  dict,
  activeId,
  pathsRef,
  flashesRef,
  onActivate,
  onDeactivate,
}: ArcLayerProps) {
  return (
    <g className="ahos-arcs">
      {signals.map((signal) => {
        const chrome = signalChrome(signal.outcome);
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
        const reason = signal.reasonFa ?? null;
        return (
          <g
            key={signal.id}
            className="ahos-arc"
            data-arc={signal.id}
            data-outcome={signal.outcome}
            data-active={activeId === signal.id ? "true" : "false"}
          >
            <path
              ref={(element) => {
                const map = pathsRef.current ?? new Map<string, SVGPathElement>();
                if (element) map.set(arcElementId(signal.id, "head"), element);
                else map.delete(arcElementId(signal.id, "head"));
                pathsRef.current = map;
              }}
              className="ahos-arc-head"
              fill="none"
              stroke={chrome.stroke}
              strokeWidth={chrome.width}
              strokeLinecap="round"
              strokeDasharray={chrome.dasharray ?? undefined}
              opacity={chrome.startOpacity}
              d=""
            />
            <path
              ref={(element) => {
                const map = pathsRef.current ?? new Map<string, SVGPathElement>();
                if (element) map.set(arcElementId(signal.id, "tail"), element);
                else map.delete(arcElementId(signal.id, "tail"));
                pathsRef.current = map;
              }}
              className="ahos-arc-tail"
              fill="none"
              stroke={chrome.stroke}
              strokeWidth={chrome.width}
              strokeLinecap="round"
              strokeDasharray={chrome.dasharray ?? undefined}
              opacity={chrome.endOpacity}
              d=""
            />
            <path
              ref={(element) => {
                const map = pathsRef.current ?? new Map<string, SVGPathElement>();
                if (element) map.set(arcElementId(signal.id, "hit"), element);
                else map.delete(arcElementId(signal.id, "hit"));
                pathsRef.current = map;
              }}
              className="ahos-arc-hit"
              fill="none"
              stroke="transparent"
              strokeWidth={12}
              d=""
              tabIndex={0}
              role="img"
              aria-label={dict.signalAria(fromName, toName, outcomeLabel, reason)}
              onMouseEnter={() => onActivate(signal.id)}
              onMouseLeave={onDeactivate}
              onFocus={() => onActivate(signal.id)}
              onBlur={onDeactivate}
            />
            {chrome.flashAtGate ? (
              <circle
                ref={(element) => {
                  const map = flashesRef.current ?? new Map<string, SVGCircleElement>();
                  if (element) map.set(signal.id, element);
                  else map.delete(signal.id);
                  flashesRef.current = map;
                }}
                className="ahos-arc-flash"
                r={2.6}
                cx={-99}
                cy={-99}
                opacity={0}
              />
            ) : null}
          </g>
        );
      })}
    </g>
  );
}
