"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { MissingValue, TruthChip } from '@/src/features/newsroom/truth';
import { PANEL, REPORTER_ROLE_LABEL_EN, REPORTER_ROLE_LABEL_FA } from '@/src/features/newsroom/lib/labels';
import { formatRatio, formatRelativeFa, formatTimeFa } from '@/src/features/newsroom/lib/format';
import type { ReporterAgent } from '@/src/features/newsroom/lib/types';
import { Panel } from './primitives';

function AttemptBar({ agent }: { agent: ReporterAgent }) {
  if (agent.attempts === null || agent.pass === null || agent.attempts <= 0) {
    return (
      <span className="nw-mono text-[12px] text-nw-unknown" title={tr("fa", "newsroom.ui.ReporterRoster_1")}>
        <MissingValue />
      </span>
    );
  }
  const ratio = agent.pass / agent.attempts;
  return (
    <span className="inline-flex items-center gap-1.5" title={trf("newsroom.fmt.passOf", { pass: agent.pass ?? "—", attempts: agent.attempts ?? "—" })}>
      <span className="relative inline-block h-[4px] w-12 overflow-hidden rounded-full bg-nw-line">
        <span
          className="absolute inset-y-0 right-0 rounded-full bg-nw-cyan/70"
          style={{ width: `${Math.round(ratio * 100)}%` }}
        />
      </span>
      <span className="nw-mono text-[12px] text-nw-text-dim">
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
      chips={<span className="nw-mono text-[12px] text-nw-text-faint">{trf("newsroom.fmt.agentsN", { n: reporters.length })}</span>}
      bodyClassName="nw-scroll min-h-0 overflow-auto"
    >
      <ul data-testid="reporter-list">
        {reporters.map((agent) => (
          <li
            key={agent.id}
            className="flex items-center justify-between gap-2 border-b border-nw-line-soft/70 px-2.5 py-2 last:border-b-0"
            data-testid={`reporter-row-${agent.id}`}
            data-status={agent.status}
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-[12px] text-nw-text" title={agent.nameFa}>
                  {agent.nameFa}
                </span>
                <span className="shrink-0 rounded-[4px] border border-nw-line px-1 py-[1px] font-nw-en text-[12px] tracking-[0.1em] text-nw-text-faint">
                  {REPORTER_ROLE_LABEL_EN[agent.role]}
                  <span className="ms-1 font-nw-fa tracking-normal">{REPORTER_ROLE_LABEL_FA[agent.role]}</span>
                </span>
              </div>
              <p className="mt-0.5 truncate font-nw-en text-[12px] text-nw-text-faint">{agent.codeEn}</p>
            </div>

            <div className="flex shrink-0 flex-col items-end gap-1">
              <div className="flex items-center gap-1.5">
                <AttemptBar agent={agent} />
                <TruthChip status={agent.status} size="xs" />
              </div>
              <span className="nw-mono text-[12px] text-nw-text-faint" title={agent.noteFa ?? ''}>
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