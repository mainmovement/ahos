'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Overview } from './components/overview'
import { RecentSales } from './components/recent-sales'

export function Dashboard() {
  return (
    <div className='p-6 space-y-6'>
      {/* Greeting Section */}
      <div className='mb-6 text-center py-8 bg-gradient-to-br from-[#D4AF37]/10 to-transparent border border-[#D4AF37]/20 rounded-lg'>
        <h1 className='text-3xl font-bold text-[#D4AF37 mb-2'>کنترل مرکزی AHOS</h1>
        <p className='text-lg text-[#D4AF37]/80'>Good evening, Mehrdad</p>
      </div>

      <Tabs defaultValue='overview' className='space-y-4'>
        <div className='w-full overflow-x-auto'>
          <TabsList className='grid w-full grid-cols-4'>
            <TabsTrigger value='overview'>نمای کلی</TabsTrigger>
            <TabsTrigger value='analytics'>تحلیل‌ها</TabsTrigger>
            <TabsTrigger value='reports' disabled>گزارش‌ها</TabsTrigger>
            <TabsTrigger value='notifications' disabled>اعلانات</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value='overview' className='space-y-6'>
          {/* KPI Cards */}
          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>تأیید شده</CardTitle>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth='2'
                  className='h-4 w-4 text-[#D4AF37]/60'
                >
                  <path d='M22 11.08V12a10 10 0 1 1-5.93-9.14' />
                  <polyline points='22 4 12 14.01 9 11.01' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>24</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +8.1% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>در نظارت</CardTitle>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth='2'
                  className='h-4 w-4 text-[#D4AF37]/60'
                >
                  <circle cx='12' cy='12' r='10' />
                  <path d='M12 6v6l4 2' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>12</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +3.2% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>مجموع</CardTitle>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth='2'
                  className='h-4 w-4 text-[#D4AF37]/60'
                >
                  <rect width='20' height='14' x='2' y='5' rx='2' />
                  <path d='M2 10h20' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>178</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +12% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>رد شده</CardTitle>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='currentColor'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth='2'
                  className='h-4 w-4 text-[#D4AF37]/60'
                >
                  <circle cx='12' cy='12' r='10' />
                  <line x1='4.93' y1='4.93' x2='19.07' y2='19.07' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>8</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  -2.1% از ماه قبل
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Area */}
          <div className='grid grid-cols-1 gap-6 lg:grid-cols-12'>
            {/* Center Area - Globe and Charts */}
            <div className='col-span-1 lg:col-span-8 space-y-6'>
              {/* Globe Section (Placeholder) */}
              <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 h-[400px] flex items-center justify-center'>
                <div className='text-center'>
                  <div className='w-48 h-48 mx-auto mb-4 rounded-full bg-gradient-to-br from-[#D4AF37]/20 to-transparent border-2 border-[#D4AF37]/30 flex items-center justify-center'>
                    <div className='text-4xl text-[#D4AF37]'>🌐</div>
                  </div>
                  <h3 className='text-xl font-bold text-[#D4AF37]'>هولوگرافیک گلوب</h3>
                  <p className='text-sm text-[#D4AF37]/60 mt-2'>فرصت‌ها در نقشه جهانی</p>
                </div>
              </Card>

              {/* Market Overview */}
              <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>نمای کلی بازار</CardTitle>
                </CardHeader>
                <CardContent className='ps-2'>
                  <Overview />
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Live Intelligence Feed + Quick Actions */}
            <div className='col-span-1 lg:col-span-4 space-y-6'>
              {/* Live Intelligence Feed */}
              <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 h-[300px]'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>خبر هوشمند</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='space-y-3'>
                    <div className='p-3 bg-[#D4AF37]/5 border border-[#D4AF37]/20 rounded'>
                      <p className='text-sm text-[#D4AF37]'>BTC突破 $35,000</p>
                      <p className='text-xs text-[#D4AF37]/60 mt-1'>2 دقیقه پیش</p>
                    </div>
                    <div className='p-3 bg-[#D4AF37]/5 border border-[#D4AF37]/20 rounded'>
                      <p className='text-sm text-[#D4AF37]'>ETH نشانه‌های صعود</p>
                      <p className='text-xs text-[#D4AF37]/60 mt-1'>5 دقیقه پیش</p>
                    </div>
                    <div className='p-3 bg-[#D4AF37]/5 border border-[#D4AF37]/20 rounded'>
                      <p className='text-sm text-[#D4AF37]">گلد مسترث在新高点</p>
                      <p className='text-xs text-[#D4AF37]/60 mt-1'>8 دقیقه پیش</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>اقدامات سریع</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='grid grid-cols-2 gap-3'>
                    <button className='p-3 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 rounded-lg text-sm text-[#D4AF37] transition-all'>
                      اسکن بازار
                    </button>
                    <button className='p-3 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 rounded-lg text-sm text-[#D4AF37] transition-all'>
                      تحلیل
                    </button>
                    <button className='p-3 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 rounded-lg text-sm text-[#D4AF37] transition-all'>
                      گزارش
                    </button>
                    <button className='p-3 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 rounded-lg text-sm text-[#D4AF37] transition-all'>
                      تنظیمات
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Bottom Row */}
          <div className='grid grid-cols-1 gap-6 lg:grid-cols-4'>
            {/* University */}
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>دانشگاه AHOS</CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-center py-4'>
                  <div className='text-2xl mb-2'>🎓</div>
                  <p className='text-sm text-[#D4AF37]/60'>آموزش و تحقیق</p>
                </div>
              </CardContent>
            </Card>

            {/* Agent Society */}
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>جمعیت عامل</CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-center py-4'>
                  <div className='text-2xl mb-2'>👥</div>
                  <p className='text-sm text-[#D4AF37]/60'>تیم‌های هوش مصنوعی</p>
                </div>
              </CardContent>
            </Card>

            {/* Auto Trading */}
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>معامله خودکار</CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-center py-4'>
                  <div className='text-2xl mb-2'>🤖</div>
                  <p className='text-sm text-[#D4AF37]/60'>عملکرد ربات</p>
                </div>
              </CardContent>
            </Card>

            {/* Chat */}
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>چت با AHOS</CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-center py-4'>
                  <div className='text-2xl mb-2'>💬</div>
                  <p className='text-sm text-[#D4AF37]/60'>هوش مصنوعی</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value='analytics' className='space-y-4'>
          <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 p-6'>
            <div className='h-[400px] flex items-center justify-center text-[#D4AF37]/50'>
              <p>نمودار تحلیل‌ها</p>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}