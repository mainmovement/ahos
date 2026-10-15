import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from './app-sidebar'
import { LayoutProvider } from '@/app/command_center/components/context/layout-provider'
import { SearchProvider } from '@/app/command_center/components/context/search-provider'
import { getCookie } from '@/app/command_center/components/lib/cookies'
import { SkipToMain } from '@/app/command_center/components/skip-to-main'
import { Header } from './header'
import { HeaderProps } from './types'

type AuthenticatedLayoutProps = {
  children?: ReactNode
  headerProps?: HeaderProps
}

export function AuthenticatedLayout({ children, headerProps }: AuthenticatedLayoutProps) {
  const defaultOpen = getCookie('sidebar_state') !== 'false'
  return (
    <SearchProvider>
      <LayoutProvider>
        <SidebarProvider defaultOpen={defaultOpen}>
          <SkipToMain />
          <AppSidebar />
          <SidebarInset
            className={cn(
              // Set content container, so we can use container queries
              '@container/content',

              // If layout is fixed, set the height
              // to 100svh to prevent overflow
              'has-data-[layout=fixed]:h-svh',

              // If layout is fixed and sidebar is inset,
              // set the height to 100svh - spacing (total margins) to prevent overflow
              'peer-data-[variant=inset]:has-data-[layout=fixed]:h-[calc(100svh-(var(--spacing)*4))]'
            )}
          >
            <Header {...headerProps} />
            {children}
          </SidebarInset>
        </SidebarProvider>
      </LayoutProvider>
    </SearchProvider>
  )
}