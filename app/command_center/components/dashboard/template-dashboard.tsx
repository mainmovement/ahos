'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Header } from '../layout/header'
import { TopNav } from '../layout/top-nav'
import { Search } from '../layout/search'
import { ThemeSwitch } from '../layout/theme-switch'
import { ConfigDrawer } from '../layout/config-drawer'
import { ProfileDropdown } from '../layout/profile-dropdown'
import { useSnap } from '@/components/ahos/use-command-snapshot'
import { AhosOverview } from '@/app/command_center/components/ahos/overview'

export function Dashboard() {
  const { data, stale, loading } = useSnap()

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4AF37] mx-auto" />
          <p className="mt-4 text-muted-foreground">در حال دریافت داده‌های AHOS...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <TopNav links={topNav} className='me-auto' />
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      {/* ===== Main Content ===== */}
      <main className="p-6 space-y-6">
        <div className="mb-2 flex items-center justify-between space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">پایانه فرمان AHOS</h1>
          <div className="flex items-center space-x-2">
            <Button>بارگیری گزارش</Button>
          </div>
        </div>

        {/* KPI Cards Row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">کل فرصت‌های تأیید شده</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">142</div>
              <p className="text-xs text-muted-foreground">
                +12% از ماه قبل
              </p>
            </CardContent>
          </Card>

          <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">در حال نظارت</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">89</div>
              <p className="text-xs text-muted-foreground">
                +8% از ماه قبل
              </p>
            </CardContent>
          </Card>

          <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">رد شده</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <rect width="20" height="14" x="2" y="5" rx="2" />
                <path d="M2 10h20" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">53</div>
              <p className="text-xs text-muted-foreground">
                -3% از ماه قبل
              </p>
            </CardContent>
          </Card>

          <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">در حال اجرا</CardTitle>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                className="h-4 w-4 text-muted-foreground"
              >
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">27</div>
              <p className="text-xs text-muted-foreground">
                +15% از ساعت قبل
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="col-span-2">
            <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
              <CardHeader>
                <CardTitle>نمای کلی بازار</CardTitle>
                <CardDescription>
                  تحلیل لحظه‌ای بازارهای جهانی
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AhosOverview />
              </CardContent>
            </Card>
          </div>
          <div className="col-span-1">
            <Card className="bg-[#000]/5 border-[#D4AF37]/40 backdrop-blur">
              <CardHeader>
                <CardTitle>اخبار هوشمند</CardTitle>
                <CardDescription>
                  مهم‌ترین اخبار و تحولات بازار
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm">
                    <p className="font-medium">طلا در بالاترین سطح 2 ماهه</p>
                    <p className="text-muted-foreground mt-1">قیمت طلا به 4200 دلار رسید</p>
                    <p className="text-xs text-muted-foreground mt-2">2 دقیقه پیش</p>
                  </div>
                  <div className="text-sm">
                    <p className="font-medium">تحلیل: بیتکوین در حال اصلاح</p>
                    <p className="text-muted-foreground mt-1">کارشناسان پیش‌بینی اصلاح می‌کنند</p>
                    <p className="text-xs text-muted-foreground mt-2">15 دقیقه پیش</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </>
  )
}

const topNav = [
  {
    title: 'نمای کلی',
    href: '/command_center',
    isActive: true,
    disabled: false,
  },
  {
    title: 'کشف',
    href: '/command_center/discovery',
    isActive: false,
    disabled: false,
  },
  {
    title: 'فرصت‌ها',
    href: '/command_center/opportunities',
    isActive: false,
    disabled: false,
  },
  {
    title: 'تجارت',
    href: '/command_center/trading',
    isActive: false,
    disabled: false,
  },
]