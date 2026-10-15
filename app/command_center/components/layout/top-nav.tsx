'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Menu } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type TopNavProps = React.HTMLAttributes<HTMLElement> & {
  links?: {
    title: string
    href: string
    isActive: boolean
    disabled?: boolean
  }[]
}

export function TopNav({ className, links = [], ...props }: TopNavProps) {
  const pathname = usePathname()

  return (
    <>
      <div className='md:hidden'>
        <DropdownMenu modal={false}>
          <DropdownMenuTrigger asChild>
            <Button
              size='icon'
              variant='outline'
              aria-label='Open navigation menu'
            >
              <Menu />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side='bottom' align='start' className='w-48'>
            {links.map(({ title, href, disabled }) => (
              <DropdownMenuItem key={`${title}-${href}`} asChild>
                <Link
                  href={disabled ? '#' : href}
                  aria-disabled={disabled}
                  className={cn(
                    'w-full',
                    disabled && 'pointer-events-none opacity-50'
                  )}
                >
                  {title}
                </Link>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <nav
        className={cn(
          'hidden items-center space-x-4 md:flex lg:space-x-6',
          className
        )}
        {...props}
      >
        {links.map(({ title, href, disabled }) => (
          <Link
            key={`${title}-${href}`}
            href={disabled ? '#' : href}
            aria-disabled={disabled}
            className={cn(
              'text-sm font-medium transition-colors hover:text-primary',
              pathname === href || (href !== '/' && pathname.startsWith(href))
                ? 'text-foreground'
                : 'text-muted-foreground',
              disabled && 'pointer-events-none opacity-50'
            )}
          >
            {title}
          </Link>
        ))}
      </nav>
    </>
  )
}