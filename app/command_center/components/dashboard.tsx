'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useSnap } from '@/components/ahos/use-command-snapshot'
import { AhosOverview } from '@/app/command_center/components/ahos/overview'

export function Dashboard() {
  const { loading } = useSnap()

  if (loading) {
    return (
      <div className='flex h-full items-center justify-center bg-background'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4AF37] mx-auto' />
          <p className='mt-4 text-muted-foreground'>در حال دریافت داده‌های AHOS...</p>
        </div>
      </div>
    )
  }

  return <AhosOverview />
}
