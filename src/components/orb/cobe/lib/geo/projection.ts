/**
 * Lat/lng → screen projection that matches what COBE actually draws.
 *
 * COBE's shaders (v2.0.1) use these conventions, which this module reproduces exactly:
 *
 *   cartesian(lat, lng) = [ cos(lat)·cos(lng), sin(lat), −cos(lat)·sin(lng) ]      (unit vector)
 *   rotation             view = rotate(world, phi, theta);  phi = longitude spin, theta = tilt
 *   marker placement     world point × 0.85   (0.8 sphere radius + 0.05 markerElevation)
 *   visibility           a marker is NOT drawn only if  z < 0  AND  |point.xy| < 0.8
 *   screen (CSS px)      x = ((p.x / aspect)·scale + 1)/2 · width
 *                        y = ( 1 − p.y·scale ) / 2 · height
 *
 * `project()` therefore lands an SVG/DOM overlay exactly on top of COBE's own dots — asserted in
 * `tests/projection.test.ts`, including the invariant that the centre of the disc at theta = 0,
 * phi = 0 is (0°N, 90°W).
 */

export type Vec3 = readonly [number, number, number];

/** Radius of the dotted sphere in COBE's dot pass (the fragment shader's `a <= .64` test). */
export const SPHERE_RADIUS = 0.8;
/** Markers and arcs sit slightly above the dots: 0.8 + markerElevation (0.05). */
export const MARKER_RADIUS = 0.85;

const DEG = Math.PI / 180;

export type LatLng = { lat: number; lng: number };

/** Unit vector for a geographic coordinate, in COBE's world frame. */
export function latLngToCartesian(lat: number, lng: number): Vec3 {
  const phi = lat * DEG;
  const lambda = lng * DEG;
  const cosPhi = Math.cos(phi);
  return [cosPhi * Math.cos(lambda), Math.sin(phi), -cosPhi * Math.sin(lambda)];
}

/** Geographic coordinate of a world-frame vector (inverse of `latLngToCartesian`). */
export function cartesianToLatLng(d: Vec3): LatLng {
  const lat = Math.asin(Math.max(-1, Math.min(1, d[1]))) / DEG;
  const lng = Math.atan2(-d[2], d[0]) / DEG;
  return { lat, lng };
}

/** Rotates a world-frame vector into COBE's view frame (x right, y up, z towards the camera). */
export function toView(d: Vec3, phi: number, theta: number): Vec3 {
  const cosPhi = Math.cos(phi);
  const sinPhi = Math.sin(phi);
  const cosTheta = Math.cos(theta);
  const sinTheta = Math.sin(theta);
  const [x, y, z] = d;
  return [
    cosPhi * x + sinPhi * z,
    sinPhi * sinTheta * x + cosTheta * y - cosPhi * sinTheta * z,
    -sinPhi * cosTheta * x + sinTheta * y + cosPhi * cosTheta * z,
  ];
}

/**
 * The world-frame direction that faces the camera at (phi, theta).
 *
 * Obtained by solving `view = rotate(world, phi, theta) = (0, 0, 1)`, i.e. the third row of COBE's
 * rotation matrix. Sanity check: at (0, 0) this is the +Z axis, which the shader maps to
 * `lng = 190° − 360° = −170°` → 90°W, the true centre of COBE's map at its default rotation.
 */
export function frontDirection(phi: number, theta = 0): Vec3 {
  const cosPhi = Math.cos(phi);
  const sinPhi = Math.sin(phi);
  const cosTheta = Math.cos(theta);
  const sinTheta = Math.sin(theta);
  return [-cosTheta * sinPhi, sinTheta, cosTheta * cosPhi];
}

/** Geographic coordinate currently facing the camera. */
export function frontLatLng(phi: number, theta = 0): LatLng {
  return cartesianToLatLng(frontDirection(phi, theta));
}

/**
 * Longitude spin that brings `lng` to the centre of the disc, and the latitude that ends up centred
 * (it is fixed by theta alone: the centre latitude is exactly `theta` in degrees).
 */
export function phiForCentre(lng: number, theta = 0): number {
  const lambda = lng * DEG;
  const cosLat = Math.cos(theta);
  return Math.atan2(-cosLat * Math.cos(lambda), -cosLat * Math.sin(lambda));
}

export type Projected = {
  /** CSS pixels from the left edge of the globe frame. */
  x: number;
  /** CSS pixels from the top edge of the globe frame. */
  y: number;
  /** False when the point sits on the far side, hidden by the sphere. */
  visible: boolean;
  /** View-frame z (positive = towards the viewer). */
  depth: number;
  /** Distance from the disc centre in view units, relative to the sphere radius. */
  radial: number;
};

export type GlobeLayout = {
  width: number;
  height: number;
  /** COBE's `scale` option (default 1). */
  scale?: number;
};

/** An arbitrary world-frame 3D point (already carrying its altitude) → screen. */
export type ProjectPoint = (world: Vec3) => Projected;

/** Builds the projector for COBE's current rotation and frame size. */
export function makeGlobeProjector(phi: number, theta: number, layout: GlobeLayout): ProjectPoint {
  const aspect = layout.width / layout.height;
  const scale = layout.scale ?? 1;
  const halfW = layout.width / 2;
  const halfH = layout.height / 2;
  return (world: Vec3): Projected => {
    const view = toView(world, phi, theta);
    const visible = view[2] >= 0 || Math.hypot(view[0], view[1]) >= SPHERE_RADIUS;
    return {
      x: ((view[0] / aspect) * scale + 1) * halfW,
      y: (1 - view[1] * scale) * halfH,
      visible,
      depth: view[2],
      radial: Math.hypot(view[0], view[1]) / SPHERE_RADIUS,
    };
  };
}

/** Projects a geographic coordinate with marker geometry (radius 0.85, COBE-identical). */
export function project(lat: number, lng: number, phi: number, theta: number, layout: GlobeLayout): Projected {
  const world = latLngToCartesian(lat, lng);
  const r = MARKER_RADIUS;
  return makeGlobeProjector(phi, theta, layout)([world[0] * r, world[1] * r, world[2] * r]);
}

/* --------------------------------------------------------- flat map projector */

export type MapRect = { x: number; y: number; width: number; height: number };

/** Largest 2:1 equirectangular rectangle that fits inside a `width x height` frame. */
export function mapRect(width: number, height: number, inset = 0.04): MapRect {
  const availableW = width * (1 - inset);
  const availableH = height * (1 - inset);
  const w = Math.min(availableW, availableH * 2);
  const h = w / 2;
  return { x: (width - w) / 2, y: (height - h) / 2, width: w, height: h };
}

/** Equirectangular projector used by `mode="map"` — same output shape, never hidden. */
export function makeFlatProjector(rect: MapRect): ProjectPoint {
  return (world: Vec3): Projected => {
    const { lat, lng } = cartesianToLatLng(world);
    return {
      x: rect.x + ((lng + 180) / 360) * rect.width,
      y: rect.y + ((90 - lat) / 180) * rect.height,
      visible: true,
      depth: 1,
      radial: 0,
    };
  };
}

/* ------------------------------------------------------------------- arcs */

export type ArcSample = { x: number; y: number; visible: boolean };

export type ArcShapeOptions = {
  /** Radius the arc's ends sit at (defaults to the marker radius). */
  baseRadius?: number;
  /** Peak extra altitude in sphere-radius units at full arc length. */
  height?: number;
};

/**
 * Samples an arc between two coordinates as a spherical quadratic Bézier — the same shape family
 * COBE v2 draws — with the peak scaled down for short hops so a Dubai→Riyadh signal does not
 * balloon. Ends are pinned to the marker radius so the curve touches the dots.
 */
export function sampleArc(
  from: LatLng,
  to: LatLng,
  projectPoint: ProjectPoint,
  options: ArcShapeOptions = {},
  steps = 40,
): ArcSample[] {
  const baseRadius = options.baseRadius ?? MARKER_RADIUS;
  const height = options.height ?? 0.2;
  const a = latLngToCartesian(from.lat, from.lng);
  const b = latLngToCartesian(to.lat, to.lng);
  const d = Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]));
  const distance = Math.acos(d);
  const mid: Vec3 = [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const length = Math.hypot(mid[0], mid[1], mid[2]);
  const direction: Vec3 = length < 1e-6 ? [0, 1, 0] : [mid[0] / length, mid[1] / length, mid[2] / length];
  const peak = baseRadius + height * Math.min(1, Math.max(0.18, distance / 1.1));
  const control: Vec3 = [direction[0] * peak, direction[1] * peak, direction[2] * peak];
  const samples: ArcSample[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const it = 1 - t;
    const world: Vec3 = [
      it * it * a[0] * baseRadius + 2 * it * t * control[0] + t * t * b[0] * baseRadius,
      it * it * a[1] * baseRadius + 2 * it * t * control[1] + t * t * b[1] * baseRadius,
      it * it * a[2] * baseRadius + 2 * it * t * control[2] + t * t * b[2] * baseRadius,
    ];
    const projected = projectPoint(world);
    samples.push({ x: projected.x, y: projected.y, visible: projected.visible });
  }
  return samples;
}

/** Screen-space arc for flat map mode: a plain quadratic Bézier bowed over the chord. */
export function sampleFlatArc(
  from: { x: number; y: number },
  to: { x: number; y: number },
  steps = 40,
): ArcSample[] {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const chord = Math.hypot(dx, dy) || 1;
  const bow = Math.min(0.22, 0.06 + chord / 4200) * chord;
  const midX = (from.x + to.x) / 2 - (dy / chord) * bow;
  const midY = (from.y + to.y) / 2 + (dx / chord) * bow;
  const samples: ArcSample[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const it = 1 - t;
    samples.push({
      x: it * it * from.x + 2 * it * t * midX + t * t * to.x,
      y: it * it * from.y + 2 * it * t * midY + t * t * to.y,
      visible: true,
    });
  }
  return samples;
}

/**
 * Builds an SVG path from samples, dropping hidden samples so the visible hemisphere is
 * respected (an arc that dips behind the globe comes back as separate pieces).
 */
export function pathFromSamples(samples: readonly ArcSample[]): string | null {
  let path = "";
  let pen = false;
  let drew = false;
  for (const sample of samples) {
    if (!sample.visible) {
      pen = false;
      continue;
    }
    const x = Math.round(sample.x * 10) / 10;
    const y = Math.round(sample.y * 10) / 10;
    if (pen) {
      path += `L${x} ${y}`;
    } else {
      path += `M${x} ${y}`;
      pen = true;
      drew = true;
    }
  }
  return drew ? path : null;
}

/** Closed path for a geographic ring (used for the Iran outline). */
export function ringPath(
  ring: readonly (readonly [number, number])[],
  projectPoint: ProjectPoint,
  radius = SPHERE_RADIUS * 1.002,
): string | null {
  const samples: ArcSample[] = ring.map(([lng, lat]) => {
    const world = latLngToCartesian(lat, lng);
    const p = projectPoint([world[0] * radius, world[1] * radius, world[2] * radius]);
    return { x: p.x, y: p.y, visible: p.visible };
  });
  return pathFromSamples(samples);
}
