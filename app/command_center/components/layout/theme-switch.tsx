'use client'

import { useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function ThemeSwitch() {
  const [isDark, setIsDark] = useState(true)

  const toggleTheme = () => {
    setIsDark(!isDark)
    // In a real implementation, you would update a theme context or class on body
    document.documentElement.classList.toggle('dark', !isDark)
  }

  return (
    <Button
      size='icon'
      variant='ghost'
      onClick={toggleTheme}
      className='text-[#D4AF37]'
    >
      {isDark ? (
        <Sun className='h-4 w-4' />
      ) : (
        <Moon className='h-4 w-4' />
      )}
      <span className='sr-only'>Toggle theme</span>
    </Button>
  )
}