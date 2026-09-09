import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowUpLeft, ArrowUpRight } from "lucide-react";
import { cx, TONE, type Tone } from "@/lib/ui";
import { hashCode } from "@/lib/ui";

/* ------------------------- structure ------------------------- */

export function Kicker({ children, tone = "jade" }: { children: ReactNode; tone?: Tone }) {
  const t = TONE[tone];
  return (
    <span
      className={cx(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-medium tracking-wide",
        t.bg, t.text, "border", t.border,
      )}
    >
      <span className={cx("size-1.5 rounded-full a-pulse-soft", t.dot)} />
      {children}
    </span>
  );
}

export function SectionHead({
  kicker, title, sub, href, action, tone = "jade",
}: {
  kicker: string; title: ReactNode; sub?: string; href?: string; action?: string; tone?: Tone;
}) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-6">
      <div className="max-w-2xl">
        <Kicker tone={tone}>{kicker}</Kicker>
        <h2 className="mt-4 text-3xl font-black leading-tight sm:text-4xl">{title}</h2>
        {sub ? <p className="mt-3 text-sm leading-7 text-mist">{sub}</p> : null}
      </div>
      {href && action ? (
        <Link
          href={href}
          className="group inline-flex items-center gap-2 text-sm text-jade-300 transition hover:text-gild-300"
        >
          {action}
          <ArrowUpLeft className="size-4 transition-transform group-hover:-translate-y-0.5 group-hover:-translate-x-0.5 ltr:hidden" />
          <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 rtl:hidden" />
        </Link>
      ) : null}
    </div>
  );
}

export function Panel({
  children, className, hover = true, id,
}: {
  children: ReactNode; className?: string; hover?: boolean; id?: string;
}) {
  return (
    <div id={id} className={cx("glass rounded-3xl p-6", hover && "panel-hover", className)}>
      {children}
    </div>
  );
}

/* ------------------------- badges ------------------------- */

export function Badge({ label, tone, pulse = false, className }: {
  label: ReactNode; tone: Tone; pulse?: boolean; className?: string;
}) {
  const t = TONE[tone];
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold",
        t.bg, t.text, t.border, className,
      )}
    >
      <span className={cx("size-1.5 rounded-full", t.dot, pulse && "a-pulse-soft")} />
      {label}
    </span>
  );
}

/* ------------------------- token monogram ------------------------- */

const MONO_GRADS = [
  ["#34d399", "#0d9488"], ["#f5b73f", "#b45309"], ["#7dd3fc", "#0369a1"],
  ["#c4b5fd", "#6d28d9"], ["#f472b6", "#be185d"], ["#67e8f9", "#0e7490"],
  ["#fca5a5", "#b91c1c"], ["#bef264", "#4d7c0f"],
];

export function Monogram({ symbol, seed, size = 48 }: { symbol: string; seed: string; size?: number }) {
  const g = MONO_GRADS[hashCode(seed) % MONO_GRADS.length];
  return (
    <span
      className="relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-2xl font-black"
      style={{
        width: size, height: size,
        background: `linear-gradient(150deg, ${g[0]}26, ${g[1]}14 55%, transparent)`,
        border: `1px solid ${g[0]}45`,
        boxShadow: `inset 0 1px 0 ${g[0]}30, 0 6px 22px -12px ${g[0]}55`,
      }}
    >
      <span
        className="absolute -top-1/2 -start-1/3 size-full rotate-12 rounded-full opacity-40"
        style={{ background: `radial-gradient(circle, ${g[0]}35, transparent 70%)` }}
      />
      <span style={{ color: g[0], fontSize: size * 0.3 }} className="num tracking-tight">
        {symbol.slice(0, 3)}
      </span>
    </span>
  );
}

/* ------------------------- score bar ------------------------- */

export function ScoreBar({ label, value, toneHex, delay = 0 }: {
  label: string; value: number; toneHex: string; delay?: number;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 text-[11px] text-mist sm:w-24">{label}</span>
      <div className="h-1.5 grow overflow-hidden rounded-full bg-white/5">
        <div
          className="bar-grow h-full rounded-full"
          style={{
            width: `${value}%`,
            background: `linear-gradient(90deg, ${toneHex}55, ${toneHex})`,
            boxShadow: `0 0 12px ${toneHex}66`,
            animationDelay: `${delay}ms`,
          }}
        />
      </div>
      <span className="num w-7 shrink-0 text-end text-[11px] text-frost/90">{value}</span>
    </div>
  );
}

/* ------------------------- logo ------------------------- */

export function AhosMark({ size = 38 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden>
      <defs>
        <linearGradient id="ahg" x1="0" y1="0" x2="48" y2="48">
          <stop offset="0" stopColor="#fcd34d" />
          <stop offset="0.55" stopColor="#34d399" />
          <stop offset="1" stopColor="#0d9488" />
        </linearGradient>
      </defs>
      {/* trunk */}
      <path d="M24 42 C24 34 24 28 24 20" stroke="url(#ahg)" strokeWidth="2.6" strokeLinecap="round" />
      {/* branches */}
      <path d="M24 26 C18 24 14 20 12.5 15" stroke="url(#ahg)" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M24 22 C30 21 34 17 35.5 12" stroke="url(#ahg)" strokeWidth="1.8" strokeLinecap="round" />
      {/* roots */}
      <path d="M24 42 C20 44 16 44.5 13 46" stroke="url(#ahg)" strokeWidth="1.4" strokeLinecap="round" opacity="0.7" />
      <path d="M24 42 C28 44 32 44.5 35 46" stroke="url(#ahg)" strokeWidth="1.4" strokeLinecap="round" opacity="0.7" />
      {/* fruits */}
      <circle cx="12" cy="13" r="3.4" fill="#f5b73f" />
      <circle cx="36" cy="10" r="2.6" fill="#34d399" />
      <circle cx="24" cy="17" r="2.2" fill="#f5b73f" opacity="0.9" />
      <circle cx="12" cy="13" r="5.6" stroke="#f5b73f" strokeOpacity="0.35" strokeWidth="1" />
    </svg>
  );
}
