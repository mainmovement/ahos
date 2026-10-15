'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Overview } from './overview'
import { RecentSales } from './recent-sales'

export function Dashboard() {
  return (
    <div className='p-6 space-y-6'>
      <div className='mb-2 flex items-center justify-between space-y-2'>
        <h1 className='text-2xl font-bold tracking-tight'>کنترل مرکزی AHOS</h1>
        <div className='flex items-center space-x-2'>
          <button className='px-4 py-2 bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 text-[#D4AF37] rounded-md transition-all border border-[#D4AF37]/30'>
            دانلود گزارش
          </button>
        </div>
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

        <TabsContent value='overview' className='space-y-4'>
          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>درآمد کل</CardTitle>
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
                  <path d='M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>$45,231.89</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +20.1% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>مشترکین</CardTitle>
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
                  <path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2' />
                  <circle cx='9' cy='7' r='4' />
                  <path d='M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>+2350</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +180.1% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>فروش‌ها</CardTitle>
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
                <div className='text-2xl font-bold text-[#D4AF37]'>+12,234</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +19% از ماه قبل
                </p>
              </CardContent>
            </Card>

            <Card className='backdrop-blur bg-black/50 border-[#D4AF37]/30 hover:border-[#D4AF37]/60 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-[#D4AF37]'>فعال در لحظه</CardTitle>
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
                  <path d='M22 12h-4l-3 9L9 3l-3 9H2' />
                </svg>
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-[#D4AF37]'>+573</div>
                <p className='text-xs text-[#D4AF37]/60'>
                  +201 از ساعت قبل
                </p>
              </CardContent>
            </Card>
          </div>

          <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
            <Card className='col-span-1 lg:col-span-4 backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>نمای کلی بازار</CardTitle>
              </CardHeader>
              <CardContent className='ps-2'>
                <Overview />
              </CardContent>
            </Card>

            <Card className='col-span-1 lg:col-span-3 backdrop-blur bg-black/50 border-[#D4AF37]/30'>
              <CardHeader>
                <CardTitle className='text-[#D4AF37]'>فروش‌های اخیر</CardTitle>
                <CardDescription>
                  در این ماه 265 فروش انجام شده است.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RecentSales />
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