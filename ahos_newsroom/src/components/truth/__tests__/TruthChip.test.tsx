import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { TruthChip } from '../TruthChip';
import { MissingValue } from '../index';
import { COMPONENT_STATES, TRUTH_STATUSES } from '@/features/newsroom/lib/truth';

describe('TruthChip', () => {
  it('renders UNKNOWN in grey — never in the live/green tone', () => {
    render(<TruthChip status="UNKNOWN" data-testid="chip" />);
    const chip = screen.getByTestId('chip');
    expect(chip.className).toContain('text-ah-unknown');
    expect(chip.className).not.toContain('text-ah-live');
    expect(chip.className).not.toContain('text-ah-cyan');
    expect(chip.getAttribute('data-tone')).toBe('unknown');
  });

  it('renders every non-LIVE status outside the live tone', () => {
    for (const status of TRUTH_STATUSES) {
      const { container, unmount } = render(<TruthChip status={status} />);
      const chip = container.querySelector('[data-tone]');
      if (status !== 'LIVE') {
        expect(chip?.className).not.toContain('text-ah-live');
      }
      unmount();
    }
  });

  it('keeps component states (PLANNED / UNAVAILABLE / MISSING) grey too', () => {
    for (const state of ['PLANNED', 'UNAVAILABLE', 'MISSING'] as const) {
      const { container, unmount } = render(<TruthChip status={state} />);
      const chip = container.querySelector('[data-tone]');
      expect(chip?.className).not.toContain('text-ah-live');
      unmount();
    }
    expect(COMPONENT_STATES).toContain('PLANNED');
  });

  it('always shows the English status code', () => {
    render(<TruthChip status="UNKNOWN" showFa />);
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
    expect(screen.getByText('نامعلوم')).toBeInTheDocument();
  });

  it('draws the diagonal DEMO ribbon', () => {
    render(<TruthChip status="DEMO" data-testid="chip" />);
    expect(screen.getByTestId('chip').className).toContain('ah-demo-stripes');
  });

  it('does not put the DEMO ribbon on other statuses', () => {
    render(<TruthChip status="LIVE" data-testid="chip" />);
    expect(screen.getByTestId('chip').className).not.toContain('ah-demo-stripes');
  });

  it('renders LIVE with the live tone', () => {
    render(<TruthChip status="LIVE" data-testid="chip" />);
    const chip = screen.getByTestId('chip');
    expect(chip.className).toContain('text-ah-live');
    expect(chip.getAttribute('data-tone')).toBe('live');
  });
});

describe('MissingValue', () => {
  it('renders «—» and «ناموجود», never 0', () => {
    const { container, unmount } = render(<MissingValue />);
    expect(container.textContent).toBe('—');
    expect(container.textContent).not.toBe('0');
    unmount();

    render(<MissingValue fa />);
    expect(screen.getByText('ناموجود')).toBeInTheDocument();
  });
});
