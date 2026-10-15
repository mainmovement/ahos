/**
 * Solar position — NOAA Solar Calculator algorithm (after Jean Meeus,
 * "Astronomical Algorithms"). Pure functions, unit tested in tests/solar.test.ts.
 *
 * Accuracy: declination / equation of time within ~0.01° / ~0.1 min for
 * 1900–2100, more than enough for a day/night terminator.
 */
const RAD = Math.PI / 180;
const DEG = 180 / Math.PI;

export interface SunPosition {
  /** Solar declination in degrees (+N). */
  declination: number;
  /** Equation of time in minutes (apparent − mean solar time). */
  equationOfTime: number;
  /** Latitude of the subsolar point (= declination). */
  subsolarLat: number;
  /** Longitude of the subsolar point in degrees (−180..180, +E). */
  subsolarLng: number;
}

export function julianDay(date: Date): number {
  return date.getTime() / 86_400_000 + 2_440_587.5;
}

function normalizeLng(lng: number): number {
  let x = ((lng + 180) % 360 + 360) % 360 - 180;
  if (x === -180) x = 180;
  return x;
}

export function sunPosition(date: Date): SunPosition {
  const jd = julianDay(date);
  const T = (jd - 2_451_545.0) / 36_525; // Julian centuries since J2000.0

  const L0 = (((280.46646 + T * (36000.76983 + T * 0.0003032)) % 360) + 360) % 360; // geom. mean longitude
  const M = 357.52911 + T * (35999.05029 - 0.0001537 * T); // geom. mean anomaly
  const e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T); // orbit eccentricity

  const C =
    Math.sin(M * RAD) * (1.914602 - T * (0.004817 + 0.000014 * T)) +
    Math.sin(2 * M * RAD) * (0.019993 - 0.000101 * T) +
    Math.sin(3 * M * RAD) * 0.000289; // equation of centre

  const trueLong = L0 + C;
  const omega = 125.04 - 1934.136 * T;
  const lambda = trueLong - 0.00569 - 0.00478 * Math.sin(omega * RAD); // apparent longitude

  const eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60; // mean obliquity
  const eps = eps0 + 0.00256 * Math.cos(omega * RAD); // corrected obliquity

  const declination = Math.asin(Math.sin(eps * RAD) * Math.sin(lambda * RAD)) * DEG;

  const y = Math.tan((eps / 2) * RAD) ** 2;
  const eqTime =
    4 *
    DEG *
    (y * Math.sin(2 * L0 * RAD) -
      2 * e * Math.sin(M * RAD) +
      4 * e * y * Math.sin(M * RAD) * Math.cos(2 * L0 * RAD) -
      0.5 * y * y * Math.sin(4 * L0 * RAD) -
      1.25 * e * e * Math.sin(2 * M * RAD));

  const utcMinutes = date.getUTCHours() * 60 + date.getUTCMinutes() + date.getUTCSeconds() / 60 + date.getUTCMilliseconds() / 60000;
  // At the subsolar longitude, apparent solar time is exactly 12:00.
  const subsolarLng = normalizeLng(-(utcMinutes + eqTime - 720) / 4);

  return { declination, equationOfTime: eqTime, subsolarLat: declination, subsolarLng };
}

/** Solar elevation angle (degrees above horizon) at a location. */
export function solarElevation(lat: number, lng: number, date: Date): number {
  const { declination, subsolarLng } = sunPosition(date);
  const hourAngle = normalizeLng(lng - subsolarLng);
  const cosZenith =
    Math.sin(lat * RAD) * Math.sin(declination * RAD) + Math.cos(lat * RAD) * Math.cos(declination * RAD) * Math.cos(hourAngle * RAD);
  return 90 - Math.acos(Math.max(-1, Math.min(1, cosZenith))) * DEG;
}

export interface SunTimes {
  sunrise: Date | null;
  sunset: Date | null;
  solarNoon: Date;
  /** "polar-day" | "polar-night" | null */
  polar: "polar-day" | "polar-night" | null;
}

/**
 * Sunrise / sunset for the UTC calendar day containing `date`, using the
 * standard 90.833° zenith (refraction + solar radius). Iterates once for
 * accuracy as declination/EoT change through the day.
 */
export function sunTimes(lat: number, lng: number, date: Date): SunTimes {
  const day = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  const compute = (refMs: number) => {
    const { declination, equationOfTime } = sunPosition(new Date(refMs));
    const noonMin = 720 - 4 * lng - equationOfTime;
    const cosH = Math.cos(90.833 * RAD) / (Math.cos(lat * RAD) * Math.cos(declination * RAD)) - Math.tan(lat * RAD) * Math.tan(declination * RAD);
    return { noonMin, cosH };
  };
  const first = compute(day + 12 * 3_600_000);
  const solarNoon = new Date(day + first.noonMin * 60_000);
  if (first.cosH > 1) return { sunrise: null, sunset: null, solarNoon, polar: "polar-night" };
  if (first.cosH < -1) return { sunrise: null, sunset: null, solarNoon, polar: "polar-day" };
  const H = Math.acos(first.cosH) * DEG;
  const riseGuess = day + (first.noonMin - 4 * H) * 60_000;
  const setGuess = day + (first.noonMin + 4 * H) * 60_000;
  const refine = (guess: number, sign: -1 | 1) => {
    const c = compute(guess);
    if (c.cosH > 1 || c.cosH < -1) return new Date(guess);
    const h = Math.acos(c.cosH) * DEG;
    return new Date(day + (c.noonMin + sign * 4 * h) * 60_000);
  };
  return { sunrise: refine(riseGuess, -1), sunset: refine(setGuess, 1), solarNoon, polar: null };
}

/** Antipode of the subsolar point — centre of the night hemisphere. */
export function antisolarPoint(date: Date): { lat: number; lng: number } {
  const { subsolarLat, subsolarLng } = sunPosition(date);
  return { lat: -subsolarLat, lng: normalizeLng(subsolarLng + 180) };
}
