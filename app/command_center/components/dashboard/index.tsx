import { ShieldCheck, Activity, Database, Globe, Cpu } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { TopNav } from '@/components/layout/top-nav'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Analytics } from './components/analytics'
import { HolographicGlobe } from './components/holographic-globe'
import { Overview } from './components/overview'
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
          <h1 className='text-2xl font-bold tracking-tight'>Dashboard</h1>
          <div className='flex items-center space-x-2'>
            <Button>Download</Button>
          </div>
        </div>
        <Tabs
          orientation='vertical'
          defaultValue='overview'
          className='space-y-4'
        >
          <div className='w-full overflow-x-auto pb-2'>
            <TabsList>
              <TabsTrigger value='overview'>Overview</TabsTrigger>
              <TabsTrigger value='analytics'>Analytics</TabsTrigger>
              <TabsTrigger value='globe'>
                Globe
              </TabsTrigger>
              <TabsTrigger value='reports' disabled>
                Reports
              </TabsTrigger>
              <TabsTrigger value='notifications' disabled>
                Notifications
              </TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value='overview' className='space-y-4'>
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-[#D4AF37]'>
                    Canonical State
                  </CardTitle>
                  <ShieldCheck className='h-4 w-4 text-[#D4AF37]' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold tracking-tight text-white'>INTEGRATION_READY</div>
                  <p className='text-xs text-cyan-400'>
                    Security Gate: PASS (Lane B)
                  </p>
                </CardContent>
              </Card>
              <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-cyan-400'>
                    Active Signals
                  </CardTitle>
                  <Activity className='h-4 w-4 text-cyan-400' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold tracking-tight text-white'>2,350 /s</div>
                  <p className='text-xs text-[#D4AF37]'>
                    +180.1% volatility index
                  </p>
                </CardContent>
              </Card>
              <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-[#D4AF37]'>Paper Opportunities</CardTitle>
                  <Database className='h-4 w-4 text-[#D4AF37]' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold tracking-tight text-white'>12,234</div>
                  <p className='text-xs text-cyan-400'>
                    +19% valid liquidity depth
                  </p>
                </CardContent>
              </Card>
              <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
                <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                  <CardTitle className='text-sm font-medium text-cyan-400'>
                    Agent Mesh Nodes
                  </CardTitle>
                  <Cpu className='h-4 w-4 text-cyan-400' />
                </CardHeader>
                <CardContent>
                  <div className='text-2xl font-bold tracking-tight text-white'>573 Active</div>
                  <p className='text-xs text-[#D4AF37]'>
                    +201 since last sync
                  </p>
                </CardContent>
              </Card>
            </div>
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
              <Card className='col-span-1 border-[#D4AF37]/30 bg-[#0b0b0f]/90 lg:col-span-4'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>Opportunity Inflow & Volatility</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Canonical probability and real-time signal velocity
                  </CardDescription>
                </CardHeader>
                <CardContent className='ps-2'>
                  <Overview />
                </CardContent>
              </Card>
              <Card className='col-span-1 border-cyan-500/30 bg-[#0b0b0f]/90 lg:col-span-3'>
                <CardHeader>
                  <CardTitle className='text-cyan-400'>Recent Intelligence Feeds</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Verified signals and security evaluations.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentSales />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value='analytics' className='space-y-4'>
            <Analytics />
          </TabsContent>
          <TabsContent value='globe' className='space-y-4'>
            <div className='grid gap-4'>
              <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 h-[600px] text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>Global Intelligence Mesh</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Real-time AHOS network topology and node distribution
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <HolographicGlobe className='h-[500px]' />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}

const topNav = [
  {
    title: 'Overview',
    href: 'dashboard/overview',
    isActive: true,
    disabled: false,
  },
  {
    title: 'Customers',
    href: 'dashboard/customers',
    isActive: false,
    disabled: true,
  },
  {
    title: 'Products',
    href: 'dashboard/products',
    isActive: false,
    disabled: true,
  },
  {
    title: 'Settings',
    href: 'dashboard/settings',
    isActive: false,
    disabled: true,
  },
]
