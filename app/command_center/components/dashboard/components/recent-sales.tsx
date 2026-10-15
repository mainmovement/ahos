import { ShieldCheck, AlertTriangle, CheckCircle2, Lock, Cpu } from 'lucide-react'

export function RecentSales() {
  return (
    <div className='space-y-6 text-slate-200'>
      <div className='flex items-center gap-4'>
        <div className='flex h-9 w-9 items-center justify-center rounded-full bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30'>
          <ShieldCheck className='h-4 w-4' />
        </div>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium text-white'>Lane B Security Gate</p>
            <p className='text-xs text-slate-400'>
              architecture/security/gate.py
            </p>
          </div>
          <div className='text-xs font-semibold px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'>
            PASS
          </div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <div className='flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'>
          <CheckCircle2 className='h-4 w-4' />
        </div>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium text-white'>Canonical Decision Authority</p>
            <p className='text-xs text-slate-400'>
              DecisionAdvisor pipeline sync
            </p>
          </div>
          <div className='text-xs font-semibold px-2.5 py-1 rounded bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/20'>
            BUY
          </div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <div className='flex h-9 w-9 items-center justify-center rounded-full bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30'>
          <Lock className='h-4 w-4' />
        </div>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium text-white'>Lane A Freeze Check</p>
            <p className='text-xs text-slate-400'>
              config/lane_a_freeze.sha256
            </p>
          </div>
          <div className='text-xs font-semibold px-2.5 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'>
            FROZEN
          </div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <div className='flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'>
          <Cpu className='h-4 w-4' />
        </div>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium text-white'>OpportunityScorer</p>
            <p className='text-xs text-slate-400'>
              Scored vector evaluation
            </p>
          </div>
          <div className='text-xs font-semibold px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700'>
            0.94 SCORE
          </div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <div className='flex h-9 w-9 items-center justify-center rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30'>
          <AlertTriangle className='h-4 w-4' />
        </div>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium text-white'>AI Advisor Downgrade</p>
            <p className='text-xs text-slate-400'>
              Advisory input constraint check
            </p>
          </div>
          <div className='text-xs font-semibold px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20'>
            NO OVERRIDE
          </div>
        </div>
      </div>
    </div>
  )
}
