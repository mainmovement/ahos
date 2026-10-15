"use client";

import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";
import { Tabs as T } from "radix-ui";
import { cn } from "@/lib/utils";

export const Tabs = T.Root;

export const TabsList = forwardRef<ElementRef<typeof T.List>, ComponentPropsWithoutRef<typeof T.List>>(function TabsList({ className, ...props }, ref) {
  return <T.List ref={ref} className={cn("inline-flex items-center gap-0.5 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-ink-950/50 p-0.5", className)} {...props} />;
});

export const TabsTrigger = forwardRef<ElementRef<typeof T.Trigger>, ComponentPropsWithoutRef<typeof T.Trigger>>(function TabsTrigger({ className, ...props }, ref) {
  return (
    <T.Trigger
      ref={ref}
      className={cn(
        "inline-flex h-6 items-center gap-1.5 whitespace-nowrap rounded-[var(--radius-sm)] px-2.5 text-xs text-fg-3 transition-colors hover:text-fg-1 data-[state=active]:bg-[var(--surface-active)] data-[state=active]:text-gold-200 data-[state=active]:shadow-[inset_0_0_0_1px_rgb(230_191_95/0.25)] [&_svg]:size-3.5",
        className,
      )}
      {...props}
    />
  );
});

export const TabsContent = forwardRef<ElementRef<typeof T.Content>, ComponentPropsWithoutRef<typeof T.Content>>(function TabsContent({ className, ...props }, ref) {
  return <T.Content ref={ref} className={cn("outline-none data-[state=active]:animate-fade-in", className)} {...props} />;
});
