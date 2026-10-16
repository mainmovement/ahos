"use client";

import React, { useState, useMemo } from "react";
import PulseOrb from "@/components/PulseOrb";
import { makeDepartments, makeSignals, makeHealth } from "@/lib/seed";
import type { Department, Signal, Health } from "@/components/PulseOrb";

export default function OrbDemoPage() {
  const [seed] = useState(42);
  const [departments, setDepartments] = useState<Department[]>(() => makeDepartments(seed));
  const [signals, setSignals] = useState<Signal[]>(() => makeSignals(makeDepartments(seed), 7, 40));
  const [health, setHealth] = useState<Health>(() => makeHealth(1));
  const [quality, setQuality] = useState<"low" | "medium" | "high">("medium");
  const [morphed, setMorphed] = useState(false);

  // regenerate signals when departments change
  const baseDepartments = useMemo(() => makeDepartments(seed), [seed]);

  const handleStale = () => {
    setHealth((h) => ({ ...h, stale: true }));
    setDepartments((ds) => ds.map((d) => ({ ...d, lastDataAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(), status: "STALE" })));
  };
  const handleJitter = () => {
    setHealth((h) => ({ ...h, jitterMs: 900, stale: false }));
  };
  const handleBurst = () => {
    setSignals((prev) => {
      const burst: Signal[] = Array.from({ length: 12 }, (_, i) => ({
        id: `burst-${Date.now()}-${i}`,
        deptId: baseDepartments[i % baseDepartments.length].id,
        at: new Date().toISOString(),
        outcome: "dissipated",
        reason: "رد توسط دروازه ریسک",
      }));
      return [...burst, ...prev].slice(0, 80);
    });
  };
  const handleAllClear = () => {
    setHealth({ bpm: 60, jitterMs: 0, stale: false });
    setDepartments((ds) => ds.map((d) => ({ ...d, status: "LIVE", lastDataAt: new Date().toISOString(), confidence: 0.95 })));
    setSignals((prev) => prev.map((s) => ({ ...s, outcome: "absorbed" })));
  };

  return (
    <div className="flex h-screen w-screen flex-col bg-black text-stone-100" dir="rtl">
      <header className="flex items-center justify-between border-b border-amber-400/20 px-4 py-2">
        <h1 className="text-sm font-semibold text-amber-200">AHOS Pulse Orb — DEMO</h1>
        <span className="rounded bg-amber-400/20 px-2 py-0.5 text-xs text-amber-200">DEMO DATA</span>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          <PulseOrb
            health={health}
            departments={departments}
            signals={signals}
            quality={quality}
            onMorph={setMorphed}
          />
        </div>
        <aside className="w-72 overflow-auto border-l border-amber-400/20 p-3 text-xs">
          <div className="mb-3 font-semibold text-amber-200">کنترل‌ها</div>
          <div className="flex flex-col gap-2">
            <button onClick={handleStale} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">شبیه‌سازی فید قدیمی</button>
            <button onClick={handleJitter} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">شبیه‌سازی جیتر</button>
            <button onClick={handleBurst} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">انفجار رد دروازه</button>
            <button onClick={handleAllClear} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">همه پاک</button>
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-amber-200">کیفیت</label>
            <select value={quality} onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")} className="w-full rounded border border-amber-400/40 bg-black px-2 py-1">
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </div>
          <div className="mt-4 text-stone-400">
            morphed: {morphed ? "بله" : "خیر"}
          </div>
        </aside>
      </div>
    </div>
  );
}