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
import { Overview } from './components/overview'
import { Analytics } from './components/analytics'
import { RecentSales } from './components/recent-sales'

export function Dashboard() {
  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-2">
            <h1 className='text-xl font-bold tracking-tight'>AHOS Command Center</h1>
          </div>
        </div>
      </Header>

      {/* ===== Main ===== */}
      <Main>
        <div className='mb-8'>
          <h1 className='text-3xl font-bold tracking-tight bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 bg-clip-text text-transparent'>
            فرماندهی AHOS
          </h1>
          <p className='text-muted-foreground mt-2'>مرکز فرماندهی و هوش عملیاتی</p>
        </div>

        <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8'>
          <Card className="bg-gradient-to-br from-yellow-400/10 to-amber-500/5 border-yellow-400/20 backdrop-blur-sm">
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium text-yellow-400/80'>
                امتیاز امنیتی
              </CardTitle>
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
            </CardHeader>
            <CardContent>
              <RecentSales />
            </CardContent>
          </Card>
        </div>
        <Analytics />
      </Main>
    </>
  )
}
      </Main>
    </>
  )
}

