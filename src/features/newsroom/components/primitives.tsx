'use client';

import type { ReactNode } from 'react';

/* -------------------------------------------------------------------------- */
/* Panel                                                                       */
/* -------------------------------------------------------------------------- */

export interface PanelProps {
  title: string;
  titleEn?: string;
  /** Right-side chips in the header (DEMO, counts, …). */
  chips?: ReactNode;
  /** Right-side actions (buttons). */
  actions?: ReactNode;
  /** `true` ⇒ striped DEMO ribbon under the header. */
  demo?: boolean;
  /** Hairline accent colour for the header: gold for the focal panel. */
  accent?: 'gold' | 'plain';
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  'data-testid'?: string;
}

export function Panel({
  title,
  titleEn,
  chips,
  actions,
  demo = false,
  accent = 'plain',
  children,
  className = '',
  bodyClassName = '',
  'data-testid': testId,
}: PanelProps) {
  return (
    <section
      data-testid={testId}
      className={`nw-panel flex min-h-0 flex-col ${accent === 'gold' ? 'nw-panel--gold' : ''} ${className}`}
    >
      <header
        className={[
          'flex shrink-0 flex-wrap items-center justify-between gap-x-2 gap-y-1 px-3 py-2',
          accent === 'gold' ? 'border-b border-nw-gold-hairline' : 'border-b border-nw-line-soft',
        ].join(' ')}
      >
        <div className="flex min-w-0 items-center gap-2">
          <span
            aria-hidden="true"
            className={`h-3 w-[2px] shrink-0 ${accent === 'gold' ? 'bg-nw-gold' : 'bg-nw-line'}`}
          />
          <h2 className="whitespace-nowrap text-[13px] font-semibold tracking-tight text-nw-text">
            {title}
          </h2>
          {titleEn ? <span className="nw-label hidden whitespace-nowrap 2xl:inline">{titleEn}</span> : null}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {chips}
          {actions}
        </div>
      </header>
      {demo ? (
        <div
          className="nw-demo-stripes h-[3px] w-full shrink-0"
          aria-hidden="true"
          data-demo-ribbon="true"
        />
      ) : null}
      <div className={`min-h-0 flex-1 ${bodyClassName}`}>{children}</div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Buttons                                                                     */
/* -------------------------------------------------------------------------- */

export interface GhostButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  title?: string;
  tone?: 'plain' | 'gold';
  active?: boolean;
  className?: string;
  'data-testid'?: string;
  'aria-label'?: string;
}

/** The only kind of button this page is allowed to have. */
export function GhostButton({
  children,
  onClick,
  disabled = false,
  title,
  tone = 'plain',
  active = false,
  className = '',
  'data-testid': testId,
  'aria-label': ariaLabel,
}: GhostButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      data-testid={testId}
      aria-label={ariaLabel}
      className={[
        'inline-flex items-center gap-1.5 rounded-[6px] border px-2 py-[5px]',
        'text-[12px] transition-colors duration-150',
        active
          ? tone === 'gold'
            ? 'border-nw-gold/60 bg-nw-gold/12 text-nw-gold-strong'
            : 'border-nw-line-strong bg-nw-surface-2 text-nw-text'
          : 'border-nw-line text-nw-text-dim hover:border-nw-line-strong hover:text-nw-text',
        disabled ? 'cursor-not-allowed opacity-45 hover:border-nw-line hover:text-nw-text-dim' : '',
        className,
      ].join(' ')}
    >
      {children}
    </button>
  );
}

export function IconButton({
  children,
  onClick,
  disabled,
  title,
  active = false,
  'data-testid': testId,
  'aria-label': ariaLabel,
}: Omit<GhostButtonProps, 'tone' | 'className'>) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      data-testid={testId}
      aria-label={ariaLabel}
      className={[
        'inline-flex h-6 w-6 items-center justify-center rounded-[6px] border transition-colors duration-150',
        active
          ? 'border-nw-gold/50 bg-nw-gold/10 text-nw-gold'
          : 'border-nw-line text-nw-text-dim hover:border-nw-line-strong hover:text-nw-text',
        disabled ? 'cursor-not-allowed opacity-45' : '',
      ].join(' ')}
    >
      {children}
    </button>
  );
}

/* -------------------------------------------------------------------------- */
/* State blocks                                                                */
/* -------------------------------------------------------------------------- */

export function StateBlock({
  title,
  body,
  tone = 'neutral',
  glyph,
  action,
}: {
  title: string;
  body?: string;
  tone?: 'neutral' | 'error' | 'unknown';
  glyph?: ReactNode;
  action?: ReactNode;
}) {
  const toneClass =
    tone === 'error'
      ? 'text-nw-danger'
      : tone === 'unknown'
        ? 'text-nw-unknown'
        : 'text-nw-text-faint';
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
      <div className={`${toneClass} opacity-80`}>{glyph}</div>
      <p className="text-[14px] font-medium text-nw-text-dim">{title}</p>
      {body ? <p className="max-w-[38ch] text-[12px] leading-relaxed text-nw-text-faint">{body}</p> : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2 p-3" data-testid="skeleton-rows">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex flex-col gap-1.5 rounded-[6px] border border-nw-line-soft p-2.5">
          <div className="h-2 w-1/3 rounded bg-nw-surface-3" />
          <div className="h-3 w-full rounded bg-nw-surface-3" />
          <div className="h-2 w-1/2 rounded bg-nw-surface-3" />
        </div>
      ))}
      <span className="sr-only">LOADING</span>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Data row                                                                    */
/* -------------------------------------------------------------------------- */

export function DataRow({
  label,
  children,
  className = '',
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-baseline justify-between gap-3 py-1 ${className}`}>
      <span className="nw-label shrink-0">{label}</span>
      <span className="min-w-0 text-right text-[12px] text-nw-text-dim">{children}</span>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Segmented control                                                           */
/* -------------------------------------------------------------------------- */

export interface SegmentOption<T extends string> {
  id: T;
  label: string;
  title?: string;
  disabled?: boolean;
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
  'data-testid': testId,
}: {
  options: readonly SegmentOption<T>[];
  value: T;
  onChange: (next: T) => void;
  label: string;
  'data-testid'?: string;
}) {
  return (
    <div role="group" aria-label={label} data-testid={testId} className="flex items-center gap-1">
      {options.map((option) => {
        const active = option.id === value;
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            disabled={option.disabled}
            title={option.title}
            aria-pressed={active}
            className={[
              'rounded-[6px] border px-2 py-[4px] text-[12px] transition-colors duration-150',
              active
                ? 'border-nw-gold/55 bg-nw-gold/12 text-nw-gold-strong'
                : 'border-nw-line text-nw-text-dim hover:border-nw-line-strong hover:text-nw-text',
              option.disabled ? 'cursor-not-allowed opacity-45 hover:border-nw-line' : '',
            ].join(' ')}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}