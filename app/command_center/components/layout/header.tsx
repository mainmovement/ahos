'use client'

import { useState, useEffect } from 'react'
import { Link } from 'next/link'
import { cn } from '@/lib/utils'
import { Button } from '../ui/button'
import { Separator } from '../ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '../ui/badge'
import { Search, Bell, Settings, Menu, Globe } from 'lucide-react'

export function Header() {
  const [offset, setOffset] = useState(0)
  const [currentTime, setCurrentTime] = useState('')

  useEffect(() => {
    const onScroll = () => {
      setOffset(document.body.scrollTop || document.documentElement.scrollTop)
    }

    // Update time every minute
    const updateTehranTime = () => {
      const now = new Date()
      const tehranTime = now.toLocaleString('fa-IR', {
        timeZone: 'Asia/Tehran',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })
      setCurrentTime(tehranTime)
    }

    document.addEventListener('scroll', onScroll, { passive: true })
    updateTehranTime()
    const timer = setInterval(updateTehranTime, 60000)

    return () => {
      document.removeEventListener('scroll', onScroll)
      clearInterval(timer)
    }
  }, [])

  return (
    <header
      className={cn(
        'z-50 h-16',
        'sticky top-0 w-full',
        offset > 10 && 'shadow-lg shadow-gold/20'
      )}
    >
      <div className="relative flex h-full items-center justify-between px-4 sm:px-6">
        {/* Left side */}
        <div className="flex items-center gap-3">
          <SidebarTrigger variant="outline" className="max-md:scale-125" />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-gold-400" />
            <h1 className="text-lg font-bold text-amber-100">AHOS</h1>
          </div>
        </div>

        {/* Center - Search */}
        <div className="flex-1 max-w-md mx-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-amber-200/60" />
            <input
              type="search"
              placeholder="جستجو در سیستم..."
              className="w-full rounded-md border border-amber-200/20 bg-amber-500/5 px-10 py-2 text-amber-100 placeholder:text-amber-200/60 focus:border-amber-400/40 focus:outline-none focus:ring-2 focus:ring-amber-400/20"
            />
          </div>
        </div>

        {/* Right side - Status and user */}
        <div className="flex items-center gap-3">
          {/* Status chips */}
          <div className="hidden sm:flex items-center gap-2">
            <Badge variant="secondary" className="bg-green-500/20 text-green-300 border-green-500/30">
              تمام سیستم‌ها فعال
            </Badge>
            <Badge variant="secondary" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              آماده به کار
            </Badge>
          </div>

          {/* Clock */}
          <div className="text-sm font-medium text-amber-100">
            {currentTime}
          </div>

          {/* Notifications */}
          <Button
            size="icon"
            variant="ghost"
            className="h-9 w-9 text-amber-200/60 hover:text-amber-100 hover:bg-amber-500/10"
          >
            <Bell className="h-4 w-4" />
            <span className="sr-only">اعلان‌ها</span>
          </Button>

          {/* Settings */}
          <Button
            size="icon"
            variant="ghost"
            className="h-9 w-9 text-amber-200/60 hover:text-amber-100 hover:bg-amber-500/10"
          >
            <Settings className="h-4 w-4" />
            <span className="sr-only">تنظیمات</span>
          </Button>

          {/* User avatar */}
          <Avatar className="h-8 w-8 border border-amber-400/20">
            <AvatarImage src="/avatars/mehrdad.jpg" alt="مهراد" />
            <AvatarFallback className="text-amber-300">م</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}