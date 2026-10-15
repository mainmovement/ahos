import { cn } from "@/lib/utils";

/** Kian's identity orb — a CSS-only glowing sphere (no avatar implies a task). */
export function KianOrb({ size = 32, thinking = false, className }: { size?: number; thinking?: boolean; className?: string }) {
  return (
    <span aria-hidden className={cn("relative inline-flex shrink-0 items-center justify-center", className)} style={{ width: size, height: size }}>
      <span
        className={cn("absolute inset-0 rounded-full blur-[6px]", thinking ? "animate-pulse-soft" : "")}
        style={{ background: "radial-gradient(circle at 50% 50%, rgb(230 191 95 / .55), rgb(69 208 230 / .18) 60%, transparent 70%)" }}
      />
      <span
        className="absolute inset-[2px] rounded-full border border-gold-300/50"
        style={{
          background:
            "radial-gradient(circle at 35% 30%, #fff6d8 0%, #f0d27e 18%, #b48a32 45%, #1b2d4b 75%, #060b16 100%)",
          boxShadow: "inset 0 -3px 8px rgb(69 208 230 / .35), inset 0 2px 4px rgb(255 255 255 / .35)",
        }}
      />
      <span className={cn("absolute inset-[5px] rounded-full border border-dashed border-gold-100/30", thinking && "animate-spin-slow")} />
    </span>
  );
}
