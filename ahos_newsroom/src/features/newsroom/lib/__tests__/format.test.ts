import { describe, expect, it } from 'vitest';

import {
  MISSING,
  MISSING_FA,
  formatClockFa,
  formatRatio,
  formatStampFa,
  formatTimeFa,
  freshnessBucket,
  orMissing,
  parseIso,
  toPersianDigits,
} from '../format';

const NOW = '2026-10-16T12:00:00.000+03:30';

describe('digits and placeholders', () => {
  it('converts Latin digits to Persian digits', () => {
    expect(toPersianDigits(1234)).toBe('۱۲۳۴');
    expect(toPersianDigits('v0.1')).toBe('v۰.۱');
    expect(toPersianDigits('nws-oil-0142')).toBe('nws-oil-۰۱۴۲');
  });

  it('never renders a missing value as a number', () => {
    expect(formatTimeFa(null)).toBe(MISSING);
    expect(formatStampFa(null)).toBe(MISSING_FA);
    expect(orMissing(null)).toBe('—');
    expect(formatRatio(null, null)).toBe('—');
    expect(formatRatio(4, 7)).toBe('۴/۷');
  });

  it('rejects unparseable timestamps instead of guessing', () => {
    expect(parseIso('not-a-date')).toBeNull();
    expect(parseIso(null)).toBeNull();
    expect(parseIso(NOW)?.toISOString()).toBe('2026-10-16T08:30:00.000Z');
  });
});

describe('Tehran wall clock', () => {
  it('formats times in Tehran (+03:30) regardless of host timezone', () => {
    expect(formatTimeFa('2026-10-16T11:52:00.000+03:30')).toBe('۱۱:۵۲');
    // Same instant expressed in UTC must produce the same Tehran wall time.
    expect(formatTimeFa('2026-10-16T08:22:00.000Z')).toBe('۱۱:۵۲');
  });

  it('formats the live clock with seconds', () => {
    expect(formatClockFa(new Date('2026-10-16T08:30:00.000Z'))).toBe('۱۲:۰۰:۰۰');
  });
});

describe('freshness', () => {
  it('buckets by age against the snapshot clock', () => {
    expect(freshnessBucket('2026-10-16T11:52:00.000+03:30', NOW)).toBe('FRESH');
    expect(freshnessBucket('2026-10-16T11:36:00.000+03:30', NOW)).toBe('RECENT');
    expect(freshnessBucket('2026-10-16T08:50:00.000+03:30', NOW)).toBe('AGING');
    expect(freshnessBucket('2026-10-15T08:00:00.000+03:30', NOW)).toBe('STALE');
  });

  it('is UNKNOWN without a timestamp or without a reference clock', () => {
    expect(freshnessBucket(null, NOW)).toBe('UNKNOWN');
    expect(freshnessBucket('2026-10-16T11:52:00.000+03:30', null)).toBe('UNKNOWN');
  });

  it('is UNKNOWN for timestamps in the future instead of pretending they are fresh', () => {
    expect(freshnessBucket('2026-10-17T11:52:00.000+03:30', NOW)).toBe('UNKNOWN');
  });
});
