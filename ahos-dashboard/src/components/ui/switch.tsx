"use client";

import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";
import { Switch as S } from "radix-ui";
import { cn } from "@/lib/utils";

export const Switch = forwardRef<ElementRef<typeof S.Root>, ComponentPropsWithoutRef<typeof S.Root>>(function Switch({ className, ...props }, ref) {
  return (
    <S.Root
      ref={ref}
      className={cn(
        "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border border-[var(--line-hairline)] bg-ink-800 transition-colors data-[state=checked]:border-gold-500/60 data-[state=checked]:bg-gold-600/40",
        className,
      )}
      {...props}
    >
      {/* margin-inline-start positions the thumb, so the switch mirrors correctly in RTL */}
      <S.Thumb className="ms-0.5 block size-3.5 rounded-full bg-fg-3 shadow transition-[margin,background-color] duration-[var(--dur-base)] data-[state=checked]:ms-[18px] data-[state=checked]:bg-gold-300 data-[state=checked]:shadow-[var(--shadow-glow-sm)]" />
    </S.Root>
  );
});
