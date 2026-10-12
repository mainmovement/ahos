/**
 * M-D6.4 sun selftest — the terminator is real, as an assertion.
 *
 * Run: npm run test:sun
 * Self-test, not independent verification.
 *
 * A painted terminator could look right and be anywhere. This one is derived from
 * the clock, so it is checkable against astronomy: the solstices put the
 * subsolar point at the tropics, the equinoxes put it on the equator, the sun
 * moves west at the rate the Earth turns, and it never leaves the tropics. A bug
 * in the series would break one of those without breaking the render, which is
 * exactly why these are numbers and not a screenshot.
 *
 * Runs without a GPU, without `window`, and without three.js.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  subsolarPoint,
  sunDirection,
  sunFacing,
  terminatorWeight,
} from "../components/stage/sun.ts";

/** Astronomical events for 2026, UTC — the fixtures the series must reproduce. */
const JUNE_SOLSTICE = new Date("2026-06-21T02:24:00Z");
const DECEMBER_SOLSTICE = new Date("2026-12-21T21:50:00Z");
const MARCH_EQUINOX = new Date("2026-03-20T10:46:00Z");
const SEPTEMBER_EQUINOX = new Date("2026-09-23T03:05:00Z");

/** Earth's axial tilt, rounded: the tropics are named for this number. */
const OBLIQUITY = 23.44;

describe("M-D6.4: the sun is where astronomy puts it", () => {
  it("reaches the tropics at the solstices", () => {
    const june = subsolarPoint(JUNE_SOLSTICE);
    const december = subsolarPoint(DECEMBER_SOLSTICE);
    // 0.5° is the tolerance the approximation and the event minute deserve; the
    // globe's dot spacing is far coarser than this, so anything inside it is the
    // same terminator.
    assert.ok(
      Math.abs(june.lat - OBLIQUITY) < 0.5,
      `June solstice declination ${june.lat.toFixed(2)}°, not the tropic of Cancer`,
    );
    assert.ok(
      Math.abs(december.lat + OBLIQUITY) < 0.5,
      `December solstice declination ${december.lat.toFixed(2)}°, not the tropic of Capricorn`,
    );
  });

  it("crosses the equator at the equinoxes", () => {
    for (const [name, date] of [
      ["March equinox", MARCH_EQUINOX],
      ["September equinox", SEPTEMBER_EQUINOX],
    ] as const) {
      const { lat } = subsolarPoint(date);
      assert.ok(Math.abs(lat) < 0.5, `${name}: subsolar latitude ${lat.toFixed(2)}°, not the equator`);
    }
  });

  it("never leaves the tropics, on any day of the year", () => {
    // A series with a wrong harmonic would escape this band somewhere mid-year,
    // and the solstice test above would not catch it.
    for (let day = 0; day < 365; day++) {
      const date = new Date(Date.UTC(2026, 0, 1) + day * 86_400_000);
      const { lat } = subsolarPoint(date);
      assert.ok(
        Math.abs(lat) <= OBLIQUITY + 0.2,
        `day ${day} has subsolar latitude ${lat.toFixed(2)}°, outside the tropics`,
      );
    }
  });
});

describe("M-D6.4: the sun moves west at the rate the Earth turns", () => {
  it("covers about 15° of longitude per hour", () => {
    const base = new Date("2026-10-12T12:00:00Z");
    const a = subsolarPoint(base);
    const b = subsolarPoint(new Date(base.getTime() + 3_600_000));
    const moved = b.lon - a.lon;
    assert.ok(
      moved < -14.9 && moved > -15.1,
      `the sun moved ${moved.toFixed(3)}° in an hour, not ~15° westward`,
    );
  });

  it("returns to the same meridian a day later", () => {
    const base = new Date("2026-10-12T06:30:00Z");
    const a = subsolarPoint(base);
    const b = subsolarPoint(new Date(base.getTime() + 86_400_000));
    const drift = Math.abs(b.lon - a.lon);
    assert.ok(
      drift < 1,
      `the sun's longitude drifted ${drift.toFixed(3)}° over a day; the series is not periodic`,
    );
  });

  it("is near Greenwich at noon UTC, within the equation of time", () => {
    // lon = -eqtime/4 at 12:00 UTC, and the equation of time's annual swing is
    // about ±16 minutes, so ±4.2° is the honest bound rather than zero.
    for (const day of [0, 45, 140, 220, 305]) {
      const date = new Date(Date.UTC(2026, 0, 1) + day * 86_400_000);
      date.setUTCHours(12, 0, 0, 0);
      const { lon } = subsolarPoint(date);
      assert.ok(
        Math.abs(lon) < 4.2,
        `day ${day} noon UTC puts the sun at ${lon.toFixed(2)}°, beyond the equation of time`,
      );
    }
  });
});

describe("M-D6.4: the direction agrees with the point", () => {
  it("is a unit vector in the frame the globe uses", () => {
    const [x, y, z] = sunDirection(new Date("2026-06-21T02:24:00Z"));
    const len = Math.hypot(x, y, z);
    assert.ok(Math.abs(len - 1) < 1e-10, `the sun direction has length ${len}`);
    // y is up, so the sun's height is the sine of its latitude.
    const { lat } = subsolarPoint(JUNE_SOLSTICE);
    assert.ok(
      Math.abs(Math.asin(y) * 180 / Math.PI - lat) < 1e-9,
      "the direction's height is not the declination",
    );
  });

  it("puts lon 0, lat 0 on the +x axis, as landDots' convention does", () => {
    // atan2(z, x) is the longitude in both modules; if they disagreed, the
    // terminator would be rotated against the continents rather than on them.
    const [x, y, z] = sunDirection(MARCH_EQUINOX);
    const lon = Math.atan2(z, x) * 180 / Math.PI;
    const lat = Math.asin(y) * 180 / Math.PI;
    const { lon: plon, lat: plat } = subsolarPoint(MARCH_EQUINOX);
    assert.ok(Math.abs(lon - plon) < 1e-9, "the direction's longitude is not the point's");
    assert.ok(Math.abs(lat - plat) < 1e-9, "the direction's latitude is not the point's");
  });
});

describe("M-D6.4: the terminator grades from day to night", () => {
  const sun: [number, number, number] = [0, 1, 0];

  it("lights the point under the sun and darkens the far side", () => {
    assert.equal(sunFacing([0, 1, 0], sun), 1);
    assert.equal(sunFacing([0, -1, 0], sun), 0);
    // The limb faces the sun edge-on, so its dot product is already 0 and the
    // clamp changes nothing: a Lambertian terminator gets no direct light.
    assert.equal(sunFacing([1, 0, 0], sun), 0);
  });

  it("is full day on the lit side and full night on the dark one", () => {
    // A spread of 0.3 means the band sits between dot products -0.3 and +0.3.
    assert.equal(terminatorWeight([0, 1, 0], sun), 1);
    assert.equal(terminatorWeight([0, -1, 0], sun), 0);
    // And the centre of the band is the middle of the gradient, not a step.
    assert.ok(
      Math.abs(terminatorWeight([1, 0, 0], sun) - 0.5) < 1e-12,
      "the terminator's centre is not half bright",
    );
  });

  it("is monotonic from the anti-solar point to the subsolar point", () => {
    // A smoothstep that inverted would put a bright band inside the night side.
    // The path runs along the sun's meridian, dot product -1 to +1, so the
    // weight can only rise.
    let prev = -1;
    for (let i = 0; i <= 40; i++) {
      const t = (i / 40) * Math.PI;
      const dir: [number, number, number] = [0, -Math.cos(t), Math.sin(t)];
      const w = terminatorWeight(dir, sun);
      assert.ok(w >= prev - 1e-12, "the terminator brightens, then darkens again");
      prev = w;
    }
  });
});
