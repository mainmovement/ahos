import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Globe } from 'lucide-react'

const marketData = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    price: '$43,250.00',
    change: '+2.34%',
    volume: '$28.5B',
    marketCap: '$845.2B',
    sentiment: 'BULLISH',
    rank: 1,
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: '$2,156.78',
    change: '+1.87%',
    volume: '$15.2B',
    marketCap: '$258.9B',
    sentiment: 'BULLISH',
    rank: 2,
  },
  {
    symbol: 'SOL',
    name: 'Solana',
    price: '$98.45',
    change: '+3.21%',
    volume: '$4.8B',
    marketCap: '$42.1B',
    sentiment: 'VERY_BULLISH',
    rank: 5,
  },
  {
    symbol: 'BNB',
    name: 'Binance Coin',
    price: '$315.20',
    change: '-0.45%',
    volume: '$1.2B',
    marketCap: '$48.3B',
    sentiment: 'NEUTRAL',
    rank: 3,
  },
  {
    symbol: 'ADA',
    name: 'Cardano',
    price: '$0.48',
    change: '-1.23%',
    volume: '$580M',
    marketCap: '$16.8B',
    sentiment: 'BEARISH',
    rank: 8,
  },
  {
    symbol: 'AVAX',
    name: 'Avalanche',
    price: '$38.75',
    change: '+0.92%',
    volume: '$425M',
    marketCap: '$14.2B',
    sentiment: 'NEUTRAL',
    rank: 12,
  },
  {
    symbol: 'DOT',
    name: 'Polkadot',
    price: '$7.23',
    change: '+2.15%',
    volume: '$320M',
    marketCap: '$9.1B',
    sentiment: 'BULLISH',
    rank: 13,
  },
  {
    symbol: 'MATIC',
    name: 'Polygon',
    price: '$0.85',
    change: '+1.47%',
    volume: '$380M',
    marketCap: '$8.4B',
    sentiment: 'BULLISH',
    rank: 14,
  },
]

const getSentimentBadge = (sentiment: string) => {
  switch (sentiment) {
    case 'VERY_BULLISH':
      return <Badge className='bg-green-500/20 text-green-300 border-green-500/30'>VERY BULLISH</Badge>
    case 'BULLISH':
      return <Badge className='bg-green-400/20 text-green-300 border-green-400/30'>BULLISH</Badge>
    case 'NEUTRAL':
      return <Badge className='bg-gray-500/20 text-gray-300 border-gray-500/30'>NEUTRAL</Badge>
    case 'BEARISH':
      return <Badge className='bg-red-500/20 text-red-300 border-red-500/30'>BEARISH</Badge>
    default:
      return <Badge>{sentiment}</Badge>
  }
}

const getChangeColor = (change: string) => {
  if (change.startsWith('+')) return 'text-green-300'
  if (change.startsWith('-')) return 'text-red-300'
  return 'text-muted-foreground'
}

export function GlobalMarkets() {
  return (
    <Card>
      <CardHeader>
        <div className='flex items-center gap-2'>
          <Globe className='h-5 w-5 text-cyan-400' />
          <CardTitle>Global Markets</CardTitle>
        </div>
        <div className='text-sm text-muted-foreground'>
          Real-time cryptocurrency market data
        </div>
      </CardHeader>
      <CardContent>
        <div className='space-y-4'>
          {marketData.map((market) => (
            <div
              key={market.symbol}
              className='flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-4 transition-all hover:bg-white/[0.04]'
            >
              <div className='flex items-center gap-3'>
                <div className='text-2xl font-bold text-cyan-400'>
                  #{market.rank}
                </div>
                <div className='flex-1'>
                  <div className='flex items-center gap-2'>
                    <span className='font-bold text-sm'>${market.symbol}</span>
                    <span className='text-sm text-muted-foreground'>
                      {market.name}
                    </span>
                  </div>
                  <div className='flex items-center gap-4 mt-2'>
                    <span className={`font-medium ${getChangeColor(market.change)}`}>
                      {market.price}
                    </span>
                    <span className={`text-sm ${getChangeColor(market.change)}`}>
                      {market.change}
                    </span>
                  </div>
                </div>
              </div>
              <div className='flex items-center gap-4 text-right'>
                <div className='text-xs text-muted-foreground'>
                  <div>{market.volume}</div>
                  <div className='mt-1'>{market.marketCap}</div>
                </div>
                {getSentimentBadge(market.sentiment)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}