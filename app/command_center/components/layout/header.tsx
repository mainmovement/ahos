import Link from 'next/link'
import { cn } from '@/lib/utils'
import { HeaderProps } from './types'
import { Search } from './search'
import { ProfileDropdown } from './profile-dropdown'
import { ConfigDrawer } from './config-drawer'

export function Header({ className, children, ...props }: HeaderProps) {
  return (
    <header
      className={cn(
        'z-50 h-16 bg-background/90 backdrop-blur-xl border-b border-cyan-500/20',
        'sticky top-0 w-full',
        className
      )}
      {...props}
    >
      <div className='relative flex h-full items-center gap-3 p-4'>
        <div className='flex items-center gap-3 flex-1'>
          <Link className='flex items-center space-x-2' href='/'>
            <div className='w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center'>
              <span className='text-black font-bold text-sm'>★</span>
            </div>
            <span className='hidden font-bold sm:inline-block text-amber-300'>AHOS</span>
          </Link>
          <div className='relative flex flex-1 items-center gap-3'>
            <Search placeholder='جستجوی دستور...' />
          </div>
        </div>
        <div className='flex items-center space-x-4'>
          <div className='hidden sm:flex items-center gap-2'>
            <div className='px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-xs text-amber-300'>
              PAPER ONLY
            </div>
            <div className='px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-xs text-cyan-300'>
              System Healthy
            </div>
          </div>
          <ProfileDropdown />
        </div>
        {children}
      </div>
    </header>
  )
}