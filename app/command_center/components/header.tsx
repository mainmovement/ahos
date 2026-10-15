'use client';

import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { Breadcrumbs } from '@/components/breadcrumbs';
import SearchInput from '@/components/search-input';
import { AHOS_OPERATOR } from '@/lib/operator';
import { UserAvatarProfile } from '@/components/user-avatar-profile';
import { StatusChips } from '@/components/ahos/status-chips';
import { TehranClock } from '@/components/ahos/tehran-clock';
import Link from 'next/link';

/**
 * AHOS top bar (spec: "AHOS logo + search, status chips — PAPER ONLY, System
 * Health, Evidence Freshness, Uptime — clock (Tehran), owner avatar Mehrdad").
 *
 * The ported template's bar also carried a GitHub CTA, a light/dark toggle and a
 * ten-skin theme selector; AHOS has one dark skin and no repo link on the chrome,
 * so those are gone. What is kept is the part worth keeping: SidebarTrigger,
 * breadcrumbs, and the kbar ⌘K search.
 */
export default function Header() {
  return (
    <header className='sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between gap-2 border-b border-sidebar-border/60 bg-background/70 backdrop-blur-xl md:h-14'>
      <div className='flex items-center gap-2 px-3'>
        <SidebarTrigger className='-ml-1' />
        <Separator orientation='vertical' className='mr-2 h-4 data-vertical:self-center' />
        <Breadcrumbs />
      </div>

      <div className='flex items-center gap-2 px-3'>
        <StatusChips />
        <Separator orientation='vertical' className='hidden h-4 data-vertical:self-center xl:block' />
        <TehranClock className='hidden text-xs xl:flex' />
        <div className='hidden md:flex'>
          <SearchInput />
        </div>
        <Link
          href='/settings'
          aria-label='Operator profile'
          className='group flex items-center gap-2 rounded-lg border border-transparent px-1.5 py-1 transition-colors hover:border-border hover:bg-sidebar-accent'
        >
          <UserAvatarProfile
            className='h-8 w-8 rounded-lg ring-1 ring-primary/30'
            user={AHOS_OPERATOR}
          />
          <span className='hidden text-right text-xs leading-tight sm:block'>
            <span className='block font-semibold text-foreground'>{AHOS_OPERATOR.fullName}</span>
            <span className='block text-muted-foreground'>{AHOS_OPERATOR.role}</span>
          </span>
        </Link>
      </div>
    </header>
  );
}
