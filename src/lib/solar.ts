/**
 * Approximate apparent geocentric solar position, in degrees.
 * NOAA/Meeus solar elements with GMST. UTC is used as an approximation to UT1;
 * precision is appropriate for an Earth visualization, not navigation.
 * Reference: NOAA Solar Calculation Details / Astronomical Algorithms, Meeus.
 */
const radians = Math.PI / 180;
const wrap = (degrees: number) => ((degrees % 360) + 360) % 360;
export function solarPosition(date: Date): {
  latitude: number;
  longitude: number;
} {
  const jd = date.getTime() / 86400000 + 2440587.5;
  const t = (jd - 2451545) / 36525;
  const meanLongitude = wrap(280.46646 + t * (36000.76983 + t * 0.0003032));
  const meanAnomaly =
    wrap(357.52911 + t * (35999.05029 - 0.0001537 * t)) * radians;
  const center =
    Math.sin(meanAnomaly) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
    Math.sin(2 * meanAnomaly) * (0.019993 - 0.000101 * t) +
    Math.sin(3 * meanAnomaly) * 0.000289;
  const omega = (125.04 - 1934.136 * t) * radians;
  const apparentLongitude =
    (meanLongitude + center - 0.00569 - 0.00478 * Math.sin(omega)) * radians;
  const meanObliquity =
    23 +
    (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60;
  const obliquity = (meanObliquity + 0.00256 * Math.cos(omega)) * radians;
  const latitude =
    Math.asin(Math.sin(obliquity) * Math.sin(apparentLongitude)) / radians;
  const rightAscension =
    Math.atan2(
      Math.cos(obliquity) * Math.sin(apparentLongitude),
      Math.cos(apparentLongitude),
    ) / radians;
  const sidereal =
    280.46061837 +
    360.98564736629 * (jd - 2451545) +
    0.000387933 * t * t -
    (t * t * t) / 38710000;
  return { latitude, longitude: wrap(rightAscension - sidereal + 180) - 180 };
}
export function solarAltitude(
  latitude: number,
  longitude: number,
  sun: { latitude: number; longitude: number },
): number {
  return (
    Math.asin(
      Math.sin(latitude * radians) * Math.sin(sun.latitude * radians) +
        Math.cos(latitude * radians) *
          Math.cos(sun.latitude * radians) *
          Math.cos((longitude - sun.longitude) * radians),
    ) / radians
  );
}
