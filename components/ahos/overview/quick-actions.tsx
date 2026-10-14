'use client';

import Link from 'next/link';
import { Icons } from '@/components/icons';
import { GlowCard, PanelTitle } from './primitives';

/**
 * MASTER_SPEC "Right: ... Quick Actions".
 *
 * Navigation only — these are the surfaces the operator moves to from the
 * overview. Nothing here performs an action, and no action is a trade: AHOS is
 * PAPER_ONLY, so the only "paper" entry points at the paper ledger, which is
 * itself read-only presentation here.
 */
const ACTIONS: Array<{ href: string; icon: keyof typeof Icons; label: string; sub: string; tone: string }> = [
  {
    href: '/opportunities',
    icon: 'opportunities',
    label: 'فرصت‌ها',
    sub: 'ردیفِ کانونیکال',
    tone: 'text-primary'
  },
  {
    href: '/evidence',
    icon: 'evidence',
    label: 'گرافِ شواهد',
    sub: 'خط لوله و رسید',
    tone: 'text-accent'
  },
  {
    href: '/paper',
    icon: 'paperTrading',
    label: 'معاملهٔ کاغذی',
    sub: 'دفترِ PAPER ONLY',
    tone: 'text-primary'
  },
  {
    href: '/chat',
    icon: 'chat',
    label: 'گفت‌وگو با AHOS',
    sub: 'پرسش و پاسخ',
    tone: 'text-accent'
  }
];

export function QuickActions() {
  return (
    <GlowCard glow='cyan'>
      <PanelTitle icon={<span className='text-accent'>✦</span>}>دسترسیِ سریع</PanelTitle>
      <div className='grid grid-cols-2 gap-2 px-4 pb-4'>
        {ACTIONS.map((a) => {
          const Icon = Icons[a.icon];
          return (
            <Link
              key={a.href}
              href={a.href}
              className='group flex items-center gap-2.5 rounded-xl border border-border/50 bg-muted/30 px-3 py-2.5 transition-colors hover:border-primary/40 hover:bg-primary/5'
            >
              <Icon className={`size-4 shrink-0 ${a.tone}`} />
              <span className='flex flex-col leading-tight'>
                <span className='text-xs font-medium text-foreground'>{a.label}</span>
                <span className='text-[10px] text-muted-foreground'>{a.sub}</span>
              </span>
            </Link>
          );
        })}
      </div>
    </GlowCard>
  );
}
