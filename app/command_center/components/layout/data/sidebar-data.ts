import {
  LayoutDashboard,
  ListTodo,
  Package,
  MessagesSquare,
  Users,
  Settings,
  Bell,
  UserCog,
  ShieldCheck,
  HelpCircle,
  Command,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'AHOS Operator',
    email: 'operator@ahos.system',
    avatar: '/ahos-logo.png',
  },
  teams: [
    {
      name: 'AHOS Command Center',
      logo: Command,
      plan: 'Crypto Intelligence Platform',
    },
  ],
  navGroups: [
    {
      title: 'Command Center',
      items: [
        {
          title: 'Overview',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Discovery',
          url: '/discovery',
          icon: Package,
        },
        {
          title: 'Opportunities',
          url: '/opportunities',
          icon: ListTodo,
        },
        {
          title: 'Trades',
          url: '/trades',
          icon: MessagesSquare,
        },
        {
          title: 'Agents',
          url: '/agents',
          icon: Users,
        },
      ],
    },
    {
      title: 'Security',
      items: [
        {
          title: 'Access Control',
          url: '/security',
          icon: ShieldCheck,
        },
        {
          title: 'System Status',
          url: '/status',
          icon: Bell,
        },
      ],
    },
    {
      title: 'Settings',
      items: [
        {
          title: 'Profile',
          url: '/settings',
          icon: UserCog,
        },
        {
          title: 'Preferences',
          url: '/settings/preferences',
          icon: Settings,
        },
        {
          title: 'Help',
          url: '/help',
          icon: HelpCircle,
        },
      ],
    },
  ],
}