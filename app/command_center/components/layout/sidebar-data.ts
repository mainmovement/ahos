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
  Search,
} from 'lucide-react'
import { type SidebarData } from './types'

export const sidebarData: SidebarData = {
  user: {
    name: 'مهراد',
    email: 'mehrdad@ahos.network',
    avatar: '/avatars/mehrdad.jpg',
  },
  teams: [
    {
      name: 'AHOS',
      logo: LayoutDashboard,
      plan: 'Production',
    },
  ],
  navGroups: [
    {
      title: 'دسترسی‌ها',
      items: [
        { title: 'مرکز فرماندهی', url: '/', icon: LayoutDashboard },
        { title: 'کاوش (Discovery)', url: '/discovery', icon: Search },
        { title: 'فرصت‌ها', url: '/opportunities', icon: Activity },
        { title: 'اطلاعات بازار', url: '/market-intelligence', icon: Database },
        { title: 'معاملات خودکار', url: '/autopilot', icon: Terminal },
        { title: 'آموزش و پژوهش', url: '/university', icon: Brain },
        { title: 'هویت و امنیت', url: '/security', icon: Lock },
        { title: 'شواهد', url: '/evidence', icon: FileText },
        { title: 'شخصی‌سازی', url: '/learning', icon: Brain },
      ],
    },
    {
      title: 'ابزارها',
      items: [
        { title: 'چت با AHOS', url: '/chat', icon: MessagesSquare, badge: '3' },
        { title: 'مدیریت مأموریت‌ها', url: '/missions', icon: Activity },
        { title: 'حساب‌ها', url: '/accounts' },
        { title: 'گزارش‌ها', url: '/reports' },
        { title: 'تنظیمات', url: '/settings', icon: Settings },
      ],
    },
  ],
}
