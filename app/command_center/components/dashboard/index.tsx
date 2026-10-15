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
      <div className='flex-1 overflow-y-auto p-4'>
        {/* KPI Cards Row */}
        <div className='grid gap-4 mb-6 lg:grid-cols-4'>
          {[
            { title: 'کل کاربران', value: '2,543', change: '+12%', icon: '👥' },
            { title: 'فرصت‌ها شناسایی شده', value: '48', change: '+23%', icon: '🎯' },
            { title: 'سیستم‌های فعال', value: '24', change: '+3%', icon: '🖥️' },
            { title: 'نرخ موفقیت', value: '98.2%', change: '+1.2%', icon: '✅' },
          ].map((stat, i) => (
            <Card key={i} className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium text-amber-200/60'>
                  {stat.title}
                </CardTitle>
                <span className='text-2xl'>{stat.icon}</span>
              </CardHeader>
              <CardContent>
                <div className='flex items-baseline gap-x-2'>
                  <p className='text-2xl font-bold text-amber-100'>
                    {stat.value}
                  </p>
                  <p className='text-sm text-green-400'>
                    {stat.change}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Area */}
        <div className='grid gap-4 lg:grid-cols-3'>
          {/* Center Globe */}
          <div className='lg:col-span-2'>
            <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm h-[400px]'>
              <CardHeader>
                <CardTitle className='text-xl font-bold text-amber-100'>
                  نمایه جهانی AHOS
                </CardTitle>
              </CardHeader>
              <CardContent className='flex items-center justify-center h-[320px]'>
                <div className='text-center text-amber-200/60'>
                  <div className='text-4xl mb-4'>🌍</div>
                  <p>نمایه ۳D تحلیل فرصت‌ها</p>
                  <p className='text-sm mt-2'>در حال توسعه...</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Intelligence Feed */}
          <div className='lg:col-span-1'>
            <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
              <CardHeader>
                <CardTitle className='text-lg font-bold text-amber-100'>
                  تغذیه هوشمندی
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='space-y-3'>
                  {[
                    {
                      time: '۵ دقیقه پیش',
                      title: 'فرصت جدید در BTC/USDT',
                      message: 'پولیگان قوی تشخیص داده شد',
                      type: 'opportunity'
                    },
                    {
                      time: '۱۵ دقیقه پیش',
                      title: 'هشدار امنیتی',
                      message: 'تلاش غیرمجاز برای دسترسی',
                      type: 'security'
                    },
                    {
                      time: '۳۰ دقیقه پیش',
                      title: 'به‌روزرسانی سیستم',
                      message: 'الگوریتم v2.1 اجرا شد',
                      type: 'system'
                    },
                  ].map((item, i) => (
                    <div key={i} className='p-3 rounded-lg border border-amber-200/20'>
                      <div className='flex items-center justify-between mb-1'>
                        <span className='text-xs text-amber-200/60'>{item.time}</span>
                        {item.type === 'opportunity' && <span className='text-green-400 text-xs'>✓</span>}
                        {item.type === 'security' && <span className='text-red-400 text-xs'>⚠</span>}
                        {item.type === 'system' && <span className='text-blue-400 text-xs'>⚙</span>}
                      </div>
                      <h4 className='text-sm font-medium text-amber-100 mb-1'>
                        {item.title}
                      </h4>
                      <p className='text-xs text-amber-200/60'>
                        {item.message}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Bottom Row */}
        <div className='grid gap-4 mt-6 lg:grid-cols-2'>
          {/* Market Scan */}
          <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
            <CardHeader>
              <CardTitle className='text-lg font-bold text-amber-100'>
                اسکن بازار لحظه‌ای
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-2'>
                {[
                  { pair: 'BTC/USDT', trend: 'صعودی', confidence: '92%' },
                  { pair: 'ETH/USDT', trend: 'نوسانی', confidence: '78%' },
                  { pair: 'BNB/USDT', trend: 'صعودی', confidence: '85%' },
                  { pair: 'ADA/USDT', trend: 'نزولی', confidence: '67%' },
                ].map((item, i) => (
                  <div key={i} className='flex items-center justify-between py-2 border-b border-amber-200/10'>
                    <span className='text-sm font-medium text-amber-100'>
                      {item.pair}
                    </span>
                    <div className='flex items-center gap-2'>
                      <span className={`text-xs ${item.trend === 'صعودی' ? 'text-green-400' : item.trend === 'نزولی' ? 'text-red-400' : 'text-amber-400'}`}>
                        {item.trend}
                      </span>
                      <span className='text-xs text-amber-200/60'>
                        {item.confidence}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Canonical Decision */}
          <Card className='bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm'>
            <CardHeader>
              <CardTitle className='text-lg font-bold text-amber-100'>
                تصمیم کانونی
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className='text-center py-4'>
                <div className='text-6xl mb-2'>🤖</div>
                <h4 className='text-lg font-bold text-amber-100 mb-2'>
                  وضعیت: نظارت
                </h4>
                <p className='text-sm text-amber-200/60 mb-4'>
                  سیستم در حال نظارت بر بازار است
                </p>
                <div className='flex gap-2 justify-center'>
                  <span className='px-3 py-1 rounded-full bg-green-500/20 text-green-300 text-xs border border-green-500/30'>
                    نرخ موفقیت: 98.2%
                  </span>
                  <span className='px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs border border-blue-500/30'>
                    تاخیر: 0.3s
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  return <DashboardContent />
}