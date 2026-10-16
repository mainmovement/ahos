'use client'

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'

const data = [
  {
    name: 'Jan',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Feb',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Mar',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Apr',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'May',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Jun',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Jul',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Aug',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Sep',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Oct',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Nov',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
  {
    name: 'Dec',
    signals: Math.floor(Math.random() * 200) + 50,
    opportunities: Math.floor(Math.random() * 100) + 20,
  },
]

export function Overview() {
  return (
    <ResponsiveContainer width='100%' height={350}>
      <BarChart data={data}>
        <XAxis
          dataKey='name'
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
          tickFormatter={(value) => value}
        />
        <Bar dataKey='signals' fill='#3b82f6' radius={[4, 4, 0, 0]} />
        <Bar dataKey='opportunities' fill='#10b981' radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}