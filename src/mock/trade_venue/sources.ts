/**
 * Mock source registry.
 * ============================================================================
 * Truth rule: a number is only as trustworthy as the source that produced it.
 * Every row in the fixtures names one of these sources, and the UI prints the
 * source id beside the value. `demo: true` sources are fixtures — the page also
 * carries a bundle-level DEMO banner + ribbon, so no surface can be mistaken
 * for live data even when it demonstrates the LIVE status chip.
 */

export type SourceKind = "LEDGER" | "FEED" | "SIMULATION" | "SYSTEM";

export interface MockSource {
  id: string;
  kind: SourceKind;
  labelFa: string;
  /** True ⇒ the source itself is a fixture (never a real market feed). */
  demo: boolean;
  noteFa: string;
}

export const MOCK_SOURCES = {
  ledger: {
    id: "paper.engine.ledger",
    kind: "LEDGER",
    labelFa: "دفتر موتور کاغذی",
    demo: true,
    noteFa: "دفتر محلی موتور کاغذی؛ ثبتی است و قابل بازگشایی نیست.",
  },
  goldDemo: {
    id: "feed.gold.demo",
    kind: "FEED",
    labelFa: "فید نمایشی طلا",
    demo: true,
    noteFa: "تنها فید متصل روی این میز، و آن هم نمایشی است.",
  },
  fxDelayed: {
    id: "feed.fx.delayed",
    kind: "FEED",
    labelFa: "فید ارز با تأخیر",
    demo: true,
    noteFa: "فید تأخیری؛ هر مقدار کهنه برچسب کهنه می‌گیرد.",
  },
  oilWire: {
    id: "feed.oil.wire",
    kind: "FEED",
    labelFa: "فید نفت",
    demo: true,
    noteFa: "دو منبع نفت با هم اختلاف دارند؛ تا داوری، وضعیت تناقض است.",
  },
  equitiesGap: {
    id: "feed.equities.gap",
    kind: "FEED",
    labelFa: "فید سهام (قطع)",
    demo: true,
    noteFa: "فید سهام قطع است؛ هیچ عددی ساخته نمی‌شود.",
  },
  simEngine: {
    id: "sim.engine",
    kind: "SIMULATION",
    labelFa: "موتور شبیه‌سازی",
    demo: true,
    noteFa: "کتاب شبیه‌سازی؛ از همهٔ جمع‌های کاغذی واقعی کنار گذاشته می‌شود.",
  },
  system: {
    id: "system.guard",
    kind: "SYSTEM",
    labelFa: "نگهبان سیستم",
    demo: true,
    noteFa: "یادداشت‌های نگهبان فقط‌کاغذی.",
  },
} as const satisfies Record<string, MockSource>;

export type MockSourceKey = keyof typeof MOCK_SOURCES;

export function sourceById(key: MockSourceKey): MockSource {
  return MOCK_SOURCES[key];
}

/** All sources that fed this bundle, for the telemetry strip. */
export function sourceIds(): string[] {
  return Object.values(MOCK_SOURCES).map((source) => source.id);
}
