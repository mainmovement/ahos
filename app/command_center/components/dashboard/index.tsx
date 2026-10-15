import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ConfigDrawer } from '../layout/config-drawer'
import { Header } from '../layout/header'
import { Main } from '../layout/main'
import { TopNav } from '../layout/top-nav'
import { ProfileDropdown } from '../layout/profile-dropdown'
import { Search } from '../layout/search'
import { Overview } from './components/overview'
import { Analytics } from './components/analytics'
import { RecentTransactions } from './components/recent-transactions'
import { SecurityAlerts } from './components/security-alerts'
import { GlobalMarkets } from './components/global-markets'
import { LiquidityFlow } from './components/liquidity-flow'

export function Dashboard() {
  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <TopNav links={topNav} className='me-auto' />
        <Search placeholder='Search markets, signals, alerts...' />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      {/* ===== Main ===== */}
      <Main>
        <div className='mb-6 flex items-center justify-between space-y-2'>
          <div>
            <h1 className='text-3xl font-bold tracking-tight'>Command Center</h1>
            <p className='text-muted-foreground'>
              Advanced crypto opportunity intelligence system
            </p>
          </div>
          <div className='flex items-center space-x-2'>
            <Button variant='outline' size='sm'>
              Export Report
            </Button>
            <Button size='sm'>
              New Signal
            </Button>
          </div>
        </div>

        {/* Market Overview Cards */}
        <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6'>
          <Card className='bg-gradient-to-br from-blue-500/10 to-blue-600/10 border-blue-400/30'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium text-blue-200'>
                Active Signals
              </CardTitle>
              <div className='h-4 w-4 rounded-full bg-blue-500 animate-pulse' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold text-blue-300'>247</div>
              <p className='text-xs text-blue-200/80'>
                +12% from last hour
              </p>
            </CardContent>
          </Card>

          <Card className='bg-gradient-to-br from-green-500/10 to-green-600/10 border-green-400/30'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium text-green-200'>
                Paper Positions
              </CardTitle>
              <div className='h-4 w-4 rounded-full bg-green-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold text-green-300'>18</div>
              <p className='text-xs text-green-200/80'>
                +3 from yesterday
              </p>
            </CardContent>
          </Card>

          <Card className='bg-gradient-to-br from-purple-500/10 to-purple-600/10 border-purple-400/30'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium text-purple-200'>
                Security Events
              </CardTitle>
              <div className='h-4 w-4 rounded-full bg-purple-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold text-purple-300'>3</div>
              <p className='text-xs text-purple-200/80'>
                2 critical, 1 warning
              </p>
            </CardContent>
          </Card>

          <Card className='bg-gradient-to-br from-cyan-500/10 to-cyan-600/10 border-cyan-400/30'>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium text-cyan-200'>
                Liquidity Score
              </CardTitle>
              <div className='h-4 w-4 rounded-full bg-cyan-500' />
            </CardHeader>
            <CardContent>
              <div className='text-2xl font-bold text-cyan-300'>8.7/10</div>
              <p className='text-xs text-cyan-200/80'>
                +0.3 from last update
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs
          orientation='vertical'
          defaultValue='overview'
          className='space-y-4'
        >
          <div className='w-full overflow-x-auto pb-2'>
            <TabsList className='grid w-full grid-cols-4'>
              <TabsTrigger value='overview'>Overview</TabsTrigger>
              <TabsTrigger value='analytics'>Analytics</TabsTrigger>
              <TabsTrigger value='markets'>Global Markets</TabsTrigger>
              <TabsTrigger value='security'>Security</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value='overview' className='space-y-4'>
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-3'>
              <Card className='col-span-1 lg:col-span-2'>
                <CardHeader>
                  <CardTitle>Signal Overview</CardTitle>
                  <CardDescription>
                    Real-time market intelligence and opportunity signals
                  </CardDescription>
                </CardHeader>
                <CardContent className='ps-2'>
                  <Overview />
                </CardContent>
              </Card>

              <Card className='col-span-1 lg:col-span-1'>
                <CardHeader>
                  <CardTitle>Recent Transactions</CardTitle>
                  <CardDescription>
                    Latest paper trading activities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentTransactions />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value='analytics' className='space-y-4'>
            <div className='grid grid-cols-1 gap-4 lg:grid-cols-2'>
              <Card>
                <CardHeader>
                  <CardTitle>Performance Analytics</CardTitle>
                  <CardDescription>
                    Portfolio and signal performance metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Analytics />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Liquidity Flow</CardTitle>
                  <CardDescription>
                    Market liquidity analysis and flow visualization
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <LiquidityFlow />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value='markets' className='space-y-4'>
            <Card>
              <CardHeader>
                <CardTitle>Global Markets</CardTitle>
                <CardDescription>
                  Real-time market data and global sentiment analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GlobalMarkets />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value='security' className='space-y-4'>
            <Card>
              <CardHeader>
                <CardTitle>Security Alerts</CardTitle>
                <CardDescription>
                  Critical security events and system monitoring
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SecurityAlerts />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}

const topNav = [
  {
    title: 'Overview',
    href: '/dashboard',
    isActive: true,
    disabled: false,
  },
  {
    title: 'Signals',
    href: '/signals',
    isActive: false,
    disabled: false,
  },
  {
    title: 'Markets',
    href: '/markets',
    isActive: false,
    disabled: false,
  },
  {
    title: 'Security',
    href: '/security',
    isActive: false,
    disabled: false,
  },
]