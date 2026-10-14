'use client';

import type { Snap, News } from '@/dashboard_snapshot';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "Right: Live Intelligence Feed".
 *
 * The engine's own news items, in the order they arrived, with the importance
 * label the provider assigned. A missing Persian title falls back to the
 * original headline — never to an invented summary. Time-ago is computed from
 * `publishedAt`; an item without a timestamp shows no age rather than "now".
 */

function timeAgo(iso: string | null): string | null {
  if (!iso) return null;
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return null;
  const mins = Math.max(0, Math.round((Date.now() - then) / 60_000));
  if (mins < 1) return 'هم‌اکنون';
  if (mins < 60) return `${fa(mins)} دقیقه`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${fa(hrs)} ساعت`;
  return `${fa(Math.round(hrs / 24))} روز`;
}

function fa(n: number): string {
  return String(n).replace(/[0-9]/g, (c) => '۰۱۲۳۴۵۶۷۸۹'[Number(c)]);
}

function importanceTone(i: string): string {
  const s = i.toUpperCase();
  if (s.includes('HIGH') || s.includes('CRITICAL')) return 'border-[var(--ahos-status-rejected)]/45 text-[var(--ahos-status-rejected)]';
  if (s.includes('MEDIUM')) return 'border-primary/45 text-primary';
  return 'border-border/60 text-muted-foreground';
}

function Item({ news }: { news: News }) {
  const title = news.titleFa ?? news.titleOriginal;
  const ago = timeAgo(news.publishedAt);
  return (
    <li className='group relative border-b border-border/40 px-4 py-2.5 last:border-0'>
      <span
        aria-hidden
        className='absolute inset-y-0 start-0 w-px bg-transparent transition-colors group-hover:bg-primary/50'
      />
      <div className='flex items-center justify-between gap-2'>
        <div className='flex items-center gap-1.5'>
          <span
            className={`rounded-full border px-1.5 py-0.5 text-[9px] font-semibold uppercase ${importanceTone(news.importance)}`}
          >
            {news.importance}
          </span>
          <span className='text-[10px] text-muted-foreground'>{news.source}</span>
        </div>
        {ago ? <span className='font-mono text-[10px] tabular-nums text-muted-foreground/70'>{ago}</span> : null}
      </div>
      <p
        dir={news.titleFa ? 'rtl' : 'ltr'}
        className='mt-1 line-clamp-2 text-[11px] leading-relaxed text-foreground/90'
        title={title}
      >
        {title}
      </p>
      {news.summaryFa ? (
        <p dir='rtl' className='mt-0.5 line-clamp-1 text-[10px] text-muted-foreground'>
          {news.summaryFa}
        </p>
      ) : null}
    </li>
  );
}

export function IntelligenceFeed({ snap }: { snap: Snap | null }) {
  const items = snap?.news ?? [];

  return (
    <GlowCard glow='none' className='min-h-0'>
      <PanelTitle icon={<span className='text-accent'>◉</span>} hint={items.length ? `${fa(items.length)} مورد` : undefined}>
        جریانِ هوشِ زنده
      </PanelTitle>
      {items.length === 0 ? (
        <Waiting label={snap ? 'هنوز خبری رسیده نشده' : 'در انتظارِ داده'} className='h-52' />
      ) : (
        <ul className='max-h-80 overflow-y-auto pb-2'>
          {items.slice(0, 14).map((n) => (
            <Item key={n.id} news={n} />
          ))}
        </ul>
      )}
    </GlowCard>
  );
}
