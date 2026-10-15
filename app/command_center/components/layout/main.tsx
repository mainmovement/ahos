import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type MainProps = {
  fixed?: boolean
  children: ReactNode
  className?: string
}

export function Main({ fixed, children, className }: MainProps) {
  return (
    <main
      id='main-content'
      data-layout={fixed ? 'fixed' : 'auto'}
      className={cn(
        'peer-[[data-layout-fixed]]/header:overflow-auto px-4 py-6',
        'peer-[[data-layout-fixed]]/header:h-[calc(100svh-var(--header-height))]',
        fixed && 'flex flex-col flex-grow overflow-hidden',
        !fixed && 'flex-1',
        '@container/content:px-4 py-6',
        '@7xl/content:mx-auto @7xl/content:w-full @7xl/content:max-w-7xl',
        className
      )}
    >
      {children}
    </main>
  )
}