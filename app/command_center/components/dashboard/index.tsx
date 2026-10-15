import { ShieldCheck, Activity, Database, Globe, Cpu, Zap, AlertTriangle, CheckCircle2, Lock } from 'lucide-react'
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
          <h1 className='text-2xl font-bold tracking-tight'>AHOS Command Center</h1>
          <div className='flex items-center space-x-2'>
            <Button>System Status</Button>
            <Button variant='outline'>Download Report</Button>
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

          {/* ===== Overview Tab ===== */}
          <TabsContent value='overview' className='space-y-4'>
            {/* Top KPI Cards */}
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <Card className='backdrop-blur bg-white/5 border border-[#D4AF37]/40 text-slate-100 shadow-[0_0_25px_rgba(212,175,55,0.2)] hover:shadow-[0_0_35px_rgba(212,175,55,0.3)] transition-all duration-300'>
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
              <Card className='backdrop-blur bg-white/5 border border-cyan-500/40 text-slate-100 shadow-[0_0_25px_rgba(0,240,255,0.2)] hover:shadow-[0_0_35px_rgba(0,240,255,0.3)] transition-all duration-300'>
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
              <Card className='backdrop-blur bg-white/5 border border-[#D4AF37]/40 text-slate-100 shadow-[0_0_25px_rgba(212,175,55,0.2)] hover:shadow-[0_0_35px_rgba(212,175,55,0.3)] transition-all duration-300'>
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
              <Card className='backdrop-blur bg-white/5 border border-cyan-500/40 text-slate-100 shadow-[0_0_25px_rgba(0,240,255,0.2)] hover:shadow-[0_0_35px_rgba(0,240,255,0.3)] transition-all duration-300'>
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

            {/* Main Content Grid */}
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-12'>
              {/* Left Column - Main Charts */}
              <div className='lg:col-span-8 space-y-4'>
                <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                  <CardHeader>
                    <CardTitle className='text-[#D4AF37]'>Opportunity Inflow & Volatility</CardTitle>
                    <CardDescription className='text-slate-400'>
                      Canonical probability and real-time signal velocity
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Overview />
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Intelligence Feed & Quick Actions */}
              <div className='lg:col-span-4 space-y-4'>
                {/* Live Intelligence Feed */}
                <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
                  <CardHeader>
                    <CardTitle className='text-cyan-400'>Live Intelligence Feed</CardTitle>
                    <CardDescription className='text-slate-400'>
                      Real-time security and liquidity updates
                    </CardDescription>
                  </CardHeader>
                  <CardContent className='space-y-4'>
                    <div className='flex items-start gap-3 p-3 rounded-lg bg-[#0b0b0f]/80 border border-[#D4AF37]/20'>
                      <div className='flex h-8 w-8 items-center justify-center rounded-full bg-[#D4AF37]/10 text-[#D4AF37] flex-shrink-0'>
                        <Zap className='h-4 w-4' />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <p className='text-sm font-medium text-white'>Gate Evaluation Complete</p>
                        <p className='text-xs text-slate-400'>Lane B security check verified in 1.2s</p>
                      </div>
                      <span className='text-xs text-slate-500'>Just now</span>
                    </div>

                    <div className='flex items-start gap-3 p-3 rounded-lg bg-[#0b0b0f]/80 border border-cyan-500/20'>
                      <div className='flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 flex-shrink-0'>
                        <CheckCircle2 className='h-4 w-4' />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <p className='text-sm font-medium text-white'>Canonical Sync Active</p>
                        <p className='text-xs text-slate-400'>DecisionAdvisor pipeline operational</p>
                      </div>
                      <span className='text-xs text-slate-500'>2m ago</span>
                    </div>

                    <div className='flex items-start gap-3 p-3 rounded-lg bg-[#0b0b0f]/80 border border-cyan-500/20'>
                      <div className='flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 flex-shrink-0'>
                        <Lock className='h-4 w-4' />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <p className='text-sm font-medium text-white'>Lane A Freeze Status</p>
                        <p className='text-xs text-slate-400'>config/lane_a_freeze.sha256 verified</p>
                      </div>
                      <span className='text-xs text-slate-500'>5m ago</span>
                    </div>

                    <div className='flex items-start gap-3 p-3 rounded-lg bg-[#0b0b0f]/80 border border-cyan-500/20'>
                      <div className='flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 flex-shrink-0'>
                        <Zap className='h-4 w-4' />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <p className='text-sm font-medium text-white'>Token Analysis Batch</p>
                        <p className='text-xs text-slate-400'>12 new opportunities scored</p>
                      </div>
                      <span className='text-xs text-slate-500'>8m ago</span>
                    </div>

                    <div className='flex items-start gap-3 p-3 rounded-lg bg-[#0b0b0f]/80 border border-cyan-500/20'>
                      <div className='flex h-8 w-8 items-center justify-center rounded-full bg-[#D4AF37]/10 text-[#D4AF37] flex-shrink-0'>
                        <AlertTriangle className='h-4 w-4' />
                      </div>
                      <div className='flex-1 min-w-0'>
                        <p className='text-sm font-medium text-white'>AI Advisor Constraint Check</p>
                        <p className='text-xs text-slate-400'>No override privileges detected</p>
                      </div>
                      <span className='text-xs text-slate-500'>12m ago</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                  <CardHeader>
                    <CardTitle className='text-[#D4AF37]'>Quick Actions</CardTitle>
                    <CardDescription className='text-slate-400'>
                      Common operational tasks
                    </CardDescription>
                  </CardHeader>
                  <CardContent className='space-y-2'>
                    <Button className='w-full justify-between bg-[#0b0b0f]/80 border border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10'>
                      <span>Run Full Security Gate</span>
                      <ShieldCheck className='h-4 w-4' />
                    </Button>
                    <Button className='w-full justify-between bg-[#0b0b0f]/80 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10'>
                      <span>Score New Tokens</span>
                      <Activity className='h-4 w-4' />
                    </Button>
                    <Button className='w-full justify-between bg-[#0b0b0f]/80 border border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10'>
                      <span>Review Freeze Hash</span>
                      <Lock className='h-4 w-4' />
                    </Button>
                    <Button className='w-full justify-between bg-[#0b0b0f]/80 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10'>
                      <span>Export Report</span>
                      <Database className='h-4 w-4' />
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Bottom Row Panels */}
            <div className='grid grid-cols-1 lg:grid-cols-4 gap-4'>
              {/* University / Research Lab */}
              <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>AHOS University</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Research & Training
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-2'>
                    <div className='text-sm text-white'>Active Courses: 12</div>
                    <div className='text-xs text-cyan-400'>+3 new this week</div>
                    <div className='text-xs text-[#D4AF37]'>Progress: 78%</div>
                  </div>
                </CardContent>
              </Card>

              {/* Agent Society */}
              <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
                <CardHeader>
                  <CardTitle className='text-cyan-400'>Agent Society</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Community Network
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-2'>
                    <div className='text-sm text-white'>Members: 2,847</div>
                    <div className='text-xs text-[#D4AF37]'>+127 today</div>
                    <div className='text-xs text-cyan-400'>Teams: 45 active</div>
                  </div>
                </CardContent>
              </Card>

              {/* Auto Trading */}
              <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
                <CardHeader>
                  <CardTitle className='text-[#D4AF37]'>Auto Trading</CardTitle>
                  <CardDescription className='text-slate-400'>
                    Performance Overview
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-2'>
                    <div className='text-sm text-white'>P&L: +12.3%</div>
                    <div className='text-xs text-cyan-400'>24h change</div>
                    <div className='text-xs text-[#D4AF37']'>Active Bots: 23</div>
                  </div>
                </CardContent>
              </Card>

              {/* Chat with AHOS */}
              <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
                <CardHeader>
                  <CardTitle className='text-cyan-400'>Chat with AHOS</CardTitle>
                  <CardDescription className='text-slate-400'>
                    AI Assistant
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-2'>
                    <div className='text-sm text-white'>Status: Online</div>
                    <div className='text-xs text-[#D4AF37]'>Response: 0.8s avg</div>
                    <div className='text-xs text-cyan-400'>Sessions: 156 today</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ===== Analytics Tab ===== */}
          <TabsContent value='analytics' className='space-y-4'>
            <Analytics />
          </TabsContent>

          {/* ===== Globe Tab ===== */}
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
