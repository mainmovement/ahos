'use client'

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/components/ui/sidebar'
import { NavGroup } from './nav-group'
import { NavUser } from './nav-user'
import { sidebarData } from './data/sidebar-data'

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader>
        {/* Placeholder for future logo */}
        <div className="px-2 py-4 text-center">
          <div className="text-lg font-bold text-white">AHOS</div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {sidebarData.navGroups.map((props) => (
          <NavGroup key={props.title} {...props} />
        ))}
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={sidebarData.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
