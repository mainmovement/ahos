import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Search } from 'lucide-react'
import { useSearch } from '@/app/command_center/components/context/search-provider'

export function CommandMenu() {
  const { setIsOpen } = useSearch()
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        variant='ghost'
        className='relative h-8 w-8 p-0'
        onClick={() => setOpen(true)}
      >
        <Search className='h-4 w-4' />
        <span className='sr-only'>جستجو</span>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <Command>
          <CommandInput placeholder='جستجوی دستورات...' />
          <CommandList>
            <CommandEmpty>هیچ چیزی پیدا نشد</CommandEmpty>
            <CommandGroup heading='دستورات'>
              <CommandItem onSelect={() => setIsOpen(true)}>
                جستجوی جهانی
              </CommandItem>
              <CommandItem>تنظیمات</CommandItem>
              <CommandItem>پشتیبانی</CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </CommandDialog>
    </>
  )
}