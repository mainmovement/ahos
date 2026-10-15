import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { useState } from 'react'

const alerts = [
  {
    id: 1,
    type: 'CRITICAL',
    title: 'Unusual Trading Activity Detected',
    description: 'Multiple rapid paper trades on ETH/USDT detected in 5-minute window.',
    severity: 'critical',
    time: '2 min ago',
    icon: AlertCircle,
  },
  {
    id: 2,
    type: 'WARNING',
    title: 'Liquidity Drop Detected',
    description: 'SOL/USDT liquidity pool below 20% of normal levels.',
    severity: 'warning',
    time: '15 min ago',
    icon: AlertTriangle,
  },
  {
    id: 3,
    type: 'INFO',
    title: 'System Update Completed',
    description: 'Latest identity scoring update deployed successfully.',
    severity: 'info',
    time: '1 hour ago',
    icon: CheckCircle,
  },
  {
    id: 4,
    type: 'CRITICAL',
    title: 'External Connection Blocked',
    description: 'Unrecognized WebSocket connection attempt blocked by security gate.',
    severity: 'critical',
    time: '2 hours ago',
    icon: AlertCircle,
  },
  {
    id: 5,
    type: 'WARNING',
    title: 'API Rate Limit Approaching',
    description: 'Registry API usage at 85% of limit. Consider implementing caching.',
    severity: 'warning',
    time: '3 hours ago',
    icon: AlertTriangle,
  },
]

const getSeverityBadge = (severity: string) => {
  switch (severity) {
    case 'critical':
      return (
        <Badge className='bg-red-500/20 text-red-300 border-red-500/30 flex items-center gap-1'>
          <AlertCircle className='h-3 w-3' />
          CRITICAL
        </Badge>
      )
    case 'warning':
      return (
        <Badge className='bg-yellow-500/20 text-yellow-300 border-yellow-500/30 flex items-center gap-1'>
          <AlertTriangle className='h-3 w-3' />
          WARNING
        </Badge>
      )
    case 'info':
      return (
        <Badge className='bg-blue-500/20 text-blue-300 border-blue-500/30 flex items-center gap-1'>
          <CheckCircle className='h-3 w-3' />
          INFO
        </Badge>
      )
    default:
      return <Badge>{severity}</Badge>
  }
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical':
      return <AlertCircle className='h-4 w-4 text-red-400' />
    case 'warning':
      return <AlertTriangle className='h-4 w-4 text-yellow-400' />
    case 'info':
      return <CheckCircle className='h-4 w-4 text-green-400' />
    default:
      return null
  }
}

export function SecurityAlerts() {
  const [expandedAlert, setExpandedAlert] = useState<number | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security Events</CardTitle>
      </CardHeader>
      <CardContent>
        <div className='space-y-4'>
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className='rounded-lg border border-white/5 bg-white/[0.02] p-4 transition-all hover:bg-white/[0.04]'
            >
              <div className='flex items-start justify-between gap-4'>
                <div className='flex-1 space-y-2'>
                  <div className='flex items-center gap-3'>
                    {getSeverityIcon(alert.severity)}
                    <div className='flex-1'>
                      <div className='flex items-center justify-between'>
                        <h4 className='font-medium text-sm'>{alert.title}</h4>
                        {getSeverityBadge(alert.severity)}
                      </div>
                      <p className='text-sm text-muted-foreground'>
                        {alert.description}
                      </p>
                    </div>
                  </div>
                  <div className='flex items-center justify-between text-xs text-muted-foreground'>
                    <span>{alert.time}</span>
                    <span className='flex items-center gap-1'>
                      <Shield className='h-3 w-3' />
                      {alert.type}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}