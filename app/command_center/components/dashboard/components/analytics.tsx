import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { AnalyticsChart } from './analytics-chart'

export function Analytics() {
  return (
    <div className='space-y-4'>
      <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
        <CardHeader>
          <CardTitle className='text-[#D4AF37]'>Signal Velocity & Canonical Depth</CardTitle>
          <CardDescription className='text-slate-400'>
            Real-time evidence velocity and liquidity depth evaluation
          </CardDescription>
        </CardHeader>
        <CardContent className='px-6'>
          <AnalyticsChart />
        </CardContent>
      </Card>
      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
        <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium text-cyan-400'>Evidence Records</CardTitle>
            <svg
              xmlns='http://www.w3.org/2000/svg'
              viewBox='0 0 24 24'
              fill='none'
              stroke='currentColor'
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth='2'
              className='h-4 w-4 text-cyan-400'
            >
              <path d='M3 3v18h18' />
              <path d='M7 15l4-4 4 4 4-6' />
            </svg>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold text-white'>1,248</div>
            <p className='text-xs text-[#D4AF37]'>+12.4% verification rate</p>
          </CardContent>
        </Card>
        <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium text-[#D4AF37]'>
              Canonical Validity
            </CardTitle>
            <svg
              xmlns='http://www.w3.org/2000/svg'
              viewBox='0 0 24 24'
              fill='none'
              stroke='currentColor'
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth='2'
              className='h-4 w-4 text-[#D4AF37]'
            >
              <circle cx='12' cy='7' r='4' />
              <path d='M6 21v-2a6 6 0 0 1 12 0v2' />
            </svg>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold text-white'>832</div>
            <p className='text-xs text-cyan-400'>+5.8% probability score</p>
          </CardContent>
        </Card>
        <Card className='border-cyan-500/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(0,240,255,0.1)]'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium text-cyan-400'>Gate Tolerance</CardTitle>
            <svg
              xmlns='http://www.w3.org/2000/svg'
              viewBox='0 0 24 24'
              fill='none'
              stroke='currentColor'
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth='2'
              className='h-4 w-4 text-cyan-400'
            >
              <path d='M3 12h6l3 6 3-6h6' />
            </svg>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold text-white'>42%</div>
            <p className='text-xs text-[#D4AF37]'>-3.2% false positive drift</p>
          </CardContent>
        </Card>
        <Card className='border-[#D4AF37]/30 bg-[#0b0b0f]/90 text-slate-100 shadow-[0_0_15px_rgba(212,175,55,0.1)]'>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium text-[#D4AF37]'>Avg. Confirmation</CardTitle>
            <svg
              xmlns='http://www.w3.org/2000/svg'
              viewBox='0 0 24 24'
              fill='none'
              stroke='currentColor'
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth='2'
              className='h-4 w-4 text-[#D4AF37]'
            >
              <circle cx='12' cy='12' r='10' />
              <path d='M12 6v6l4 2' />
            </svg>
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold text-white'>3m 24s</div>
            <p className='text-xs text-cyan-400'>+18s latency velocity</p>
          </CardContent>
        </Card>
      </div>
      <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
        <Card className='col-span-1 border-[#D4AF37]/30 bg-[#0b0b0f]/90 lg:col-span-4'>
          <CardHeader>
            <CardTitle className='text-[#D4AF37]'>Signal Origin Distribution</CardTitle>
            <CardDescription className='text-slate-400'>
              Evidence provenance by lane and source
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SimpleBarList
              items={[
                { name: 'Lane A (Frozen)', value: 512 },
                { name: 'Lane B (Canonical)', value: 238 },
                { name: 'External Verified', value: 174 },
                { name: 'Operator Observed', value: 104 },
              ]}
              barClass='fill-[#D4AF37]'
              valueFormatter={(n) => `${n}`}
            />
          </CardContent>
        </Card>
        <Card className='col-span-1 border-cyan-500/30 bg-[#0b0b0f]/90 lg:col-span-3'>
          <CardHeader>
            <CardTitle className='text-cyan-400'>Gate Outcome Split</CardTitle>
            <CardDescription className='text-slate-400'>
              Security overlay classification
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SimpleBarList
              items={[
                { name: 'PASS', value: 74 },
                { name: 'REJECT', value: 22 },
                { name: 'INCOMPLETE', value: 4 },
              ]}
              barClass='fill-cyan-400'
              valueFormatter={(n) => `${n}%`}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function SimpleBarList({
  items,
  valueFormatter,
  barClass,
}: {
  items: { name: string; value: number }[]
  valueFormatter: (n: number) => string
  barClass: string
}) {
  const max = Math.max(...items.map((i) => i.value), 1)
  return (
    <ul className='space-y-3'>
      {items.map((i) => {
        const width = `${Math.round((i.value / max) * 100)}%`
        return (
          <li key={i.name} className='flex items-center justify-between gap-3'>
            <div className='min-w-0 flex-1'>
              <div className='mb-1 truncate text-xs text-muted-foreground'>
                {i.name}
              </div>
              <div className='h-2.5 w-full rounded-full bg-muted'>
                <div
                  className={`h-2.5 rounded-full ${barClass}`}
                  style={{ width }}
                />
              </div>
            </div>
            <div className='ps-2 text-xs font-medium tabular-nums'>
              {valueFormatter(i.value)}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
