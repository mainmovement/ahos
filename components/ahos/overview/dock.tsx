'use client';

import Link from 'next/link';
import { Icons } from '@/components/icons';

/**
 * MASTER_SPEC "bottom dock buttons (Evidence Graph, Knowledge Base, Learning
 * Center, System Monitor, Audit Log)".
 *
 * A fixed-looking rail of deep links to the surfaces that do not yet have their
 * own sidebar entry or that the operator wants one click away. Pure navigation —
 * the buttons carry no state and perform no action.
 */
const DOCK: Array<{ href: string; icon: keyof typeof Icons; label: string }> = [
  { href: '/evidence', icon: 'evidence', label: 'گرافِ شواهد' },
  { href: '/university', icon: 'university', label: 'پایگاهِ دانش' },
  { href: '/learning', icon: 'learning', label: 'مرکزِ یادگیری' },
  { href: '/agents', icon: 'agents', label: 'پایشِ سامانه' },
  { href: '/audit', icon: 'audit', label: 'سوابق و حسابرسی' }
];

export function Dock() {
  return (
    <nav
      aria-label='دسترسیِ سریع'
      dir='rtl'
      className='flex items-center gap-2 rounded-2xl border border-border/50 bg-card/50 p-2 backdrop-blur-xl'
    >
      {DOCK.map((d) => {
        const Icon = Icons[d.icon];
        return (
          <Link
            key={d.href}
            href={d.href}
            className='group flex flex-1 items-center justify-center gap-2 rounded-xl border border-transparent px-3 py-2 text-[11px] font-medium text-muted-foreground transition-colors hover:border-primary/35 hover:bg-primary/5 hover:text-foreground'
          >
            <Icon className='size-4 text-primary/70 transition-colors group-hover:text-primary' />
            <span>{d.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
