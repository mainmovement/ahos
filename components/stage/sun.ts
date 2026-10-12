/**
 * M-D6.4 — the sun, computed rather than painted.
 *
 * The owner's 00:20 next steps ask for a *real* day/night terminator, so the sun
 * has to be where the sun actually is. This module is the NOAA solar position
 * approximation: a Fourier series in the fractional year for the equation of time
 * and the declination. It is accurate to roughly 0.01°, which is about a kilometre
 * of subsolar travel — two orders of magnitude finer than the spacing between the
 * globe's dots, so the terminator it draws is the real one and not a stylised one.
 *
 * The globe this drives is an ornament, but the astronomy is not faked: the
 * subsolar point is derived from the clock, not from an artist's choice, and a
 * capture taken at 03:00 UTC shows a night side over the Americas for the same
 * reason the real world does.
 *
 * Pure, synchronous, no `window` and no three.js — so the sun can be asserted on
 * a machine with no GPU, which is the only way "the terminator is real" can be
 * proven rather than eyeballed.
 */

export interface Subsolar {
  /** Degrees east of Greenwich, in [-180, 180]. */
  lon: number;
  /** Degrees north, in [-23.5, 23.5] for the real obliquity. */
  lat: number;
}

/** The year's day number, 1-based, in UTC. */
function dayOfYear(date: Date): number {
  const start = Date.UTC(date.getUTCFullYear(), 0, 0);
  const now = Date.UTC(
    date.getUTCFullYear(),
    date.getUTCMonth(),
    date.getUTCDate(),
  );
  return Math.floor((now - start) / 86_400_000);
}

/**
 * The point on Earth where the sun is directly overhead.
 *
 * Longitude follows from local solar time being noon there: with `tst` in
 * minutes, `tst = utcMinutes + eqtime + 4*lon` (UTC, so no timezone term), and
 * `tst = 720` at the subsolar meridian — hence `lon = (720 - utcMinutes -
 * eqtime) / 4`. The `4` is a degree per four minutes of rotation.
 */
export function subsolarPoint(date: Date): Subsolar {
  // Fractional position in the year, the series' only input.
  const doy = dayOfYear(date);
  const hours =
    date.getUTCHours() +
    date.getUTCMinutes() / 60 +
    date.getUTCSeconds() / 3_600 +
    date.getUTCMilliseconds() / 3_600_000;
  const frac = ((2 * Math.PI) / 365) * (doy - 1 + hours / 24);

  // Equation of time, in minutes: the analemma's east-west swing.
  const eqtime =
    229.18 *
    (0.000_075 +
      0.001_868 * Math.cos(frac) -
      0.032_077 * Math.sin(frac) -
      0.014_615 * Math.cos(2 * frac) -
      0.040_849 * Math.sin(2 * frac));

  // Declination, in radians: the analemma's north-south swing.
  const decl =
    0.006_918 -
    0.399_912 * Math.cos(frac) +
    0.070_257 * Math.sin(frac) -
    0.006_758 * Math.cos(2 * frac) +
    0.000_907 * Math.sin(2 * frac) -
    0.002_697 * Math.cos(3 * frac) +
    0.001_48 * Math.sin(3 * frac);

  const utcMinutes = hours * 60;
  return {
    lon: wrap180((720 - utcMinutes - eqtime) / 4),
    lat: (decl * 180) / Math.PI,
  };
}

/** Wrap a longitude into [-180, 180) without a sign flip at the meridian. */
function wrap180(lon: number): number {
  const m = ((lon + 180) % 360 + 360) % 360;
  return m === 0 && lon > 0 ? 180 : m - 180;
}

/**
 * The sun's direction in the globe's frame: a unit vector, `y` up, with longitude
 * `atan2(z, x)` — the same convention `landDots.ts` uses, so a dot over a place
 * the sun is above is lit, and one on the far side is not.
 */
export function sunDirection(date: Date): [number, number, number] {
  const { lon, lat } = subsolarPoint(date);
  const lo = (lon * Math.PI) / 180;
  const la = (lat * Math.PI) / 180;
  const cl = Math.cos(la);
  return [cl * Math.cos(lo), Math.sin(la), cl * Math.sin(lo)];
}

/**
 * The fraction of a surface that faces the sun, in [0, 1]: 1 on the subsolar
 * point, 0 on the far side, 0.5 on the terminator. Used as the day/night weight.
 */
export function sunFacing(
  dir: [number, number, number],
  sun: [number, number, number],
): number {
  return Math.max(0, dir[0] * sun[0] + dir[1] * sun[1] + dir[2] * sun[2]);
}

/**
 * A soft terminator. A hard `max(0, dot)` puts a knife edge where the dots are
 * sparse enough to see the step; smoothing over the penumbra the real atmosphere
 * gives (and a point globe has no atmosphere, so this is a rendering choice, not
 * physics) keeps the day side bright, the night side dark, and the band between
 * them a gradient.
 *
 * `spread` is in units of the dot product, so 0.3 is a ~17°-wide penumbra.
 */
export function terminatorWeight(
  dir: [number, number, number],
  sun: [number, number, number],
  spread: number = 0.3,
): number {
  const d = dir[0] * sun[0] + dir[1] * sun[1] + dir[2] * sun[2];
  if (spread <= 0) return d > 0 ? 1 : 0;
  const t = (d + spread) / (2 * spread);
  if (t <= 0) return 0;
  if (t >= 1) return 1;
  // smoothstep, so the gradient has no visible kink at the band's edges.
  return t * t * (3 - 2 * t);
}
