import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { TopNav } from '@/components/layout/top-nav'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ConfigDrawer } from '@/components/config-drawer'
import { Overview } from './components/overview'
import { Analytics } from './components/analytics'
import { RecentSales } from './components/recent-sales'

export function Dashboard() {
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

      {/* ===== Main ===== */}
      <Main>
        <div className='mb-2 flex items-center justify-between space-y-2'>
          <h1 className='text-2xl font-bold tracking-tight'>فرماندهی AHOS</h1>
          <div className='flex items-center space-x-2'>
            <Button>دانلود گزارش</Button>
          </div>
        </div>

        {/* Status Pills Row */}
        <div className='flex flex-wrap gap-2 mb-6'>
          <div className='inline-flex items-center rounded-full bg-green-500/20 px-3 py-1 text-xs font-medium text-green-400 border border-green-400/30'>
            <div className='w-2 h-2 bg-green-400 rounded-full mr-2' />
            کاغذی فقط
          </div>
          <div className='inline-flex items-center rounded-full bg-blue-500/20 px-3 py-1 text-xs font-medium text-blue-400 border border-blue-400/30'>
            <div className='w-2 h-2 bg-blue-400 rounded-full mr-2' />
            سلامت سیستم: عالی
          </div>
          <div className='inline-flex items-center rounded-full bg-yellow-500/20 px-3 py-1 text-xs font-medium text-yellow-400 border border-yellow-400/30'>
            <div className='w-2 h-2 bg-yellow-400 rounded-full mr-2' />
            تازگی شواهد: 5 دقیقه
          </div>
          <div className='inline-flex items-center rounded-full bg-purple-500/20 px-3 py-1 text-xs font-medium text-purple-400 border border-purple-400/30'>
            <div className='w-2 h-2 bg-purple-400 rounded-full mr-2' />
            uptime: 99.9%
          </div>
          <div className='inline-flex items-center rounded-full bg-orange-500/20 px-3 py-1 text-xs font-medium text-orange-400 border border-orange-400/30'>
            <div className='w-2 h-2 bg-orange-400 rounded-full mr-2' />
            تهران ۱۸:۴۵
          </div>
        </div>

        <Tabs
          orientation='vertical'
          defaultValue='overview'
          className='space-y-4'
        >
          <div className='w-full overflow-x-auto pb-2'>
            <TabsList>
              <TabsTrigger value='overview'>نمای کلی</TabsTrigger>
              <TabsTrigger value='analytics'>تحلیل‌ها</TabsTrigger>
              <TabsTrigger value='reports' disabled>
                گزارش‌ها
              </TabsTrigger>
              <TabsTrigger value='notifications' disabled>
                اعلان‌ها
              </TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value='overview' className='space-y-4'>
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <Card className="bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm">
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-yellow-400/80'>
                    امتیاز امنیتی
                  </CardTitle>
                  <svg
                    xmlns='http://www.w3.org/2000/svg'
                    viewBox='0 0 24 24'
                    fill='none'
                    stroke='currentColor'
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth='2'
                    className='h-4 w-4 text-yellow-400/60'
                  >
                    <path d='M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold text-yellow-400'>98.5%</div>
                  <p className='text-xs text-yellow-400/60'>
                    +2.1% از آخرین ممیزی
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm">
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-yellow-400/80'>
                    عاملان فعال
                  </CardTitle>
                  <svg
                    xmlns='http://www.w3.org/2000/svg'
                    viewBox='0 0 24 24'
                    fill='none'
                    stroke='currentColor'
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth='2'
                    className='h-4 w-4 text-yellow-400/60'
                  >
                    <circle cx='12' cy='12' r='10' />
                    <path d='M12 6v6l4 2' />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold text-yellow-400'>12</div>
                  <p className='text-xs text-yellow-400/60'>
                    +3 این هفته
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm">
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-yellow-400/80'>
                    فرصت‌ها
                  </CardTitle>
                  <svg
                    xmlns='http://www.w3.org/2000/svg'
                    viewBox='0 0 24 24'
                    fill='none'
                    stroke='currentColor'
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth='2'
                    className='h-4 w-4 text-yellow-400/60'
                  >
                    <path d='M22 12h-4l-3 9L9 3l-3 9H2' />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold text-yellow-400'>247</div>
                  <p className='text-xs text-yellow-400/60'>
                    +18 امروز
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm">
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-yellow-400/80'>
                    معاملات کاغذی
                  </CardTitle>
                  <svg
                    xmlns='http://www.w3.org/2000/svg'
                    viewBox='0 0 24 24'
                    fill='none'
                    stroke='currentColor'
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth='2'
                    className='h-4 w-4 text-yellow-400/60'
                  >
                    <path d='M3 3v18h18' />
                    <path d='M18.7 8l-5.1 5.2-2.8-2.7L7 14.3' />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold text-yellow-400'>+47.3%</div>
                  <p className='text-xs text-yellow-400/60'>
                    عملکرد سالانه
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
              <Card className='col-span-1 lg:col-span-4 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>نمای کلی بازار</CardTitle>
                </CardHeader>
                <CardContent className='ps-2'>
                  <Overview />
                </CardContent>
              </Card>
              <Card className='col-span-1 lg:col-span-3 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>فعالیت اخیر</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    آخرین اجراهای عامل
                  </CardDescription>
                <CardContent>
                  <RecentSales />
                </CardContent>
              </Card>
            </div>

            {/* Right Column */}
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-3'>
              <Card className='col-span-1 lg:col-span-2 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>Feed زنده هوش</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    آخرین سیگنال‌ها و فرصت‌ها
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-3'>
                    <div className='flex items-start space-x-3 p-3 rounded-lg bg-yellow-400/5 border border-yellow-400/10'>
                      <div className='w-2 h-2 bg-yellow-400 rounded-full mt-1.5' />
                      <div>
                        <p className='text-sm font-medium text-yellow-400/80'>فرصت خرید XAU/USD</p>
                        <p className='text-xs text-yellow-400/60'>سطح مقاومت: 2150.00 • سیگنال: 93%</p>
                        <p className='text-xs text-yellow-400/40 mt-1'>2 دقیقه پیش</p>
                      </div>
                    </div>
                    <div className='flex items-start space-x-3 p-3 rounded-lg bg-green-400/5 border border-green-400/10'>
                      <div className='w-2 h-2 bg-green-400 rounded-full mt-1.5' />
                      <div>
                        <p className='text-sm font-medium text-green-400/80'>اعلامیه امنیتی</p>
                        <p className='text-xs text-green-400/60'>سیستم عامل عاملان پایدار است</p>
                        <p className='text-xs text-green-400/40 mt-1'>15 دقیقه پیش</p>
                      </div>
                    </div>
                    <div className='flex items-start space-x-3 p-3 rounded-lg bg-blue-400/5 border border-blue-400/10'>
                      <div className='w-2 h-2 bg-blue-400 rounded-full mt-1.5' />
                      <div>
                        <p className='text-sm font-medium text-blue-400/80'>به‌روزرسانی داده</p>
                        <p className='text-xs text-blue-400/60'>داده‌های بازار با موفقیت بارگذاری شد</p>
                        <p className='text-xs text-blue-400/40 mt-1'>1 ساعت پیش</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className='col-span-1 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>اقدامات سریع</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    دسترسی سریع به وظایف
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-2'>
                    <Button variant='outline' className='w-full justify-start bg-yellow-400/5 border-yellow-400/30 text-yellow-400/80 hover:bg-yellow-400/10'>
                      <svg className='mr-2 h-4 w-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                      </svg>
                      اسکن بازار
                    </Button>
                    <Button variant='outline' className='w-full justify-start bg-yellow-400/5 border-yellow-400/30 text-yellow-400/80 hover:bg-yellow-400/10'>
                      <svg className='mr-2 h-4 w-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                      </svg>
                      گزارش عملکرد
                    </Button>
                    <Button variant='outline' className='w-full justify-start bg-yellow-400/5 border-yellow-400/30 text-yellow-400/80 hover:bg-yellow-400/10'>
                      <svg className='mr-2 h-4 w-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                      </svg>
                      مدیریت عاملان
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Bottom Row */}
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-4'>
              <Card className='col-span-1 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>دانشگاه AHOS</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    مرکز تحقیقات و آموزش
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='text-center py-8'>
                    <div className='text-4xl mb-2'>🎓</div>
                    <p className='text-sm text-yellow-400/80'>12 دوره فعال</p>
                    <p className='text-xs text-yellow-400/60 mt-1'>256 دانشجو</p>
                  </div>
                </CardContent>
              </Card>

              <Card className='col-span-1 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>انجمن عاملان</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    شبکه همکاری
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='text-center py-8'>
                    <div className='text-4xl mb-2'>👥</div>
                    <p className='text-sm text-yellow-400/80'>8 تیم فعال</p>
                    <p className='text-xs text-yellow-400/60 mt-1'>47 عامل</p>
                  </div>
                </CardContent>
              </Card>

              <Card className='col-span-2 bg-gradient-to-br from-yellow-400/5 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
                <CardHeader>
                  <CardTitle className='text-yellow-400/80'>عملکرد معاملات خودکار</CardTitle>
                  <CardDescription className='text-yellow-400/60'>
                    روندهای عملکرد 30 روزه
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='h-32 flex items-center justify-center'>
                    <p className='text-yellow-400/60 text-sm'>نمودار عملیات در حال بارگذاری...</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value='analytics' className='space-y-4'>
            <Analytics />
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}

const topNav = [
  {
    title: 'نمای کلی',
    href: '/dashboard',
    isActive: true,
    disabled: false,
  },
  {
    title: 'مشتریان',
    href: '/dashboard/customers',
    isActive: false,
    disabled: true,
  },
  {
    title: 'محصولات',
    href: '/dashboard/products',
    isActive: false,
    disabled: true,
  },
  {
    title: 'تنظیمات',
    href: '/dashboard/settings',
    isActive: false,
    disabled: true,
  },
]