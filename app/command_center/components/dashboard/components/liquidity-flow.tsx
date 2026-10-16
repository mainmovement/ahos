'use client'

import { RadialBarChart, RadialBar, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const data = [
  {
    name: 'BTC/USDT',
    liquidity: 85,
    depth: 'High',
    value: 28.5,
  },
  {
    name: 'ETH/USDT',
    liquidity: 78,
    depth: 'High',
    value: 15.2,
  },
  {
    name: 'SOL/USDT',
    liquidity: 92,
    depth: 'Very High',
    value: 4.8,
  },
  {
    name: 'BNB/USDT',
    liquidity: 65,
    depth: 'Medium',
    value: 1.2,
  },
  {
    name: 'ADA/USDT',
    liquidity: 45,
    depth: 'Low',
    value: 0.58,
  },
  {
    name: 'Others',
    liquidity: 55,
    depth: 'Medium',
    value: 8.7,
  },
]

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

const getDepthColor = (depth: string) => {
  switch (depth) {
    case 'Very High':
      return 'text-green-400'
    case 'High':
      return 'text-green-300'
    case 'Medium':
      return 'text-yellow-300'
    case 'Low':
      return 'text-red-300'
    default:
      return 'text-muted-foreground'
  }
}

export function LiquidityFlow() {
  return (
    <div className='space-y-6'>
      <div className='grid grid-cols-2 gap-4'>
        <div className='text-center p-4 rounded-lg bg-white/[0.02] border border-white/5'>
          <div className='text-2xl font-bold text-cyan-300'>
            68.7%
          </div>
          <div className='text-sm text-muted-foreground'>
            Average Liquidity Score
          </div>
        </div>
        <div className='text-center p-4 rounded-lg bg-white/[0.02] border border-white/5'>
          <div className='text-2xl font-bold text-green-300'>
            $58.98B
          </div>
          <div className='text-sm text-muted-foreground'>
            Total Market Depth
          </div>
        </div>
      </div>

      <ResponsiveContainer width='100%' height={250}>
        <RadialBarChart
          cx='50%'
          cy='50%'
          innerRadius='40%'
          outerRadius='100%'
          barSize={16}
          data={data}
          startAngle={180}
          endAngle={0}
        >
          <RadialBar
            dataKey='liquidity'
            fill='#8884d8'
            background
            cornerRadius={4}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0,0,0,0.8)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
            formatter={(value: number, name: string) => [
              `${value}%`,
              'Liquidity Score'
            ]}
          />
        </RadialBarChart>
      </ResponsiveContainer>

      <div className='space-y-3'>
        <div className='grid grid-cols-3 gap-4 text-sm'>
          <div>
            <div className='text-muted-foreground mb-1'>Total Pairs</div>
            <div className='font-bold text-cyan-300'>25</div>
          </div>
          <div>
            <div className='text-muted-foreground mb-1'>High Depth</div>
            <div className='font-bold text-green-300'>8</div>
          </div>
          <div>
            <div className='text-muted-foreground mb-1'>Low Depth</div>
            <div className='font-bold text-red-300'>3</div>
          </div>
        </div>

        <div className='space-y-2'>
          {data.map((item, index) => (
            <div key={item.name} className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <div
                  className='w-3 h-3 rounded-full'
                  style={{ backgroundColor: COLORS[index] }}
                />
                <span className='text-sm font-medium'>{item.name}</span>
              </div>
              <div className='flex items-center gap-2'>
                <span className={`text-xs ${getDepthColor(item.depth)}`}>
                  {item.depth}
                </span>
                <span className='text-sm text-muted-foreground'>
                  {item.liquidity}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}