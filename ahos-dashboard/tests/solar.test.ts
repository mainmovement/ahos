import { test } from "node:test";
import assert from "node:assert/strict";
import { antisolarPoint, solarElevation, sunPosition, sunTimes } from "../src/lib/astro/solar.ts";

const near = (actual: number, expected: number, tol: number, msg: string) =>
  assert.ok(Math.abs(actual - expected) <= tol, `${msg}: expected ${expected}±${tol}, got ${actual.toFixed(4)}`);

test("June solstice declination ≈ +23.44°", () => {
  near(sunPosition(new Date("2024-06-20T20:51:00Z")).declination, 23.44, 0.02, "declination");
});

test("March equinox declination ≈ 0°", () => {
  near(sunPosition(new Date("2024-03-20T03:06:00Z")).declination, 0, 0.02, "declination");
});

test("December solstice declination ≈ −23.44°", () => {
  near(sunPosition(new Date("2024-12-21T09:20:00Z")).declination, -23.44, 0.02, "declination");
});

test("equation of time extremes (Feb ≈ −14.2 min, Nov ≈ +16.4 min)", () => {
  near(sunPosition(new Date("2024-02-11T12:00:00Z")).equationOfTime, -14.2, 0.3, "EoT Feb");
  near(sunPosition(new Date("2024-11-03T12:00:00Z")).equationOfTime, 16.4, 0.3, "EoT Nov");
});

test("subsolar longitude follows UTC + equation of time", () => {
  const p = sunPosition(new Date("2024-03-20T12:00:00Z"));
  near(p.subsolarLng, -p.equationOfTime / 4, 1e-9, "subsolar lng at 12:00Z");
  const q = sunPosition(new Date("2024-03-20T18:00:00Z"));
  near(q.subsolarLng, -90 - q.equationOfTime / 4, 1e-9, "subsolar lng at 18:00Z");
});

test("sun is at zenith over the subsolar point", () => {
  const d = new Date("2025-08-01T09:30:00Z");
  const p = sunPosition(d);
  near(solarElevation(p.subsolarLat, p.subsolarLng, d), 90, 0.01, "elevation");
  const a = antisolarPoint(d);
  near(solarElevation(a.lat, a.lng, d), -90, 0.01, "antisolar elevation");
});

test("Tehran sunrise/sunset on 2024-06-21 (≈01:18Z / 15:54Z)", () => {
  const t = sunTimes(35.6892, 51.389, new Date("2024-06-21T08:00:00Z"));
  assert.equal(t.polar, null);
  const mins = (d: Date | null) => (d ? d.getUTCHours() * 60 + d.getUTCMinutes() + d.getUTCSeconds() / 60 : NaN);
  near(mins(t.sunrise), 1 * 60 + 18, 4, "sunrise (UTC minutes)");
  near(mins(t.sunset), 15 * 60 + 54, 4, "sunset (UTC minutes)");
});

test("polar night is reported north of the Arctic circle in December", () => {
  const t = sunTimes(78.22, 15.65, new Date("2024-12-21T12:00:00Z"));
  assert.equal(t.polar, "polar-night");
});
