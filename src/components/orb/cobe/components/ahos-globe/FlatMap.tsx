"use client";

/**
 * Flat equirectangular dot map for `mode="map"`.
 *
 * Built from the same 1° Natural Earth land mask the globe uses (see `lib/geo/mask.generated.ts`),
 * so the dot pattern and the globe agree. One `<path>` carries every dot — a single round-capped
 * tick per land cell — which keeps the crossfade cheap on integrated graphics.
 */

import { useMemo } from "react";
import { mapDots, dotsPath, IRAN_RINGS } from "../../lib/geo/mask";
import { mapRect } from "../../lib/geo/projection";

export type FlatMapProps = {
  /** Globe-square size in CSS px (the map is fitted inside it, 2:1). */
  size: number;
  /** Drive the 0.9 s crossfade from CSS. */
  visible: boolean;
};

export function FlatMap({ size, visible }: FlatMapProps) {
  const rect = useMemo(() => mapRect(size, size, 0.03), [size]);
  const dotRadius = Math.max(0.7, size / 460);

  const { dots, iran } = useMemo(() => {
    const points = mapDots(rect.width, rect.height, dotRadius, rect.x, rect.y);
    const land = dotsPath(points.filter((dot) => !dot.iran));
    const highlighted = dotsPath(points.filter((dot) => dot.iran));
    return { dots: land, iran: highlighted };
  }, [rect.width, rect.height, rect.x, rect.y, dotRadius]);

  const iranOutline = useMemo(() => {
    let path = "";
    for (const ring of IRAN_RINGS) {
      ring.forEach(([lng, lat], index) => {
        const x = rect.x + ((lng + 180) / 360) * rect.width;
        const y = rect.y + ((90 - lat) / 180) * rect.height;
        path += `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
      });
      path += "Z";
    }
    return path;
  }, [rect.x, rect.y, rect.width, rect.height]);

  return (
    <g className="ahos-flatmap" data-visible={visible ? "true" : "false"} aria-hidden="true">
      <rect
        className="ahos-flatmap-frame"
        x={rect.x}
        y={rect.y}
        width={rect.width}
        height={rect.height}
        rx={2}
      />
      <path className="ahos-flatmap-iran" d={iranOutline} />
      <path
        className="ahos-flatmap-dots"
        d={dots}
        strokeWidth={dotRadius * 2}
        strokeLinecap="round"
        fill="none"
      />
      <path
        className="ahos-flatmap-iran-dots"
        d={iran}
        strokeWidth={dotRadius * 2.35}
        strokeLinecap="round"
        fill="none"
      />
    </g>
  );
}
