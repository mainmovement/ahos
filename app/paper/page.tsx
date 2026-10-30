import { AhosShell } from '@/components/shell/AhosShell'
import { loadHomeBrief } from '@/home_brief'

export const dynamic = 'force-dynamic'

/**
 * Paper names from the Python receipt. This page does not decide and does not trade.
 * The process already listening on port 3200 is a previous build; it will not show
 * this page until that build is replaced.
 */
export default async function PaperOpenNamesPage() {
  const home = await loadHomeBrief()
  const names = home?.openNames ?? []

  return (
    <AhosShell>
      <main dir='rtl' className='mx-auto flex min-h-svh max-w-xl flex-col gap-4 p-8'>
        <h1 className='text-2xl font-semibold'>دفتر کاغذی</h1>
        <p>معاملهٔ واقعی خاموش است.</p>
        {names.length > 0 ? (
          <p>{names.join('، ')}</p>
        ) : (
          <p>نام موقعیت‌ها در پرونده نیست.</p>
        )}
      </main>
    </AhosShell>
  )
}
