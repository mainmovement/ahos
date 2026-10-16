import test from "node:test";
import assert from "node:assert/strict";
import { selectCalmHighlights, selectSignalParticles } from "../lib/attention.ts";

const departments = Array.from({ length: 12 }, (_, i) => ({
  id: `d${i}`, nameFa: `بخش${i}`, rate: 1, queue: 0, lastDataAt: new Date().toISOString(),
  confidence: 1, status: i < 5 ? "STALE" : "LIVE",
}));
const signals = Array.from({ length: 100 }, (_, i) => ({
  id: `s${i}`, deptId: "d", at: new Date(0).toISOString(),
  outcome: i % 3 === 0 ? "pending" : i % 3 === 1 ? "dissipated" : "absorbed",
}));
const health = { bpm: 60, jitterMs: 0, stale: false };

test("calm attention selects at most seven highlights across rings, signals and health", () => {
  const selection = selectCalmHighlights(departments, signals, health, 7);
  assert.equal(selection.departmentIds.size + selection.signals.length, 7);
  assert.equal(selection.overflow, 65);
});

test("calm mode limits signal-bearing particles to remaining highlight budget", () => {
  const selected = selectSignalParticles(departments, signals, health, true, 16384);
  assert.equal(selected.length, 2); // five stale rings consume five of seven slots
  assert.ok(selected.every((signal) => signal.outcome !== "absorbed"));
});

test("signal count never changes the fixed texture capacity", () => {
  assert.equal(selectSignalParticles([], signals, health, false, 4096).length, 100);
  const many = Array.from({ length: 9000 }, (_, i) => ({ ...signals[0], id: String(i) }));
  assert.equal(selectSignalParticles([], many, health, false, 4096).length, 4096);
});
