'use client';

import type { Snap, Opp } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "Live Market Scan table".
 *
 * Rows are the snapshot's own opportunities in the order the engine produced
 * them, capped for the overview. The table renders what the canonical layer
 * decided; it never re-scores, re-ranks for display beyond the engine's own
 * rankScore, and a row with no reading shows a muted dash rather than a guess.
 */
const MAX_ROWS = 9;

function stateTone(state: string | null | undefined): string {
  const s = (state ?? '').toUpperCase();
  if (s.includes('PASS') || s.includes('VERIFIED')) return 'text-[var(--ahos-status-verified)]';
  if (s.includes('REJECT')) return 'text-[var(--ahos-status-rejected)]';
  if (s.includes('CONFLICT')) return 'text-[var(--ahos-status-conflict)]';
  if (s.includes('STALE')) return 'text-[var(--ahos-status-stale)]';
  return 'text-[var(--ahos-status-unknown)]';
}

function Row({ opp }: { opp: Opp }) {
  const security = opp.securityState ?? opp.securityStatus ?? null;
  const coverage = opp.evidenceCoverage;
  return (
    <TableRow className='border-border/40 hover:bg-muted/30'>
      <TableCell className='py-2'>
        <div className='flex flex-col'>
          <span dir='ltr' className='font-mono text-xs font-semibold text-foreground'>
            {opp.symbol}
          </span>
          {opp.name ? (
            <span className='truncate text-[10px] text-muted-foreground' title={opp.name}>
              {opp.name}
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className='py-2 text-[11px] text-muted-foreground'>{opp.chain}</TableCell>
      <TableCell className={`py-2 text-[11px] font-medium ${stateTone(security)}`}>
        {security ?? '—'}
      </TableCell>
      <TableCell dir='ltr' className='py-2 text-end font-mono text-xs tabular-nums text-foreground/90'>
        {faNum(opp.rankScore, 1)}
      </TableCell>
      <TableCell className='py-2 text-[11px] text-muted-foreground'>{opp.confidence ?? '—'}</TableCell>
      <TableCell dir='ltr' className='py-2 text-end'>
        {coverage === null || coverage === undefined ? (
          <span className='text-muted-foreground/60'>—</span>
        ) : (
          <span className='inline-flex items-center gap-1.5'>
            <span className='h-1 w-12 overflow-hidden rounded-full bg-muted'>
              <span
                className='block h-full rounded-full bg-gradient-to-l from-primary/70 to-accent/70'
                style={{ width: `${Math.min(100, Math.max(0, coverage))}%` }}
              />
            </span>
            <span className='font-mono text-[10px] tabular-nums text-muted-foreground'>
              {faNum(coverage, 0)}٪
            </span>
          </span>
        )}
      </TableCell>
    </TableRow>
  );
}

export function MarketScan({ snap }: { snap: Snap | null }) {
  const rows = snap?.opportunities?.slice(0, MAX_ROWS) ?? [];
  const total = snap?.opportunities?.length ?? 0;

  return (
    <GlowCard glow='none'>
      <PanelTitle icon={<span className='text-primary'>▤</span>} hint={total ? `${faNum(total, 0)} فرصت` : undefined}>
        پایشِ زندهٔ بازار
      </PanelTitle>
      {rows.length === 0 ? (
        <Waiting label={snap ? 'هنوز فرصتی یافت نشده' : 'در انتظارِ داده'} className='h-48' />
      ) : (
        <div className='px-2 pb-2'>
          <Table>
            <TableHeader>
              <TableRow className='border-border/40 text-[10px] uppercase tracking-wider text-muted-foreground'>
                <TableHead className='h-8 py-1'>نماد</TableHead>
                <TableHead className='h-8 py-1'>زنجیره</TableHead>
                <TableHead className='h-8 py-1'>دروازهٔ امنیت</TableHead>
                <TableHead className='h-8 py-1 text-end'>امتیاز</TableHead>
                <TableHead className='h-8 py-1'>اعتماد</TableHead>
                <TableHead className='h-8 py-1 text-end'>پوششِ شواهد</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>{rows.map((opp) => (
              <Row key={opp.id} opp={opp} />
            ))}</TableBody>
          </Table>
        </div>
      )}
    </GlowCard>
  );
}
