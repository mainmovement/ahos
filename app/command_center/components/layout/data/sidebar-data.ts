import {
  LayoutDashboard,
  ShieldCheck,
  Brain,
  Globe,
  Database,
  Lock,
  Settings,
  Users,
  MessagesSquare,
  FileText,
  Activity,
  Terminal,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Mehrdad',
    email: 'mehrdad@ahos.ai',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [
    {
      name: 'AHOS Command',
      logo: ShieldCheck,
      plan: 'PAPER ONLY',
    },
    {
      name: 'Lane B Engine',
      logo: Brain,
      plan: 'Deterministic',
    },
  ],
  navGroups: [
    {
      title: 'Command & Intelligence',
      items: [
        {
          title: 'Command Center',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Holographic Globe',
          url: '/globe',
          icon: Globe,
        },
        {
          title: 'Opportunities',
          url: '/opportunities',
          icon: Activity,
        },
        {
          title: 'Market Intelligence',
          url: '/market',
          icon: Database,
        },
        {
          title: 'Auto Trading (Agents)',
          url: '/agents',
          icon: Terminal,
        },
      ],
    },
    {
      title: 'Governance & Security',
      items: [
        {
          title: 'Identity & Security',
          icon: Lock,
          items: [
            { title: 'Gate Authority', url: '/security/gate' },
            { title: 'Lane A Freeze', url: '/security/lane-a' },
          ],
        },
        {
          title: 'Audit & Governance',
          url: '/audit',
          icon: FileText,
        },
        {
          title: 'Evidence Ledger',
          url: '/evidence',
          icon: Database,
        },
      ],
    },
    {
      title: 'Labs & Community',
      items: [
        {
          title: 'AHOS University / Lab',
          url: '/university',
          icon: Brain,
        },
        {
          title: 'Agent Society',
          url: '/society',
          icon: Users,
        },
        {
          title: 'Chat with AHOS',
          url: '/chat',
          icon: MessagesSquare,
        },
        {
          title: 'Settings',
          url: '/settings',
          icon: Settings,
        },
      ],
    },
  ],
}
