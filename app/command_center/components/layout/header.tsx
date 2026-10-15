import Link from 'next/link'
import { cn } from '@/lib/utils'
import { HeaderProps } from './types'
import { Search } from './search'
import { ProfileDropdown } from './profile-dropdown'
import { ConfigDrawer } from './config-drawer'
import { ThemeSwitch } from './theme-switch'
import { Bell } from 'lucide-react'

export function Header({ className, children, ...props }: HeaderProps) {
  const topNav = [
    {
      title: 'کنترل مرکزی',
      href: '/command_center',
      isActive: true,
      disabled: false,
    },
    {
      title: 'کشف',
      href: '/discovery',
      isActive: false,
      disabled: false,
    },
    {
      title: 'فرصت‌ها',
      href: '/opportunities',
      isActive: false,
      disabled: false,
    },
    {
      title: 'هوش بازار',
      href: '/intelligence',
      isActive: false,
      disabled: false,
    },
  ]

  return (
    <header
      className={cn(
        'z-50 h-16 bg-black/90 backdrop-blur-xl border-b border-[#D4AF37]/30',
        'sticky top-0 w-full',
        className
      )}
      {...props}
    >
      <div className='relative flex h-full items-center gap-3 p-4'>
        <div className='flex items-center gap-3 flex-1'>
          <Link className='flex items-center space-x-2' href='/'>
            <div className='w-8 h-8 bg-gradient-to-br from-[#D4AF37] to-[#B8941F] rounded-full flex items-center justify-center'>
              <span className='text-black font-bold text-sm'>★</span>
            </div>
            <span className='hidden font-bold sm:inline-block text-[#D4AF37]'>AHOS</span>
          </Link>
          <div className='relative flex flex-1 items-center gap-3'>
            <Search placeholder='جستجو...' />
          </div>
        </div>
        <div className='flex items-center space-x-4'>
          <div className='hidden sm:flex items-center gap-2'>
            <div className='px-3 py-1 bg-[#D4AF37]/10 border border-[#D4AF37]/30 rounded-full text-xs text-[#D4AF37]'>
              PAPER ONLY
            </div>
            <div className='px-3 py-1 bg-[#D4AF37]/10 border border-[#D4AF37]/30 rounded-full text-xs text-[#D4AF37]'>
              System Healthy
            </div>
            <div className='px-3 py-1 bg-[#D4AF37]/10 border border-[#D4AF37]/30 rounded-full text-xs text-[#D4AF37]'>
              Tehran 15:30
            </div>
          </div>
          <div className='flex items-center gap-2'>
            <Bell className='h-4 w-4 text-[#D4AF37]' />
          </div>
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
        {children}
      </div>
    </header>
  )
}