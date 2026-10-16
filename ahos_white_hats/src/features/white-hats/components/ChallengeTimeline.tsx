"use client";

import { StatusChip } from "@/components/truth/StatusChip";
import type { Decision, PanelBodyState, TimelineEvent } from "../types";
import { CopyIdButton } from "./CopyIdButton";
import { EyeIcon } from "./icons";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface ChallengeTimelineProps {
  decision: Decision | null;
  events: TimelineEvent[];
  state: PanelBodyState;
  demo: boolean;
  onOpenEvidence: (id: string) => void;
}

const KIND_LABEL: Record<TimelineEvent["kind"], string> = {
  proposer: "پیشنهاددهنده",
  reporter: "منبع (گزارشگر)",
  council: "نظر شورا",
  judge: "چالش ناظر",
  verdict: "حکم",
};

const KIND_GLYPH: Record<TimelineEvent["kind"], string> = {
  proposer: "▲",
  reporter: "◉",
  council: "▣",
  judge: "⚖",
  verdict: "●",
};

/**
 * Vertical challenge timeline for the selected decision:
 * proposer → reporters (sources) → council opinions → judge challenge →
 * verdict, with every recorded reason attached to its step.
 */
export function ChallengeTimeline({
  decision,
  events,
  state,
  demo,
  onOpenEvidence,
}: ChallengeTimelineProps) {
  return (
    <Panel
      title="خط زمانی چالش"
      caption="Challenge timeline"
      testId="challenge-timeline"
      demo={demo || (decision?.demo ?? false)}
      state={state}
      badges={
        decision ? (
          <span className="flex items-center gap-1.5">
            <span className="ah-chip ah-tone-grey">
              <span className="ah-latin text-[8.5px] opacity-70">{decision.market}</span>
            </span>
            <StatusChip status={decision.verdict} />
          </span>
        ) : null
      }
    >
      {decision ? (
        <>
          <div className="flex items-center gap-2 pb-3 text-[11px] text-mute">
            <span>تصمیم انتخاب‌شده:</span>
            <span className="ah-id text-dim">{decision.id}</span>
            <CopyIdButton value={decision.id} />
          </div>

          <ol className="relative flex flex-col gap-4 border-s border-line ps-4" data-testid="timeline-events">
            {events.map((ev) => (
              <li
                key={ev.id}
                data-demo={ev.demo ? "true" : "false"}
                className={`relative ${ev.demo ? "ah-demo-stripes rounded-md" : ""}`}
              >
                <span
                  className="absolute top-[7px] grid size-[13px] place-items-center rounded-full border border-linestrong bg-surface text-[8px] text-gold"
                  style={{ insetInlineStart: -21.5 }}
                  aria-hidden="true"
                >
                  {KIND_GLYPH[ev.kind]}
                </span>

                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="ah-chip ah-tone-cyan">
                    <span>{KIND_LABEL[ev.kind]}</span>
                  </span>
                  <span className="text-[11.5px] font-medium text-ink">{ev.title}</span>
                  {ev.kind === "verdict" && ev.verdict && (
                    <StatusChip status={ev.verdict} />
                  )}
                  {ev.rejected && <StatusChip status="REJECTED" />}
                  {ev.demo && <StatusChip status="DEMO" />}
                  <span className="ms-auto text-[9.5px] text-mute">
                    <RelTime iso={ev.at} />
                  </span>
                </div>

                <p className="mt-1 text-[11px] leading-6 text-dim">{ev.detail}</p>

                {ev.actor && (
                  <p className="mt-0.5 text-[9.5px] text-mute">
                    کنشگر: <span className="text-dim/90">{ev.actor}</span>
                  </p>
                )}

                {ev.reasons && ev.reasons.length > 0 && (
                  <div className="mt-1.5 border-s-2 border-[color:rgba(217,185,119,0.25)] ps-2.5">
                    <span className="text-[9.5px] text-mute">دلایل ثبت‌شده:</span>
                    <ul className="mt-0.5 flex flex-col gap-0.5">
                      {ev.reasons.map((r, i) => (
                        <li key={i} className="text-[10.5px] leading-5 text-dim/90">
                          — {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {ev.evidenceId && (
                  <button
                    type="button"
                    className="ah-focus mt-1.5 inline-flex items-center gap-1 rounded-sm border border-line px-1.5 py-[1px] text-[10px] text-cyan/90 transition-colors hover:border-linestrong hover:text-gold"
                    onClick={() => onOpenEvidence(ev.evidenceId as string)}
                    aria-label={`مشاهده شواهد ${ev.evidenceId}`}
                  >
                    <EyeIcon />
                    <span className="ah-id">{ev.evidenceId}</span>
                  </button>
                )}
              </li>
            ))}
          </ol>

          {events.length === 0 && (
            <p className="py-4 text-center text-[11.5px] text-mute" data-testid="timeline-empty">
              رویدادی ثبت نشده — حکم این تصمیم «نامشخص» می‌ماند.
            </p>
          )}
        </>
      ) : null}
    </Panel>
  );
}
