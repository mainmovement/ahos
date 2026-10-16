import type { Department, Signal, Health } from "@/components/PulseOrb";

const DEPT_NAMES = [
  "بازار", "ریسک", "خبر", "احساس", "تکنیکال", "فاندامنتال",
  "ماکرو", "نقدینگی", "کریپتو", "فارکس", "کالا", "شاخص",
];

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeDepartments(seed = 42): Department[] {
  const rnd = mulberry32(seed);
  const now = Date.now();
  return DEPT_NAMES.map((name, i) => {
    const statusRoll = rnd();
    const status: Department["status"] =
      statusRoll > 0.85 ? "STALE" : statusRoll > 0.75 ? "DEMO" : "LIVE";
    return {
      id: `dept-${i}`,
      nameFa: name,
      rate: 0.2 + rnd() * 1.2,
      queue: Math.floor(rnd() * 6),
      lastDataAt: new Date(now - Math.floor(rnd() * 30) * 1000).toISOString(),
      confidence: 0.5 + rnd() * 0.5,
      status,
    };
  });
}

export function makeSignals(departments: Department[], seed = 7, count = 40): Signal[] {
  const rnd = mulberry32(seed);
  const outcomes: Signal["outcome"][] = ["absorbed", "dissipated", "pending"];
  const reasons = [
    "عبور از دروازه ریسک",
    "رد به دلیل نوسان بالا",
    "در انتظار تأیید",
    "عدم تطابق با سیاست",
    "تأیید شد",
  ];
  const now = Date.now();
  const sigs: Signal[] = [];
  for (let i = 0; i < count; i++) {
    const dept = departments[Math.floor(rnd() * departments.length)];
    const outcome = outcomes[Math.floor(rnd() * outcomes.length)];
    sigs.push({
      id: `sig-${i}`,
      deptId: dept.id,
      at: new Date(now - Math.floor(rnd() * 60) * 1000).toISOString(),
      outcome,
      reason: reasons[Math.floor(rnd() * reasons.length)],
    });
  }
  return sigs;
}

export function makeHealth(seed = 1): Health {
  const rnd = mulberry32(seed);
  return {
    bpm: 52 + Math.floor(rnd() * 20),
    jitterMs: Math.floor(rnd() * 80),
    stale: false,
  };
}