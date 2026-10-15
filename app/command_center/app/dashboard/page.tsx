import { AuthenticatedLayout } from '@/components/layout/authenticated-layout'
import { Dashboard } from '@/components/dashboard'

export default function DashboardPage() {
  return (
    <AuthenticatedLayout headerProps={{
      links: [
        { title: 'Overview', href: '/dashboard', isActive: true, disabled: false },
        { title: 'Signals', href: '/signals', isActive: false, disabled: false },
        { title: 'Markets', href: '/markets', isActive: false, disabled: false },
        { title: 'Security', href: '/security', isActive: false, disabled: false },
      ]
    }}>
      <Dashboard />
    </AuthenticatedLayout>
  )
}