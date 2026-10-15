'use client';

import { useEffect, useState } from 'react';

/**
 * Tehran wall clock for the top bar (spec: "clock (Tehran)").
 *
 * Rendered client-side and hydrated from a zero-width server placeholder, so the
 * server markup never carries a time that is already wrong by the time it lands.
 * Asia/Tehran has no DST, so a fixed +03:30 offset is correct year-round.
 */

const TEHRAN_OFFSET_MIN = 3 * 60 + 30;

function tehranNow(): Date {
  const now = new Date();
  // Shift to Tehran once, in UTC terms, then read local parts from that Date.
  const utc = now.getTime() + now.getTimezoneOffset() * 60_000;
  return new Date(utc + TEHRAN_OFFSET_MIN * 60_000);
}

function tehranParts(d: Date) {
  const fa = new Intl.DateTimeFormat('fa-IR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
  const date = new Intl.DateTimeFormat('fa-IR', {
    weekday: 'short',
    day: '2-digit',
    month: 'short'
  });
  return { time: fa.format(d), date: date.format(d) };
}

export function TehranClock({ className }: { className?: string }) {
  const [parts, setParts] = useState<{ time: string; date: string } | null>(null);

  useEffect(() => {
    setParts(tehranParts(tehranNow()));
    const id = setInterval(() => setParts(tehranParts(tehranNow())), 1000);
    return () => clearInterval(id);
  }, []);

  if (!parts) {
    return <span className={className} aria-hidden style={{ visibility: 'hidden' }}>-</span>;
  }

  return (
    <span className={className} dir='ltr' title='Tehran — آسیا/تهران'>
      <span className='font-mono tabular-nums tracking-wide text-foreground'>{parts.time}</span>
      <span className='mx-1.5 text-muted-foreground/50'>|</span>
      <span className='text-muted-foreground'>{parts.date}</span>
    </span>
  );
}
