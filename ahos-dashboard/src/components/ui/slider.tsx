"use client";

import { Slider as S } from "radix-ui";
import { cn } from "@/lib/utils";

interface SliderProps {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label: string;
  disabled?: boolean;
  className?: string;
}

export function Slider({ value, onChange, min = 0, max = 1, step = 0.05, label, disabled, className }: SliderProps) {
  return (
    <S.Root
      value={[value]}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      onValueChange={(v) => onChange(v[0] ?? value)}
      aria-label={label}
      className={cn("relative flex h-5 w-full touch-none select-none items-center data-[disabled]:opacity-45", className)}
    >
      <S.Track className="relative h-1 grow overflow-hidden rounded-full bg-ink-700">
        <S.Range className="absolute h-full bg-[image:var(--gradient-gold)]" />
      </S.Track>
      <S.Thumb className="block size-3.5 rounded-full border border-gold-300 bg-ink-900 shadow-[var(--shadow-glow-sm)] transition-transform hover:scale-110" aria-label={label} />
    </S.Root>
  );
}
