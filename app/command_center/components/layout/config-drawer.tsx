import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

export function ConfigDrawer() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          size='icon'
          variant='ghost'
          aria-label='Open theme settings'
          className='rounded-full'
        >
          <Settings aria-hidden='true' />
        </Button>
      </SheetTrigger>
      <SheetContent className='flex flex-col'>
        <SheetHeader className='pb-0 text-start'>
          <SheetTitle>Configuration</SheetTitle>
          <SheetDescription>
            Customize the AHOS Command Center interface.
          </SheetDescription>
        </SheetHeader>
        <div className='space-y-6 overflow-y-auto px-4 py-6'>
          <div className='space-y-4'>
            <h3 className='text-sm font-semibold text-muted-foreground'>Theme</h3>
            <div className='grid grid-cols-3 gap-4'>
              <div className='relative rounded-md border bg-background p-4'>
                <div className='text-xs font-medium text-muted-foreground'>Light</div>
                <div className='mt-2 h-16 rounded bg-gradient-to-br from-gray-50 to-gray-100' />
              </div>
              <div className='relative rounded-md border bg-background p-4'>
                <div className='text-xs font-medium text-muted-foreground'>Dark</div>
                <div className='mt-2 h-16 rounded bg-gradient-to-br from-gray-900 to-gray-800' />
              </div>
              <div className='relative rounded-md border bg-background p-4'>
                <div className='text-xs font-medium text-muted-foreground'>System</div>
                <div className='mt-2 h-16 rounded bg-gradient-to-br from-gray-200 to-gray-300' />
              </div>
            </div>
          </div>

          <div className='space-y-4'>
            <h3 className='text-sm font-semibold text-muted-foreground'>Layout</h3>
            <div className='space-y-2 text-sm'>
              <div className='flex items-center justify-between'>
                <span>Sidebar Style</span>
                <span className='text-muted-foreground'>Inset</span>
              </div>
              <div className='flex items-center justify-between'>
                <span>Collapsible</span>
                <span className='text-muted-foreground'>Icon</span>
              </div>
            </div>
          </div>

          <div className='space-y-4'>
            <h3 className='text-sm font-semibold text-muted-foreground'>Language</h3>
            <div className='space-y-2 text-sm'>
              <div className='flex items-center justify-between'>
                <span>Direction</span>
                <span className='text-muted-foreground'>LTR</span>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}