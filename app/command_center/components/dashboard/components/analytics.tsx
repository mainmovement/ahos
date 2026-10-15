import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'

const data = [
  {
    time: '00:00',
    signals: 45,
    confidence: 78,
    liquidity: 65,
  },
  {
    time: '04:00',
    signals: 52,
    confidence: 82,
    liquidity: 68,
  },
  {
    time: '08:00',
    signals: 78,
    confidence: 85,
    liquidity: 72,
  },
  {
    time: '12:00',
    signals: 125,
    confidence: 88,
    liquidity: 80,
  },
  {
    time: '16:00',
    signals: 198,
    confidence: 91,
    liquidity: 85,
  },
  {
    time: '20:00',
    signals: 156,
    confidence: 89,
    liquidity: 83,
  },
  {
    time: '24:00',
    signals: 89,
    confidence: 84,
    liquidity: 79,
  },
]

export function Analytics() {
  return (
    <ResponsiveContainer width='100%' height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray='3 3' stroke='rgba(0,0,0,0.1)' />
        <XAxis
          dataKey='time'
          stroke='#888888'
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke='#888888'
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(0,0,0,0.8)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
          }}
        />
        <Line
          type='monotone'
          dataKey='signals'
          stroke='#3b82f6'
          strokeWidth={2}
          dot={false}
        />
        <Line
          type='monotone'
          dataKey='confidence'
          stroke='#10b981'
          strokeWidth={2}
          dot={false}
        />
        <Line
          type='monotone'
          dataKey='liquidity'
          stroke='#f59e0b'
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}