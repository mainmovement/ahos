'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ArrowLeftToLine, Shield } from 'lucide-react'
import { useLayout } from '@/app/command_center/components/context/layout-provider'

export function SignOutDialog() {
  const [open, setOpen] = useState(false)
  const { resetLayout } = useLayout()

  const handleSignOut = () => {
    setOpen(false)
    resetLayout()
  }

  return (
    <>
      <Button variant='ghost' onClick={() => setOpen(true)}>
        <ArrowLeftToLine className='h-4 w-4' />
        <span className='sr-only'>خروج</span>
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className='flex items-center gap-2 text-amber-100'>
              <Shield className='h-5 w-5' />
              تأیید خروج
            </DialogTitle>
          </DialogHeader>
          <div className='space-y-4'>
            <p className='text-amber-200/60'>
              آیا از خروج از حساب کاربری مطمئن هستید؟
            </p>
            <div className='flex gap-2'>
              <Button variant='outline' onClick={() => setOpen(false)}>
                انصراف
              </Button>
              <Button variant='destructive' onClick={handleSignOut}>
                خروج
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}