"use client";

import type { ReactNode } from "react";
import { ToggleGroup } from "radix-ui";
import { cn } from "@/lib/utils";

interface SegmentedProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: ReactNode; title?: string; icon?: ReactNode }[];
  label: string;
  size?: "xs" | "sm";
  className?: string;
}

/** Single-select segmented control (Radix ToggleGroup — arrow-key navigable). */
export function Segmented<T extends string>({ value, onChange, options, label, size = "sm", className }: SegmentedProps<T>) {
  return (
    <ToggleGroup.Root
      type="single"
      value={value}
      onValueChange={(v) => v && onChange(v as T)}
      aria-label={label}
      className={cn("inline-flex items-center gap-0.5 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-ink-950/50 p-0.5", className)}
    >
      {options.map((o) => (
        <ToggleGroup.Item
          key={o.value}
          value={o.value}
          title={o.title}
          aria-label={o.title}
          className={cn(
            "inline-flex items-center gap-1 whitespace-nowrap rounded-[var(--radius-sm)] text-fg-3 transition-colors hover:text-fg-1 data-[state=on]:bg-[var(--surface-active)] data-[state=on]:text-gold-200 data-[state=on]:shadow-[inset_0_0_0_1px_rgb(230_191_95/0.25)] [&_svg]:size-3.5",
            size === "xs" ? "h-5 px-1.5 text-2xs" : "h-6 px-2.5 text-xs",
          )}
        >
          {o.icon}
          {o.label}
        </ToggleGroup.Item>
      ))}
    </ToggleGroup.Root>
  );
}
