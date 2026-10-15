"use client";
import { useEffect, useState } from "react";
import {
  countryRings,
  tehran,
  type CountryCollection,
} from "../../lib/geography";
import { solarAltitude, solarPosition } from "../../lib/solar";
import type { Language } from "../../lib/navigation";
export function EarthFallback({
  countries,
  language,
  onIran,
}: {
  countries: CountryCollection | null;
  language: Language;
  onIran: () => void;
}) {
  const [date, setDate] = useState<Date | null>(null);
  useEffect(() => {
    const timer = setInterval(() => {
      if (!document.hidden) setDate(new Date());
    }, 30000);
    const frame = requestAnimationFrame(() => setDate(new Date()));
    return () => {
      clearInterval(timer);
      cancelAnimationFrame(frame);
    };
  }, []);
  const sun = date ? solarPosition(date) : null;
  return (
    <div className="dc-earth-fallback">
      <svg
        viewBox="0 0 720 360"
        role="img"
        aria-label={
          language === "fa"
            ? "نقشهٔ دوبعدی جایگزین زمین"
            : "Two-dimensional Earth fallback map"
        }
      >
        <rect width="720" height="360" className="dc-map-ocean" />
        {Array.from({ length: 13 }, (_, i) => (
          <path
            key={`lon${i}`}
            d={`M${i * 60} 0V360`}
            className="dc-map-grid"
          />
        ))}
        {Array.from({ length: 7 }, (_, i) => (
          <path
            key={`lat${i}`}
            d={`M0 ${i * 60}H720`}
            className="dc-map-grid"
          />
        ))}
        {countries?.features.map((country) => (
          <path
            key={country.properties.iso}
            d={countryRings(country)
              .map(
                (ring) =>
                  ring
                    .map(
                      ([lng, lat], i) =>
                        `${i === 0 ? "M" : "L"}${(lng + 180) * 2},${(90 - lat) * 2}`,
                    )
                    .join(" ") + "Z",
              )
              .join(" ")}
            className={
              country.properties.iso === "IRN"
                ? "dc-map-iran"
                : "dc-map-country"
            }
          />
        ))}
        {sun &&
          Array.from({ length: 72 * 36 }, (_, i) => {
            const lat = 87.5 - Math.floor(i / 72) * 5;
            const lng = -177.5 + (i % 72) * 5;
            return solarAltitude(lat, lng, sun) < 0 ? (
              <rect
                key={i}
                x={(lng + 177.5) * 2}
                y={(87.5 - lat) * 2}
                width="10"
                height="10"
                className="dc-map-night"
              />
            ) : null;
          })}
        <circle
          cx={(tehran.lng + 180) * 2}
          cy={(90 - tehran.lat) * 2}
          r="4"
          className="dc-map-city"
        />
        <text
          x={(tehran.lng + 180) * 2 + 9}
          y={(90 - tehran.lat) * 2 - 7}
          className="dc-map-label"
        >
          TEHRAN
        </text>
      </svg>
      <div className="dc-fallback-notice">
        <span>2D FALLBACK</span>
        <p>
          {language === "fa"
            ? "رندر سه‌بعدی در دسترس نیست؛ نقشهٔ محلی جایگزین نمایش داده می‌شود."
            : "3D rendering unavailable. Showing the bundled local map instead."}
        </p>
        <button className="ah-secondary-button" onClick={onIran}>
          {language === "fa" ? "مشخصات ایران" : "Iran details"}
        </button>
      </div>
    </div>
  );
}
