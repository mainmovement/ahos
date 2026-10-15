import { solarElevation, sunPosition, sunTimes } from "@/lib/astro/solar";
import { TEHRAN } from "./scene-constants";

export interface SunInfo {
  subsolarLat: number;
  subsolarLng: number;
  tehranElevation: number;
  sunrise: Date | null;
  sunset: Date | null;
  isDayInTehran: boolean;
}

/** Sun facts for the HUD, computed locally from the real clock. */
export function computeSunInfo(ms: number): SunInfo {
  const d = new Date(ms);
  const s = sunPosition(d);
  // Use Tehran's local calendar day (local noon ≈ 08:30 UTC).
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tehran", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
  const [y, m, day] = parts.split("-").map(Number);
  const noon = new Date(Date.UTC(y!, m! - 1, day!, 8, 30));
  const times = sunTimes(TEHRAN.lat, TEHRAN.lng, noon);
  const elev = solarElevation(TEHRAN.lat, TEHRAN.lng, d);
  return { subsolarLat: s.subsolarLat, subsolarLng: s.subsolarLng, tehranElevation: elev, sunrise: times.sunrise, sunset: times.sunset, isDayInTehran: elev > -0.833 };
}
