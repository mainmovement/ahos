// FILE: 13_missions_batch3/src/components/shell/Shell.tsx
"use client";
import { useState, type ReactNode } from "react";
import type { ChipStatus, ExecutionMode, SnapshotMeta } from "@/contract/types";
import { useFlags } from "@/lib/useFlags";
import { TruthChip } from "@/components/truth/TruthChip";
import { TierChip } from "@/components/truth/TierChip";
import { TehranClock } from "./TehranClock";
import { ViolationBar } from "./ViolationBar";
import { TelemetryContext, TelemetryStrip } from "./TelemetryStrip";

export interface ShellProps {
  title: string;
  truth: ChipStatus;
  source: string | null;
  lastRead: string | null;
  rowCount: number | null;
  snapshot?: SnapshotMeta | null;
  children: ReactNode;
}

interface NavLink {
  href: string | null;
  label: string;
  batch: string;
}

const BATCH3: NavLink[] = [
  { href: "/arena/science-radar", label: "رادار علم", batch: "دسته ۳" },
  { href: "/arena/self-debug", label: "خطایابی خودکار", batch: "دسته ۳" },
  { href: "/arena/weekly-exam", label: "آزمون هفتگی هوش", batch: "دسته ۳" },
  { href: "/arena/skill-market", label: "بازار مهارت و افزونه", batch: "دسته ۳" },
  { href: "/arena/news-center", label: "مرکز اخبار آرام", batch: "دسته ۳" },
];

const OTHER_BATCHES: NavLink[] = [
  { href: null, label: "مرکز پیام", batch: "دسته ۲" },
  { href: null, label: "خودارزیابی", batch: "دسته ۲" },
  { href: null, label: "قفسه ایده", batch: "دسته ۲" },
  { href: null, label: "پژوهشکده", batch: "دسته ۲" },
  { href: null, label: "نقشه مأموریت", batch: "دسته ۲" },
  { href: null, label: "پایش سلامت", batch: "دسته ۱" },
  { href: null, label: "درس‌ها", batch: "دسته ۱" },
  { href: null, label: "کارگاه", batch: "دسته ۱" },
  { href: null, label: "همراه", batch: "دسته ۱" },
  { href: null, label: "نفت و طلا", batch: "دسته ۱" },
];

function currentPath(): string {
  if (typeof window === "undefined") return "";
  return window.location.pathname;
}

/**
 * Shared AHOS Arena shell (batches 1–3 keep one implementation).
 * RTL frame: topbar, glass work area, right sidebar, right dock slot, bottom
 * TelemetryStrip. Permanent non-dismissible «فقط کاغذی · PAPER_ONLY» pill.
 */
export function Shell({ title, truth, source, lastRead, rowCount, snapshot, children }: ShellProps) {
  const flags = useFlags();
  const [muted, setMuted] = useState(false);
  const path = currentPath();
  const execMode: ExecutionMode | null = snapshot?.executionMode ?? null;
  const realTrading = snapshot?.realTrading ?? null;

  return (
    <div className="ah-shell" data-tier={flags.tier} data-testid="shell">
      <ViolationBar
        executionMode={flags.violation ? "LIVE" : (execMode ?? "PAPER_ONLY")}
        realTrading={flags.violation ? true : (realTrading ?? false)}
      />

      <header className="ah-top">
        <h1 style={{ fontSize: 24 }}>{title}</h1>
        <TruthChip status={truth} />
        <span className="ah-pill-paper">فقط کاغذی · PAPER_ONLY</span>
        <button
          type="button"
          className="ah-btn ah-btn-ghost"
          aria-pressed={muted}
          onClick={() => setMuted((m) => !m)}
          title="بی‌صدا (فقط نمایشی)"
        >
          {muted ? "بی‌صدا" : "با صدا"}
        </button>
        <TierChip tier={flags.tier} />
        <TehranClock />
      </header>

      <aside className="ah-side">
        <nav className="ah-panel" aria-label="صفحات">
          <h2 style={{ fontSize: 17 }} className="ah-muted">
            صفحات دسته ۳
          </h2>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }} className="flex flex-col gap-1">
            {BATCH3.map((link) => {
              const current = link.href === path;
              return (
                <li key={link.label}>
                  <a className={`ah-nav-item${current ? " ah-nav-current" : ""}`} href={link.href ?? undefined}>
                    <span>{link.label}</span>
                    <span className="ah-chip ah-chip-muted">{link.batch}</span>
                  </a>
                </li>
              );
            })}
          </ul>
          <h2 style={{ fontSize: 17 }} className="ah-muted">
            دسته‌های دیگر (PLANNED)
          </h2>
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }} className="flex flex-col gap-1">
            {OTHER_BATCHES.map((link) => (
              <li key={link.label}>
                <span className="ah-nav-item ah-nav-planned" data-testid="nav-planned">
                  <span>{link.label}</span>
                  <span className="ah-chip ah-chip-muted">
                    {link.batch} · PLANNED
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </nav>

        <div className="ah-panel ah-panel-gold" data-testid="dock-slot">
          <h2 style={{ fontSize: 17 }} className="ah-gold">
            داک راست
          </h2>
          <div className="flex flex-col gap-2" style={{ fontSize: 13 }}>
            <TruthChip status={truth} />
            <span className="ah-muted">منبع: {source ?? "—"}</span>
            <span className="ah-muted">این اسلات برای ابزارهای کمکی دسته‌های بعدی رزرو شده است.</span>
          </div>
        </div>
      </aside>

      <main className="ah-main">
        <TelemetryContext.Provider value={{ source, lastRead, rowCount }}>
          <div className="flex flex-col gap-3">{children}</div>
        </TelemetryContext.Provider>
      </main>

      <TelemetryStrip source={source} lastRead={lastRead} rowCount={rowCount} />
    </div>
  );
}
