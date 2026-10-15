import { Suspense } from 'react'
import { AuthenticatedLayout } from './components/layout/authenticated-layout'
import { Dashboard } from './components/dashboard'

export default function CommandCenterPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading AHOS Command Center...</p>
        </div>
      </div>
    }>
      <AuthenticatedLayout>
        <Dashboard />
      </AuthenticatedLayout>
    </Suspense>
  )
}