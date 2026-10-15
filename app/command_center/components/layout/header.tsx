import Link from 'next/link'
import { cn } from '@/lib/utils'
import { HeaderProps } from './types'
import { TopNav } from './top-nav'
import { Search } from './search'
import { ConfigDrawer } from './config-drawer'
import { ProfileDropdown } from './profile-dropdown'
import { LayoutDashboardIcon } from 'lucide-react'

export function Header({ className, links, ...props }: HeaderProps) {
  return (
    <header
      data-layout-scroll={cn('sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60', className)}
      {...props}
    >
      <div className='container flex h-14 items-center'>
        <div className='mr-4 hidden md:flex'>
          <Link className='mr-6 flex items-center space-x-2' href='/'>
            <LayoutDashboardIcon className='h-6 w-6 text-cyan-400' />
            <span className='hidden font-bold sm:inline-block text-cyan-300'>AHOS</span>
          </Link>
        </div>
        <div className='relative mr-4 flex flex-1 items-center space-x-4 md:grow'>
          <Search placeholder='Search command center...' />
        </div>
        <div className='flex items-center space-x-2 md:absolute md:right-6 md:top-4'>
          <TopNav links={links} />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </div>
    </header>
  )
}