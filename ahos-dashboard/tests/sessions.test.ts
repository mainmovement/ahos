import { test } from "node:test";
import assert from "node:assert/strict";
import { EXCHANGES, formatCountdown, sessionState, zonedClock } from "../src/lib/time/sessions.ts";

const ex = (id: string) => {
  const e = EXCHANGES.find((x) => x.id === id);
  if (!e) throw new Error(id);
  return e;
};

test("zonedClock handles Tehran (UTC+3:30, no DST since 2022)", () => {
  const c = zonedClock(new Date("2026-07-01T05:30:00Z"), "Asia/Tehran");
  assert.equal(c.minutes, 9 * 60);
});

test("NYSE open mid-morning on a weekday (DST-aware)", () => {
  const s = sessionState(ex("nyse"), new Date("2026-10-14T14:00:00Z")); // Wed 10:00 EDT
  assert.equal(s.open, true);
  assert.equal(s.minutesToChange, 360);
});

test("NYSE closed on Saturday, reopens Monday 09:30", () => {
  const s = sessionState(ex("nyse"), new Date("2026-10-17T16:00:00Z")); // Sat 12:00 EDT
  assert.equal(s.open, false);
  assert.equal(s.minutesToChange, 2 * 1440 - 12 * 60 + 9 * 60 + 30);
});

test("Tokyo lunch break is closed and reopens in 30 minutes", () => {
  const s = sessionState(ex("tse-jp"), new Date("2026-10-14T03:00:00Z")); // Wed 12:00 JST
  assert.equal(s.open, false);
  assert.equal(s.minutesToChange, 30);
});

test("Tehran SE trades Saturday and is closed Friday", () => {
  assert.equal(sessionState(ex("tse-ir"), new Date("2026-10-17T06:00:00Z")).open, true); // Sat 09:30
  assert.equal(sessionState(ex("tse-ir"), new Date("2026-10-16T06:00:00Z")).open, false); // Fri
});

test("crypto is always open", () => {
  const s = sessionState(ex("crypto"), new Date());
  assert.equal(s.open, true);
  assert.equal(s.minutesToChange, null);
});

test("countdown formatting", () => {
  assert.equal(formatCountdown(45), "45m");
  assert.equal(formatCountdown(125), "2h 05m");
  assert.equal(formatCountdown(1440 + 180), "1d 3h");
});
