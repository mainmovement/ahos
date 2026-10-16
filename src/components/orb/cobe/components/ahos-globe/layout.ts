/**
 * Dial geometry. Every number a component needs to place chrome around the globe lives here so the
 * ring, ticks, gauge and captions can never drift apart.
 *
 * Coordinate systems
 *  - "globe space": a `size x size` square (the COBE canvas and the marker/arc overlay).
 *  - "dial space": a square of `size + 2 * STAGE_PAD` that wraps globe space with a 26 px chrome
 *    band for the department ring, its ticks and the glass caption pills.
 */

export const STAGE_PAD = 26;

/** Dial side length for a given globe size. */
export function dialSize(size: number): number {
  return size + STAGE_PAD * 2;
}

/** Thin outer ring, 1 px gold at 25% opacity. */
export function ringRadius(size: number): number {
  return size / 2 + 11;
}

/** Tick marks sit just outside the ring, pointing outwards. */
export function tickInner(size: number): number {
  return size / 2 + 11;
}

export function tickOuter(size: number): number {
  return size / 2 + 20;
}

/**
 * Department ticks are offset 15° so no tick lands exactly at the bottom centre, leaving the gate
 * readout a clean gap.
 */
export const TICK_OFFSET_DEG = 15;

/** Tick angle for department `index` (SVG convention: 0° = 3 o'clock, 90° = straight down). */
export function tickAngle(index: number, count: number): number {
  return -90 + TICK_OFFSET_DEG + (360 / count) * index;
}

/** Gate gauge: 220° centred on the bottom, drawn clockwise like an RTL gauge (right → left). */
export const GATE_START_DEG = -20;
export const GATE_SWEEP_DEG = 220;
export const GATE_THICKNESS = 4;

export function gateRadius(size: number): number {
  return size * 0.462;
}

/** Baseline y (relative to the globe square's top-left) of the gate readout pill. */
export function gateReadoutY(size: number): number {
  return size / 2 + size * 0.44;
}

/** Baseline y of the aggregate attention pill above the globe. */
export function attentionPillY(size: number): number {
  return size / 2 - size * 0.44;
}

/** Sweep of the absorbed share and of the dissipated remainder, in SVG degrees. */
export function gateSegments(absorbedShare: number | null, dissipatedShare: number | null) {
  const absorbed = absorbedShare === null ? 0 : GATE_SWEEP_DEG * absorbedShare;
  const dissipated = dissipatedShare === null ? 0 : GATE_SWEEP_DEG * dissipatedShare;
  return { absorbed, dissipated };
}

/** Converts a polar (radius, degrees) pair to cartesian dial coordinates. */
export function polar(cx: number, cy: number, radius: number, angleDeg: number): { x: number; y: number } {
  const radians = (angleDeg * Math.PI) / 180;
  return { x: cx + radius * Math.cos(radians), y: cy + radius * Math.sin(radians) };
}

/** SVG arc path for a gauge segment starting at `startDeg` and sweeping clockwise by `sweepDeg`. */
export function arcSegment(
  cx: number,
  cy: number,
  radius: number,
  startDeg: number,
  sweepDeg: number,
): string | null {
  if (!(sweepDeg > 0.01)) return null;
  const clamped = Math.min(sweepDeg, 359.999);
  const from = polar(cx, cy, radius, startDeg);
  const to = polar(cx, cy, radius, startDeg + clamped);
  const largeArc = clamped > 180 ? 1 : 0;
  return `M${from.x.toFixed(2)} ${from.y.toFixed(2)}A${radius.toFixed(2)} ${radius.toFixed(2)} 0 ${largeArc} 1 ${to.x.toFixed(2)} ${to.y.toFixed(2)}`;
}
