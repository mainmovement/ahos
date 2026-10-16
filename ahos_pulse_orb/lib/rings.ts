export interface RingLayout {
  radius: number;
  tiltX: number;
  tiltY: number;
  tiltZ: number;
}

export function ringLayout(index: number): RingLayout {
  return {
    radius: 1.72 + index * 0.13,
    tiltX: 0.3 + (index * 0.41) % 1.2,
    tiltY: (index * 0.73) % (Math.PI * 2),
    tiltZ: (index * 0.27) % 0.8,
  };
}

export function ringRotationDelta(rate: number, deltaSeconds: number, intensity: number, stalled: boolean): number {
  return stalled ? 0 : rate * deltaSeconds * intensity;
}
