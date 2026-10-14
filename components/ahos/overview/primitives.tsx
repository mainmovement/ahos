'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

/**
 * Shared glassmorphism primitives for the AHOS overview (MASTER_SPEC "Layout to
 * match": dense, glass panels with glowing edges).
 *
 * These are presentation only: they know nothing about the snapshot. A panel
 * composes them and hands them real data, or hands them nothing and gets the
 * waiting state below.
 */

type Glow = 'gold' | 'cyan' | 'none';

const GLOW: Record<Glow, string> = {
  gold: 'shadow-[0_0_44px_-16px_rgba(212,175,58,0.45)] border-primary/25',
  cyan: 'shadow-[0_0_44px_-16px_rgba(63,208,255,0.40)] border-accent/25',
  none: 'border-border/60'
};

/**
 * The panel every overview card is built on: dark glass, hairline border, a soft
 * bloom in the brand accent. `as` stays a div; nothing here is interactive.
 */
export function GlowCard({
  className,
  glow = 'gold',
  children,
  ...props
}: React.ComponentProps<'div'> & { glow?: Glow }) {
  return (
    <div
      className={cn(
        'relative flex flex-col overflow-hidden rounded-2xl border bg-gradient-to-b from-card/85 to-card/45 backdrop-blur-xl',
        GLOW[glow],
        className
      )}
      {...props}
    >
      {/* The top edge highlight the reference image reads on every panel. */}
      <span
        aria-hidden
        className='pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-foreground/25 to-transparent'
      />
      {children}
    </div>
  );
}

export function PanelTitle({
  children,
  icon,
  hint,
  className
}: {
  children: React.ReactNode;
  icon?: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center justify-between gap-2 px-4 pt-3.5 pb-2', className)}>
      <div className='flex items-center gap-2'>
        {icon ? <span className='text-primary/80'>{icon}</span> : null}
        <h3 className='text-sm font-semibold tracking-tight text-foreground'>{children}</h3>
      </div>
      {hint ? <span className='text-[10px] text-muted-foreground'>{hint}</span> : null}
    </div>
  );
}

/**
 * MASTER_SPEC: "if missing show a styled 'waiting for data' state, never
 * 'UNKNOWN'". This is that state — no numbers, no fabricated rows, a slow
 * shimmer so the panel reads as loading rather than as empty.
 */
export function Waiting({ label = 'در انتظارِ داده', className }: { label?: string; className?: string }) {
  return (
    <div
      role='status'
      dir='rtl'
      className={cn(
        'flex flex-1 items-center justify-center gap-2.5 px-4 py-6 text-xs text-muted-foreground',
        className
      )}
    >
      <span className='relative flex size-1.5'>
        <span className='absolute inline-flex h-full w-full animate-ping rounded-full bg-accent/60' />
        <span className='relative inline-flex size-1.5 rounded-full bg-accent' />
      </span>
      {label}
    </div>
  );
}

/** Persian digits — the overview's numbers never reach the DOM in Latin. */
export function faDigits(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return 'نامشخص';
  return String(n).replace(/[0-9]/g, (c) => '۰۱۲۳۴۵۶۷۸۹'[Number(c)]);
}
