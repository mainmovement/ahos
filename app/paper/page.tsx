import { AhosShell } from '@/components/shell/AhosShell'
import { loadHomeBrief } from '@/home_brief'

export const dynamic = 'force-dynamic'

/**
 * Minimal paper page. Names and equity come from the Python receipt
 * (reports/grok/PAPER/mehrdad_status.json). This page does not decide and does not trade.
 * A missing value shows as «—»; nothing is invented.
 */
export default async function PaperOpenNamesPage() {
  const home = await loadHomeBrief()
  const names = home?.openNames ?? []
  const equity = home?.equityUsd ?? null

  return (
    <AhosShell>
      <main dir='rtl' className='mx-auto flex min-h-svh max-w-xl flex-col gap-6 p-8'>
        <div className='text-center'>
          <div className='text-sm opacity-60'>موجودی</div>
          <div className='mt-1 text-4xl font-light tabular-nums' dir='ltr'>
            {typeof equity === 'number' ? `$${equity.toFixed(2)}` : '—'}
          </div>
        </div>

        <table className='w-full text-right'>
          <thead>
            <tr className='text-sm opacity-60'>
              <th className='py-2 font-normal'>#</th>
              <th className='py-2 font-normal'>معاملهٔ باز</th>
            </tr>
          </thead>
          <tbody>
            {names.length > 0 ? (
              names.map((n, i) => (
                <tr key={n} className='border-t border-white/10'>
                  <td className='py-2 opacity-60'>{i + 1}</td>
                  <td className='py-2' dir='ltr' style={{ textAlign: 'right' }}>{n}</td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={2} className='py-2 opacity-50'>—</td></tr>
            )}
          </tbody>
        </table>

        <details className='text-sm opacity-70'>
          <summary className='cursor-pointer text-xs opacity-60'>جزئیات فنی</summary>
          <div className='mt-2 flex flex-col gap-1'>
            <p>معاملهٔ واقعی خاموش است.</p>
            <p>منبع: reports/grok/PAPER/mehrdad_status.json</p>
            {home?.missingFa?.map((m) => <p key={m}>{m}</p>)}
          </div>
        </details>
      </main>
    </AhosShell>
  )
}
