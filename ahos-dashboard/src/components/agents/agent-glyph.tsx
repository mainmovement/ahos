import { cn } from "@/lib/utils";

/**
 * Neutral geometric identity glyph (hexagon + code). Deliberately NOT a
 * persona avatar: it never animates and never implies a running task — the
 * runtime chip beside it carries the state.
 */
export function AgentGlyph({ code, size = 36, className }: { code: string; size?: number; className?: string }) {
  return (
    <span aria-hidden className={cn("relative inline-flex shrink-0 items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg viewBox="0 0 40 40" width={size} height={size} className="absolute inset-0">
        <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="rgb(15 27 48 / 0.9)" stroke="rgb(230 191 95 / 0.45)" strokeWidth="1.2" />
        <polygon points="20,7 31.5,13.5 31.5,26.5 20,33 8.5,26.5 8.5,13.5" fill="none" stroke="rgb(230 191 95 / 0.15)" strokeWidth="0.8" />
      </svg>
      <span className="num relative text-[0.6rem] font-bold tracking-wide text-gold-200" dir="ltr">
        {code}
      </span>
    </span>
  );
}

/** Maturity 0..4 as filled/hollow dots with a numeric label (not colour-only). */
export function MaturityDots({ level }: { level: number }) {
  return (
    <span className="inline-flex items-center gap-1" aria-label={`maturity ${level}/4`}>
      {[0, 1, 2, 3].map((i) => (
        <span key={i} className={cn("size-1.5 rounded-full", i < level ? "bg-gold-300 shadow-[0_0_4px_var(--color-gold-300)]" : "border border-fg-5")} />
      ))}
      <span className="num ms-0.5 text-3xs text-fg-3" dir="ltr">
        L{level}
      </span>
    </span>
  );
}
