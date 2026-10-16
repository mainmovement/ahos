"use client";

/**
 * The absorption gate — graphics only.
 *
 * A 4 px gauge around the globe's centre-bottom: the absorbed share in gold, the remainder in cool
 * grey (`#8a93a0`), filled right-to-left like an RTL dial. The readout pill with the Persian-digit
 * percentage is rendered as glass HTML by `DialCaptions`, so it can sit on a blurred backdrop.
 */

import { arcSegment, GATE_START_DEG, GATE_SWEEP_DEG, GATE_THICKNESS, gateRadius, gateSegments } from "./layout";
import type { Gate, Lang } from "../../types/globe";
import { gateMath } from "../../lib/style";
import { dictionary, localizeNumber } from "../../lib/i18n";

export const GATE_TRACK_COLOUR = "rgba(255, 255, 255, 0.07)";
export const GATE_ABSORBED_COLOUR = "#d4af37";
export const GATE_DISSIPATED_COLOUR = "#8a93a0";

export type GateArcProps = {
  gate: Gate;
  size: number;
  lang: Lang;
  /** Dial-space centre, so the gauge lines up with the department ring. */
  cx: number;
  cy: number;
};

export function GateArc({ gate, size, lang, cx, cy }: GateArcProps) {
  const dict = dictionary(lang);
  const math = gateMath(gate);
  const radius = gateRadius(size);
  const { absorbed, dissipated } = gateSegments(math.absorbedShare, math.dissipatedShare);
  const track = arcSegment(cx, cy, radius, GATE_START_DEG, GATE_SWEEP_DEG);
  const absorbedPath = arcSegment(cx, cy, radius, GATE_START_DEG, absorbed);
  const dissipatedPath = arcSegment(cx, cy, radius, GATE_START_DEG + absorbed, dissipated);

  return (
    <g className="ahos-gate" data-known={math.known ? "true" : "false"} role="img" aria-label={dict.gateAria}>
      <title>{dict.gateAria}</title>
      <desc>
        {math.known
          ? `${localizeNumber(math.absorbed, lang)} ${dict.gateAbsorbed}, ${localizeNumber(math.dissipated, lang)} ${dict.gateDissipated}`
          : dict.unknownValue}
      </desc>
      <path d={track ?? undefined} fill="none" stroke={GATE_TRACK_COLOUR} strokeWidth={GATE_THICKNESS} strokeLinecap="round" />
      {dissipatedPath ? (
        <path
          d={dissipatedPath}
          fill="none"
          stroke={GATE_DISSIPATED_COLOUR}
          strokeWidth={GATE_THICKNESS}
          strokeLinecap="round"
          opacity={0.55}
          data-part="dissipated"
        />
      ) : null}
      {absorbedPath ? (
        <path
          d={absorbedPath}
          fill="none"
          stroke={GATE_ABSORBED_COLOUR}
          strokeWidth={GATE_THICKNESS}
          strokeLinecap="round"
          data-part="absorbed"
        />
      ) : null}
    </g>
  );
}
