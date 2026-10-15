import { Suspense } from 'react';
import { AuthenticatedLayout } from './components/layout/authenticated-layout';
import { Dashboard } from './components/dashboard';

export const dynamic = 'force-dynamic';

/**
 * The main screen: the AHOS command center (MASTER_SPEC "Layout to match").
 * Using shadcn-admin template with AHOS branding and styling.
 */
export default function HomePage() {
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
  );
}
