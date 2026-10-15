'use client';

import { Icons } from '@/components/icons';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

/**
 * AHOS brand block for the sidebar header (replaces the template's Clerk
 * organization switcher — AHOS has one operator and no org directory).
 *
 * The mark is the AHOS icon concept from owner_reference/03_app_icon.jpg:
 * a gold star on a black glass disc inside a gold ring. It is rendered with
 * inline SVG from the vendor icon kit so it stays crisp at 16–256 px and needs
 * no image asset to be loaded at runtime.
 */
export function OrgSwitcher({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2 px-1.5 py-2', className)}>
      <AhosMark className='size-8 shrink-0' />
      <div className='grid min-w-0 flex-1 leading-tight'>
        <span className='truncate text-sm font-semibold tracking-wide text-sidebar-foreground'>
          AHOS
        </span>
        <span className='truncate text-[10px] uppercase tracking-[0.16em] text-sidebar-foreground/60'>
          Opportunity Command
        </span>
      </div>
      <Badge
        variant='outline'
        className='border-primary/40 bg-primary/10 text-[9px] font-semibold uppercase tracking-wider text-primary shrink-0'
      >
        Paper only
      </Badge>
    </div>
  );
}

export function AhosMark({ className }: { className?: string }) {
  return (
    <svg viewBox='0 0 64 64' className={className} role='img' aria-label='AHOS'>
      <defs>
        <radialGradient id='ahos-disc' cx='50%' cy='38%' r='72%'>
          <stop offset='0%' stopColor='#1B2440' />
          <stop offset='62%' stopColor='#0A0F1E' />
          <stop offset='100%' stopColor='#040714' />
        </radialGradient>
        <linearGradient id='ahos-gold' x1='0%' y1='0%' x2='100%' y2='100%'>
          <stop offset='0%' stopColor='#F1D58E' />
          <stop offset='52%' stopColor='#D4AF5A' />
          <stop offset='100%' stopColor='#9C7631' />
        </linearGradient>
      </defs>
      <circle cx='32' cy='32' r='30' fill='url(#ahos-disc)' />
      <circle cx='32' cy='32' r='30' fill='none' stroke='url(#ahos-gold)' strokeWidth='2' />
      <circle cx='32' cy='32' r='24.5' fill='none' stroke='url(#ahos-gold)' strokeOpacity='0.38' strokeWidth='0.9' />
      <path
        d='M32 13.5l6.1 12.6 13.7 1.9-10 9.6 2.5 13.6L32 45.3l-12.3 6.4 2.5-13.6-10-9.6 13.7-1.9z'
        fill='url(#ahos-gold)'
      />
    </svg>
  );
}
