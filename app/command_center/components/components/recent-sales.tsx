import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const sales = [
  {
    id: '1',
    customer: 'علی رضایی',
    email: 'ali@example.com',
    amount: '$45,000',
    status: 'موفق',
    date: '2026-10-15',
  },
  {
    id: '2',
    customer: 'مریم احمدی',
    email: 'maryam@example.com',
    amount: '$32,000',
    status: 'موفق',
    date: '2026-10-14',
  },
  {
    id: '3',
    customer: 'سامان قاسمی',
    email: 'saman@example.com',
    amount: '$28,500',
    status: 'در انتظار',
    date: '2026-10-14',
  },
  {
    id: '4',
    customer: 'زهرا کریمی',
    email: 'zahra@example.com',
    amount: '$67,800',
    status: 'موفق',
    date: '2026-10-13',
  },
  {
    id: '5',
    customer: 'رسولی',
    email: 'reza@example.com',
    amount: '$23,400',
    status: 'لغو شده',
    date: '2026-10-13',
  },
]

export function RecentSales() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'موفق':
        return 'text-green-500'
      case 'در انتظار':
        return 'text-yellow-500'
      case 'لغو شده':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>فروش‌های اخیر</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>مشتری</TableHead>
              <TableHead>ایمیل</TableHead>
              <TableHead>مبلغ</TableHead>
              <TableHead>وضعیت</TableHead>
              <TableHead>تاریخ</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sales.map((sale) => (
              <TableRow key={sale.id}>
                <TableCell className='font-medium text-[#D4AF37]'>{sale.customer}</TableCell>
                <TableCell>{sale.email}</TableCell>
                <TableCell className='font-medium text-[#D4AF37]'>{sale.amount}</TableCell>
                <TableCell className={getStatusColor(sale.status)}>{sale.status}</TableCell>
                <TableCell>{sale.date}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}