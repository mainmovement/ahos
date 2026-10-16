import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';

const search = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useSearchParams: () => search,
}));

vi.mock('@/mock/newsroom', () => ({
  newsroomAdapter: {
    id: 'mock:newsroom-fixtures',
    kind: 'mock' as const,
    load: async () => (await import('@/mock/newsroom/fixtures')).CALM_SNAPSHOT,
  },
}));

const { NewsroomPage } = await import('../NewsroomPage');
const { CALM_SNAPSHOT } = await import('@/mock/newsroom/fixtures');

/** Action words that must never appear on a read-only intelligence screen. */
const FORBIDDEN_TEXT = [
  /خرید/,
  /فروش/,
  /سفارش/,
  /ثبتِ? ?معامله/,
  /اهرم/,
  /موقعیت/,
  /سیگنالِ? ?معاملاتی/,
  /فعال[- ]?سازی معامله/,
  /\bbuy\b/i,
  /\bsell\b/i,
  /\bplace[- ]order\b/i,
  /\bapprove\b/i,
  /\boverride\b/i,
  /\benable[- ]trading\b/i,
  /\bexecute[- ]trade\b/i,
  /\bleverage\b/i,
  /\bposition[- ]size\b/i,
  /\btake[- ]profit\b/i,
  /\bstop[- ]loss\b/i,
];

async function renderPage() {
  render(<NewsroomPage />);
  await waitFor(() => expect(screen.getByTestId('story-inbox')).toBeInTheDocument());
}

beforeEach(() => {
  for (const key of [...search.keys()]) search.delete(key);
});

describe('Newsroom page — read-only contract', () => {
  it('renders the full shell', async () => {
    await renderPage();
    expect(screen.getByTestId('newsroom-topbar')).toBeInTheDocument();
    expect(screen.getByTestId('story-inbox')).toBeInTheDocument();
    expect(screen.getByTestId('story-dossier')).toBeInTheDocument();
    expect(screen.getByTestId('source-strip')).toBeInTheDocument();
    expect(screen.getByTestId('verification-pipeline')).toBeInTheDocument();
    expect(screen.getByTestId('conflict-board')).toBeInTheDocument();
    expect(screen.getByTestId('reporter-roster')).toBeInTheDocument();
    expect(screen.getByTestId('judge-handoff-tile')).toBeInTheDocument();
    expect(screen.getByTestId('telemetry-strip')).toBeInTheDocument();
    expect(screen.getByTestId('capsule-dock')).toBeInTheDocument();
  });

  it('shows the permanent PAPER_ONLY pill and the Tehran clock', async () => {
    await renderPage();
    expect(screen.getAllByTestId('paper-only-pill').length).toBeGreaterThan(0);
    expect(screen.getByTestId('tehran-clock')).toBeInTheDocument();
  });

  it('shows the focus copy: oil & gold only', async () => {
    await renderPage();
    expect(screen.getByTestId('focus-note')).toHaveTextContent('فقط نفت و طلا');
  });

  it('has no forbidden control anywhere in the DOM', async () => {
    const { container } = render(<NewsroomPage />);
    await waitFor(() => expect(screen.getByTestId('story-inbox')).toBeInTheDocument());

    const interactive = [...container.querySelectorAll('button, a[href], [role="button"]')];
    expect(interactive.length).toBeGreaterThan(5);

    for (const el of interactive) {
      const text = (el.textContent ?? '').replace(/\s+/g, ' ');
      for (const forbidden of FORBIDDEN_TEXT) {
        expect(text, `forbidden control text on <${el.tagName}>: ${text}`).not.toMatch(forbidden);
      }
    }
  });

  it('offers only view / filter / copy-id / export-read-only actions in the handoff tile', async () => {
    await renderPage();
    const tile = screen.getByTestId('judge-handoff-tile');
    const labels = [...tile.querySelectorAll('button')].map((b) => (b.textContent ?? '').trim());
    expect(labels).toEqual(
      expect.arrayContaining(['گشودنِ مدرک', 'رونوشتِ شناسه', 'خروجیِ فقط‌خواندنی']),
    );
    for (const label of labels) {
      expect(label).not.toMatch(/تأیید نهایی|رد کردن|ارسال به معامله|فعال‌سازی/);
    }
  });

  it('never colours a story as trade advice', async () => {
    const { container } = render(<NewsroomPage />);
    await waitFor(() => expect(screen.getByTestId('story-inbox')).toBeInTheDocument());
    for (const card of container.querySelectorAll('[data-testid^="story-card-"]')) {
      expect(card.className).not.toMatch(/text-ah-live|text-ah-danger/);
    }
  });
});

describe('Newsroom page — truth rules in the UI', () => {
  it('excludes DEMO from the verified counter', async () => {
    await renderPage();
    const inbox = screen.getByTestId('story-inbox');
    // 3 fixture stories pass the two-source rule; the DEMO row never counts.
    expect(within(inbox).getByText('3 VERIFIED')).toBeInTheDocument();
    expect(within(inbox).getByText('1 DEMO')).toBeInTheDocument();
  });

  it('shows the two-source rule on the source strip of a single-source story', async () => {
    await renderPage();
    const partial = screen.getByTestId('story-card-nws-gold-0099');
    partial.click();
    await waitFor(() =>
      expect(screen.getByTestId('source-strip')).toHaveTextContent('هرگز «VERIFIED» نیست'),
    );
  });

  it('never shows VERIFIED for a story with an open conflict', async () => {
    await renderPage();
    screen.getByTestId('story-card-nws-oil-0143').click();
    await waitFor(() => expect(screen.getByTestId('story-dossier')).toHaveTextContent('CONFLICT'));
    expect(screen.getByTestId('story-dossier')).not.toHaveTextContent('VERIFIED');
  });

  it('lists conflict claim A and claim B without resolving them', async () => {
    await renderPage();
    const board = screen.getByTestId('conflict-board');
    expect(within(board).getAllByTestId('claim-A').length).toBe(2);
    expect(within(board).getAllByTestId('claim-B').length).toBe(2);
    expect(board).toHaveTextContent('حل خودکار ممنوع');
    expect(board.querySelectorAll('[data-status="CONFLICT"]').length).toBeGreaterThan(0);
  });

  it('renders UNKNOWN rows in grey in the reporter roster', async () => {
    const { container } = render(<NewsroomPage />);
    await waitFor(() => expect(screen.getByTestId('reporter-roster')).toBeInTheDocument());
    const unknownRow = container.querySelector('[data-testid="reporter-row-rpt-wire-02"]');
    expect(unknownRow).not.toBeNull();
    expect(unknownRow?.querySelector('[data-tone="unknown"]')).not.toBeNull();
    expect(unknownRow?.textContent).toContain('ناموجود');
  });
});

describe('Newsroom page — market focus', () => {
  it('activates oil and gold', async () => {
    await renderPage();
    expect(screen.getByTestId('market-pill-OIL')).toHaveAttribute('data-connected', 'true');
    expect(screen.getByTestId('market-pill-GOLD')).toHaveAttribute('data-connected', 'true');
  });

  it('marks crypto and equities as «متصل نیست» / PLANNED with no invented count', async () => {
    await renderPage();
    for (const id of ['CRYPTO', 'EQUITIES']) {
      const pill = screen.getByTestId(`market-pill-${id}`);
      expect(pill).toHaveAttribute('data-connected', 'false');
      expect(pill).toHaveAttribute('aria-disabled', 'true');
      expect(pill).toHaveTextContent('متصل نیست');
      expect(pill).toHaveTextContent('PLANNED');
      expect(pill).toHaveTextContent('—');
      expect(pill).not.toHaveTextContent(/[1-9]/);
    }
  });

  it('has zero headlines for disconnected markets', async () => {
    await renderPage();
    const disconnected = CALM_SNAPSHOT.markets.filter((m) => !m.connected).map((m) => m.id);
    for (const id of disconnected) {
      expect(CALM_SNAPSHOT.stories.filter((s) => s.market === id)).toHaveLength(0);
    }
  });
});

describe('Newsroom page — DEMO surfaces', () => {
  it('marks every mock-backed panel with the DEMO ribbon', async () => {
    const { container } = render(<NewsroomPage />);
    await waitFor(() => expect(screen.getByTestId('story-inbox')).toBeInTheDocument());
    // inbox · dossier · source strip · pipeline · conflicts · roster · handoff
    expect(container.querySelectorAll('[data-demo-ribbon="true"]').length).toBeGreaterThanOrEqual(7);
  });

  it('shows the page-level DEMO chip because the adapter is a mock', async () => {
    await renderPage();
    expect(screen.getByTestId('page-truth-chip')).toHaveAttribute('data-status', 'DEMO');
  });
});
