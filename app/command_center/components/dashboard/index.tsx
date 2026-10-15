import { Suspense } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { SearchBar } from '../layout/search-bar'
import { AppSidebar } from '../layout/app-sidebar'
import { SkipToMain } from '../skip-to-main'

function RecentSales() {
  const sales = [
    { customer: 'Ali', email: 'ali@example.com', amount: '$150.00' },
    { customer: 'Sara', email: 'sara@example.com', amount: '$230.00' },
    { customer: 'Reza', email: 'reza@example.com', amount: '$180.00' },
  ]

  return (
    <div className='space-y-8'>
      <div>
        <h2 className='text-2xl font-bold text-amber-100'>فروش‌های اخیر</h2>
        <p className='text-amber-200/60'>مشتریان جدید و فروش‌های اخیر</p>
      </div>
      <div className='space-y-4'>
        {sales.map((sale, i) => (
          <div
            key={i}
            className='flex items-center justify-between border-b border-amber-200/20 pb-4'
          >
            <div className='flex items-center space-x-4'>
              <div className='h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center'>
                <span className='text-sm font-medium text-amber-300'>
                  {sale.customer.charAt(0)}
                </span>
              </div>
              <div>
                <p className='font-medium text-amber-100'>{sale.customer}</p>
                <p className='text-sm text-amber-200/60'>{sale.email}</p>
              </div>
            </div>
            <p className='font-medium text-amber-100'>{sale.amount}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function DashboardContent() {
  return (
    <div className='flex h-full flex-col'>
      <div className='flex h-16 shrink-0 items-center gap-2 border-b border-amber-200/20 px-4'>
        <Suspense>
          <SearchBar />
        </Suspense>
      </div>
      <div className='flex-1 overflow-y-auto p-4'>
        <div className='grid gap-4 lg:grid-cols-3 lg:gap-8 xl:grid-cols-4'>
          {/* Left Column */}
          <div className='grid gap-4 lg:col-span-3'>
            <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
              <CardHeader>
                <CardTitle className='text-xl font-bold text-amber-100'>
                  فرماندهی AHOS
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
                  {[
                    { title: 'کل کاربران', value: '2,543', change: '+12%' },
                    { title: 'میزان پاسخگویی', value: '98%', change: '+2%' },
                    { title: 'سیستم‌های فعال', value: '24', change: '+3%' },
                    { title: 'نرخ خطا', value: '0.2%', change: '-0.1%' },
                  ].map((stat, i) => (
                    <div key={i}>
                      <p className='text-sm font-medium text-amber-200/60'>
                        {stat.title}
                      </p>
                      <div className='flex items-baseline gap-x-2'>
                        <p className='text-2xl font-semibold text-amber-100'>
                          {stat.value}
                        </p>
                        <p className='text-sm text-amber-400'>
                          {stat.change}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          <div className='grid gap-4 lg:col-span-3'>
            <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
              <CardHeader>
                <CardTitle className='text-xl font-bold text-amber-100'>
                  خدمات پیشنهادی
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
                  {[
                    {
                      title: 'دوره‌های آموزشی',
                      description: 'دوره‌های تخصصی و کاربردی',
                      icon: '📚',
                    },
                    {
                      title: 'پشتیبانی فنی',
                      description: 'پشتیبانی ۲۴ ساعته',
                      icon: '🔧',
                    },
                    {
                      title: 'تحلیل داده‌ها',
                      description: 'تحلیل پیشرفته داده‌ها',
                      icon: '📊',
                    },
                    {
                      title: 'امنیت سایبری',
                      description: 'امنیت پیشرفته',
                      icon: '🛡️',
                    },
                  ].map((service, i) => (
                    <div
                      key={i}
                      className='flex flex-col items-center gap-2 rounded-lg border border-amber-200/20 p-4 hover:border-amber-300/40 transition-colors'
                    >
                      <span className='text-3xl'>{service.icon}</span>
                      <h3 className='text-sm font-medium text-amber-100'>
                        {service.title}
                      </h3>
                      <p className='text-xs text-amber-200/60 text-center'>
                        {service.description}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          <div className='grid gap-4 lg:col-span-3'>
            <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
              <CardHeader>
                <CardTitle className='text-xl font-bold text-amber-100'>
                  فعالیت‌های اخیر
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='space-y-4'>
                  {[
                    {
                      action: 'ورود جدید',
                      user: 'admin',
                      time: '۱۰ دقیقه پیش',
                      icon: '👤',
                    },
                    {
                      action: 'تغییر تنظیمات',
                      user: 'user',
                      time: '۳۰ دقیقه پیش',
                      icon: '⚙️',
                    },
                    {
                      action: 'پشتیبان‌گیری',
                      user: 'system',
                      time: '۱ ساعت پیش',
                      icon: '💾',
                    },
                  ].map((activity, i) => (
                    <div key={i} className='flex items-center gap-4'>
                      <div className='h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center'>
                        <span className='text-lg text-amber-400'>
                          {activity.icon}
                        </span>
                      </div>
                      <div className='flex-1'>
                        <p className='font-medium text-amber-100'>
                          {activity.action}
                        </p>
                        <p className='text-sm text-amber-200/60'>
                          توسط {activity.user} - {activity.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  return (
    <div className='grid h-full w-full lg:grid-cols-[280px,1fr]'>
      <div className='hidden lg:block'>
        <AppSidebar />
      </div>
      <div className='flex h-full w-full flex-col lg:col-span-3'>
        <DashboardContent />
      </div>
    </div>
  )
}