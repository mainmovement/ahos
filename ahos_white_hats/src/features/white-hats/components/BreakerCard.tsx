"use client";

import { StatusChip } from "@/components/truth/StatusChip";
import type { Breaker, PanelBodyState } from "../types";
import { Panel } from "./Panel";
import { RelTime } from "./RelTime";

export interface BreakerCardProps {
  breaker: Breaker;
  state: PanelBodyState;
  demo: boolean;
}

/**
 * Kill-switch & breaker card. ARMED / TRIPPED / UNKNOWN, with limits vs
 * current as neutral numbers and a thin bar — deliberately no green/red
 * anywhere in this card; only a TRIPPED state uses the danger tone.
 */
export function BreakerCard({ breaker, state, demo }: BreakerCardProps) {
  return (
    <Panel
      title="کلید توقف و فیوز"
      caption="Kill-switch / breaker"
      testId="breaker-card"
      demo={demo}
      badges={<StatusChip status={breaker.state} />}
      state={state}
    >
      {breaker.state !== "UNKNOWN" && breaker.updatedAt && (
        <p className="pb-2 text-[10.5px] text-mute">
          آخرین گزارش فیوز: <RelTime iso={breaker.updatedAt} />
        </p>
      )}
      {breaker.state === "UNKNOWN" && (
        <p className="pb-2 text-[10.5px] text-mute">
          وضعیت فیوز بدون گزارش معتبر «نامشخص» است — حدس زده نمی‌شود.
        </p>
      )}

      {breaker.limits.length === 0 ? (
        <p className="py-3 text-center text-[11.5px] text-mute">حدی ثبت نشده است.</p>
      ) : (
        <div className="flex flex-col gap-2.5" data-testid="breaker-limits">
          {breaker.limits.map((lim) => {
            const ratio = lim.limit > 0 ? Math.min(lim.current / lim.limit, 1) : 0;
            const exceeded = lim.current > lim.limit;
            return (
              <div key={lim.key}>
                <div className="flex items-baseline justify-between gap-2 text-[11px]">
                  <span className="text-dim">{lim.label}</span>
                  <span className="ah-num text-[11px] text-dim">
                    {lim.current.toLocaleString("en-US")}
                    <span className="mx-0.5 text-mute">{lim.unit}</span>
                    <span className="text-mute">/ {lim.limit.toLocaleString("en-US")}{lim.unit}</span>
                    {exceeded && (
                      <span className="ms-1.5 text-danger" title="از حد عبور کرده است">
                        بیش از حد
                      </span>
                    )}
                  </span>
                </div>
                {/* Neutral thin bar — grey track, sand fill; danger only on a real breach. */}
                <div className="mt-1 h-[3px] w-full overflow-hidden rounded-full bg-[color:rgba(236,236,231,0.06)]">
                  <div
                    className={`h-full rounded-full ${
                      exceeded
                        ? "bg-[color:var(--ah-danger)]"
                        : "bg-[color:var(--ah-sand)] opacity-70"
                    }`}
                    style={{ width: `${Math.round(ratio * 100)}%` }}
                    role="presentation"
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="pt-2.5 text-[9.5px] leading-5 text-mute">
        اعداد خنثی‌اند و رنگ خوب/بد ندارند؛ این صفحه فقط گزارش می‌کند، هیچ چیزی را تأیید یا بازنویسی نمی‌کند.
      </p>
    </Panel>
  );
}
