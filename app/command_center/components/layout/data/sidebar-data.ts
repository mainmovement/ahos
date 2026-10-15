import {
  LayoutDashboard,
  Search,
  BarChart3,
  Lightbulb,
  Zap,
  GraduationCap,
  Shield,
  FileText,
  Exchange,
  Users,
  MessageSquare,
  Settings,
  Bell,
  HelpCircle,
  Globe,
  Server,
  TrendingUp,
  Target,
  Bot,
  BookOpen,
  ShieldCheck,
  UserCog,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Mehrdad',
    email: 'mehrdad@ahos.system',
    avatar: '/avatars/mehrdad.jpg',
  },
  teams: [
    {
      name: 'AHOS Command Center',
      logo: LayoutDashboard,
      plan: 'Crypto Intelligence Platform',
    },
  ],
  navGroups: [
    {
      title: 'General',
      items: [
        {
          title: 'Command Center',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Discovery',
          url: '/discovery',
          icon: Search,
        },
        {
          title: 'Opportunities',
          url: '/opportunities',
          icon: Target,
        },
        {
          title: 'Market Intelligence',
          url: '/intelligence',
          icon: BarChart3,
        },
        {
          title: 'Auto Trading',
          url: '/trading',
          icon: Zap,
        },
        {
          title: 'AHOS University',
          url: '/university',
          icon: GraduationCap,
        },
        {
          title: 'Identity & Security',
          url: '/security',
          icon: Shield,
        },
        {
          title: 'Evidence',
          url: '/evidence',
          icon: FileText,
        },
        {
          title: 'Paper Trading',
          url: '/paper',
          icon: Exchange,
        },
        {
          title: 'Learning',
          url: '/learning',
          icon: BookOpen,
        },
        {
          title: 'Agents',
          url: '/agents',
          icon: Bot,
        },
        {
          title: 'Chat with AHOS',
          url: '/chat',
          icon: MessageSquare,
        },
        {
          title: 'Audit & Governance',
          url: '/audit',
          icon: Globe,
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