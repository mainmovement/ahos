import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { PaperOnlyGuard, PaperOnlyPill } from '../components/PaperOnlyGuard';
import { CALM_SNAPSHOT, VIOLATION_SNAPSHOT } from '@/mock/newsroom';
import type { NewsroomSnapshot } from '../lib/types';

function snapshotWith(overrides: Partial<NewsroomSnapshot>): NewsroomSnapshot {
  return { ...CALM_SNAPSHOT, ...overrides };
}

describe('PaperOnlyGuard', () => {
  it('shows no VIOLATION bar for a compliant paper-only snapshot', () => {
    render(
      <PaperOnlyGuard snapshot={CALM_SNAPSHOT}>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    expect(screen.queryByTestId('violation-bar')).not.toBeInTheDocument();
    expect(screen.getByTestId('paper-only-guard')).toHaveAttribute('data-violation', 'false');
  });

  it('shows the VIOLATION bar when realTrading is true', () => {
    render(
      <PaperOnlyGuard snapshot={snapshotWith({ realTrading: true })}>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    const bar = screen.getByTestId('violation-bar');
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute('role', 'alert');
    expect(bar).toHaveTextContent('realTrading=true');
    expect(bar).toHaveTextContent('executionMode=PAPER_ONLY');
  });

  it('shows the VIOLATION bar when executionMode is not PAPER_ONLY', () => {
    render(
      <PaperOnlyGuard snapshot={snapshotWith({ executionMode: 'LIVE' })}>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    expect(screen.getByTestId('violation-bar')).toHaveTextContent('executionMode=LIVE');
  });

  it('shows the VIOLATION bar for the shipped violation fixture', () => {
    render(
      <PaperOnlyGuard snapshot={VIOLATION_SNAPSHOT}>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    expect(screen.getByTestId('violation-bar')).toBeInTheDocument();
  });

  it('can be forced with the demo query flag', () => {
    render(
      <PaperOnlyGuard snapshot={CALM_SNAPSHOT} forced>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    expect(screen.getByTestId('violation-bar')).toHaveAttribute('data-forced', 'true');
  });

  it('offers no control inside the violation bar', () => {
    render(
      <PaperOnlyGuard snapshot={VIOLATION_SNAPSHOT}>
        <div>page</div>
      </PaperOnlyGuard>,
    );
    expect(screen.getByTestId('violation-bar').querySelectorAll('button')).toHaveLength(0);
  });

  it('still renders the page behind the bar', () => {
    render(
      <PaperOnlyGuard snapshot={VIOLATION_SNAPSHOT}>
        <div>page-content</div>
      </PaperOnlyGuard>,
    );
    expect(screen.getByText('page-content')).toBeInTheDocument();
  });
});

describe('PaperOnlyPill', () => {
  it('is permanent and non-dismissible', () => {
    render(<PaperOnlyPill />);
    const pill = screen.getByTestId('paper-only-pill');
    expect(pill).toHaveTextContent('فقط کاغذی');
    expect(pill).toHaveTextContent('PAPER_ONLY');
    expect(pill.tagName).not.toBe('BUTTON');
    expect(pill.closest('button')).toBeNull();
  });
});
