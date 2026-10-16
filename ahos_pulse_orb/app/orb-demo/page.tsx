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
  const [morphed, setMorphed] = useState(false);
  const toggleMorph = () => setMorphed((m) => !m);
  const [calm, setCalm] = useState(true);
  const [gate, setGate] = useState({ absorbed: 0, dissipated: 0 });
  const [churnDone, setChurnDone] = useState(false);

  const baseDepartments = useMemo(() => makeDepartments(seed), [seed]);

  // compute gate counts from signals
  React.useEffect(() => {
    const a = signals.filter((s) => s.outcome === "absorbed").length;
    const d = signals.filter((s) => s.outcome === "dissipated").length;
    setGate({ absorbed: a, dissipated: d });
  }, [signals]);

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
  const handlePropChurn = async () => {
    setChurnDone(false);
    for (let i = 0; i < 50; i++) {
      setHealth((current) => ({ ...current, bpm: 55 + (i % 25), jitterMs: i % 5, stale: false }));
      await new Promise((resolve) => setTimeout(resolve, 20));
    }
    setChurnDone(true);
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
            gate={gate}
            calm={calm}
            quality="medium"
            onMorph={setMorphed}
            morphed={morphed}
          />
        </div>
        <aside className="w-72 overflow-auto border-l border-amber-400/20 p-3 text-xs">
          <div className="mb-3 font-semibold text-amber-200">کنترل‌ها</div>
          <div className="flex flex-col gap-2">
            <button onClick={handleStale} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">شبیه‌سازی فید قدیمی</button>
            <button onClick={handleJitter} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">شبیه‌سازی جیتر</button>
            <button onClick={handleBurst} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">انفجار رد دروازه</button>
            <button onClick={handleAllClear} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">همه پاک</button>
            <button onClick={() => setCalm((c) => !c)} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">Calm: {calm ? "روشن" : "خاموش"}</button>
            <button onClick={toggleMorph} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">Morph: {morphed ? "نقشه" : "اورب"}</button>
            <button onClick={handlePropChurn} className="rounded border border-amber-400/40 px-2 py-1 hover:bg-amber-400/10">50 prop updates (test)</button>
            {churnDone && <div role="status">50 prop updates complete</div>}
          </div>
          <div className="mt-4 text-stone-400">morphed: {morphed ? "بله" : "خیر"}</div>
        </aside>
      </div>
    </div>
  );
}
