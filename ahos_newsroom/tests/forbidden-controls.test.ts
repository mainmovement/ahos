/**
 * Source-level guard rail.
 *
 * The Newsroom is a *read-only* intelligence screen. This test walks every
 * source file and fails the build if a trading control, an approval verb or an
 * auto-trading hook ever appears in an identifier, prop name or handler.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const SRC = join(process.cwd(), 'src');
const TESTS = join(process.cwd(), 'tests');

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.(ts|tsx)$/.test(entry)) out.push(full);
  }
  return out;
}

const FILES = [...walk(SRC), ...walk(TESTS)].filter((f) => !f.endsWith('.test.ts') && !f.endsWith('.test.tsx'));

/**
 * Identifier-shaped forbidden tokens. These are checked against code, not
 * against prose, so documentation like "no buy/sell control exists" is allowed.
 */
const FORBIDDEN_IDENTIFIERS: { pattern: RegExp; why: string }[] = [
  { pattern: /\bon(Buy|Sell)\b/, why: 'buy/sell handler' },
  { pattern: /\bplaceOrder\b|\borderPlacement\b|\bsubmitOrder\b/, why: 'order placement' },
  { pattern: /\bexecuteTrade\b|\bexecuteOrder\b|\btradeOnNews\b/, why: 'trade execution' },
  { pattern: /\bapprove(Story|Trade|Signal)\b|\bhandleApprove\b/, why: 'approval control' },
  { pattern: /\boverride(Verdict|Decision)\b|\bhandleOverride\b/, why: 'judge override' },
  { pattern: /\benableTrading\b|\bactivateTrading\b|\bgoLiveTrading\b/, why: 'enable trading' },
  { pattern: /\bpositionSize\b|\bleverageSize\b|\briskCapital\b/, why: 'sizing control' },
  { pattern: /\btakeProfit\b|\bstopLoss\b|\borderType\b/, why: 'order parameters' },
  { pattern: /\bautoTrade\b|\bautoTrading\b|\btradeHook\b/, why: 'auto-trading hook' },
  { pattern: /\bbinance\w*Client\b|\bbroker(Client|Api)\b/i, why: 'broker/exchange client' },
  { pattern: /\bfetch\(['"]https?:/, why: 'outbound network call' },
  { pattern: /\baxios\b|\bnode-fetch\b/, why: 'http client dependency' },
];

/** Persian action words that must not appear on actionable controls. */
const FORBIDDEN_PERSIAN_ACTIONS = [
  'خرید',
  'فروش',
  'ثبت سفارش',
  'ارسال سفارش',
  'فعال‌سازی معاملات',
  'تأیید نهایی',
  'سیگنال خرید',
  'سیگنال فروش',
];

/** Lines that only *talk about* the prohibition are fine. */
const NEGATION = /(نمی‌شود|نمی‌کن|ممنوع|never|no |without|forbidden|allowed|مجاز نیست|خواندنی)/i;

describe('source guard rails', () => {
  it('finds the source tree', () => {
    expect(FILES.length).toBeGreaterThan(15);
  });

  it('contains no trading controls, approvals or auto-trading hooks', () => {
    const offences: string[] = [];
    for (const file of FILES) {
      const lines = readFileSync(file, 'utf8').split('\n');
      lines.forEach((line, index) => {
        if (NEGATION.test(line)) return;
        for (const { pattern, why } of FORBIDDEN_IDENTIFIERS) {
          if (pattern.test(line)) {
            offences.push(`${file.replace(process.cwd(), '.')}:${index + 1} [${why}] ${line.trim()}`);
          }
        }
      });
    }
    expect(offences, offences.join('\n')).toEqual([]);
  });

  it('never labels a button, link or aria-label with a trading verb', () => {
    const offences: string[] = [];
    for (const file of FILES) {
      const lines = readFileSync(file, 'utf8').split('\n');
      lines.forEach((line, index) => {
        const actionable =
          /<button|role="button"|<a\s|aria-label=|title=|>\{?ACTION\.|label:\s*'/.test(line);
        if (!actionable) return;
        if (NEGATION.test(line)) return;
        for (const word of FORBIDDEN_PERSIAN_ACTIONS) {
          if (line.includes(word)) {
            offences.push(
              `${file.replace(process.cwd(), '.')}:${index + 1} [${word}] ${line.trim().slice(0, 120)}`,
            );
          }
        }
      });
    }
    expect(offences, offences.join('\n')).toEqual([]);
  });

  it('keeps every data source behind the mock adapter package', () => {
    const outsideMock = FILES.filter(
      (file) =>
        !file.includes(`${'src'}/mock/`) &&
        /@\/mock\//.test(readFileSync(file, 'utf8')) === false &&
        /from '\.\.\/fixtures'|from '\.\/fixtures'/.test(readFileSync(file, 'utf8')),
    );
    expect(outsideMock).toEqual([]);
  });

  it('ships no API route, server action or edge function', () => {
    for (const file of FILES) {
      expect(file).not.toMatch(/src\/app\/api\//);
      const text = readFileSync(file, 'utf8');
      expect(text).not.toMatch(/'use server'/);
      expect(text).not.toMatch(/export (async )?function (GET|POST|PUT|DELETE)\s*\(/);
    }
  });
});
