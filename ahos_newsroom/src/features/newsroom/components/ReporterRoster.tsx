'use client';

import { MissingValue, TruthChip } from '@/components/truth';
import { PANEL, REPORTER_ROLE_LABEL_EN, REPORTER_ROLE_LABEL_FA } from '@/features/newsroom/lib/labels';
import { formatRatio, formatRelativeFa, formatTimeFa } from '@/features/newsroom/lib/format';
import type { ReporterAgent } from '@/features/newsroom/lib/types';
import { Panel } from './primitives';

function AttemptBar({ agent }: { agent: ReporterAgent }) {
  if (agent.attempts === null || agent.pass === null || agent.attempts <= 0) {
    return (
      <span className="ah-mono text-[10px] text-ah-unknown" title="شمارنده اندازه‌گیری نشده">
        <MissingValue />
      </span>
    );
  }
  const ratio = agent.pass / agent.attempts;
  return (
    <span className="inline-flex items-center gap-1.5" title={`موفق ${agent.pass} از ${agent.attempts}`}>
      <span className="relative inline-block h-[4px] w-12 overflow-hidden rounded-full bg-ah-line">
        <span
          className="absolute inset-y-0 right-0 rounded-full bg-ah-cyan/70"
          style={{ width: `${Math.round(ratio * 100)}%` }}
        />
      </span>
      <span className="ah-mono text-[10px] text-ah-text-dim">
        {formatRatio(agent.pass, agent.attempts)}
      </span>
    </span>
  );
}

export interface ReporterRosterProps {
  reporters: readonly ReporterAgent[];
  nowIso: string | null;
  demo: boolean;
  className?: string;
}

export function ReporterRoster({ reporters, nowIso, demo, className = '' }: ReporterRosterProps) {
  return (
    <Panel
      title={PANEL.reporters}
      titleEn="REPORTER ROSTER"
      demo={demo}
      data-testid="reporter-roster"
      className={className}
      chips={<span className="ah-mono text-[10px] text-ah-text-faint">{reporters.length} عامل</span>}
      bodyClassName="ah-scroll min-h-0 overflow-auto"
    >
      <ul data-testid="reporter-list">
        {reporters.map((agent) => (
          <li
            key={agent.id}
            className="flex items-center justify-between gap-2 border-b border-ah-line-soft/70 px-2.5 py-2 last:border-b-0"
            data-testid={`reporter-row-${agent.id}`}
            data-status={agent.status}
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-[11.5px] text-ah-text" title={agent.nameFa}>
                  {agent.nameFa}
                </span>
                <span className="shrink-0 rounded-[4px] border border-ah-line px-1 py-[1px] font-ah-en text-[8.5px] tracking-[0.1em] text-ah-text-faint">
                  {REPORTER_ROLE_LABEL_EN[agent.role]}
                  <span className="ms-1 font-ah-fa tracking-normal">{REPORTER_ROLE_LABEL_FA[agent.role]}</span>
                </span>
              </div>
              <p className="mt-0.5 truncate font-ah-en text-[9.5px] text-ah-text-faint">{agent.codeEn}</p>
            </div>

            <div className="flex shrink-0 flex-col items-end gap-1">
              <div className="flex items-center gap-1.5">
                <AttemptBar agent={agent} />
                <TruthChip status={agent.status} size="xs" />
              </div>
              <span className="ah-mono text-[9.5px] text-ah-text-faint" title={agent.noteFa ?? ''}>
                {agent.lastRunAt ? (
                  <>
                    {formatTimeFa(agent.lastRunAt)} · {formatRelativeFa(agent.lastRunAt, nowIso)}
                  </>
                ) : (
                  <MissingValue fa />
                )}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export default ReporterRoster;
