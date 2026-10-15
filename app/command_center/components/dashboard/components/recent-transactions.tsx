import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const transactions = [
  {
    id: 'TX001',
    symbol: 'BTC/USDT',
    type: 'PAPER_BUY',
    amount: '0.5',
    price: '$43,250',
    time: '2 min ago',
    status: 'EXECUTED',
    profit: '+2.3%',
  },
  {
    id: 'TX002',
    symbol: 'ETH/USDT',
    type: 'PAPER_SELL',
    amount: '2.0',
    price: '$2,150',
    time: '5 min ago',
    status: 'EXECUTED',
    profit: '+1.8%',
  },
  {
    id: 'TX003',
    symbol: 'SOL/USDT',
    type: 'PAPER_BUY',
    amount: '10',
    price: '$98.50',
    time: '8 min ago',
    status: 'PENDING',
    profit: null,
  },
  {
    id: 'TX004',
    symbol: 'BNB/USDT',
    type: 'PAPER_SELL',
    amount: '5',
    price: '$315.20',
    time: '12 min ago',
    status: 'EXECUTED',
    profit: '+0.9%',
  },
  {
    id: 'TX005',
    symbol: 'AVAX/USDT',
    type: 'PAPER_BUY',
    amount: '15',
    price: '$38.75',
    time: '15 min ago',
    status: 'EXECUTED',
    profit: '+3.2%',
  },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'EXECUTED':
      return <Badge className='bg-green-500/20 text-green-300 border-green-500/30'>EXECUTED</Badge>
    case 'PENDING':
      return <Badge className='bg-yellow-500/20 text-yellow-300 border-yellow-500/30'>PENDING</Badge>
    case 'FAILED':
      return <Badge className='bg-red-500/20 text-red-300 border-red-500/30'>FAILED</Badge>
    default:
      return <Badge>{status}</Badge>
  }
}

export function RecentTransactions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Price</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Profit</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => (
              <TableRow key={tx.id}>
                <TableCell className='font-medium'>{tx.symbol}</TableCell>
                <TableCell>
                  <Badge variant={tx.type === 'PAPER_BUY' ? 'default' : 'secondary'}>
                    {tx.type.replace('_', ' ')}
                  </Badge>
                </TableCell>
                <TableCell>{tx.amount}</TableCell>
                <TableCell>{tx.price}</TableCell>
                <TableCell className='text-muted-foreground text-sm'>
                  {tx.time}
                </TableCell>
                <TableCell>{getStatusBadge(tx.status)}</TableCell>
                <TableCell>
                  {tx.profit && (
                    <span className={`font-medium ${
                      tx.profit.startsWith('+')
                        ? 'text-green-300'
                        : tx.profit.startsWith('-')
                          ? 'text-red-300'
                          : 'text-muted-foreground'
                    }`}>
                      {tx.profit}
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}