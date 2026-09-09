import {
  Blocks, Brain, ChartCandlestick, Cpu, Fingerprint, Newspaper,
  Radio, ShieldAlert, Sigma, Swords, type LucideIcon,
} from "lucide-react";
import type { TeamRow, Stance } from "@/lib/engine";
import type { Dict, Locale } from "@/lib/dict";
import { fmtInt, fmtPct } from "@/lib/format";
import { Badge } from "@/components/primitives";
import { cx, STANCE_TONE } from "@/lib/ui";

export const TEAM_ICONS: Record<string, LucideIcon> = {
  Sigma, ChartCandlestick, Blocks, ShieldAlert, Fingerprint,
  Newspaper, Radio, Cpu, Brain, Swords,
};

export function TeamAvatar({ team, size = 44 }: { team: TeamRow; size?: number }) {
  const Icon = TEAM_ICONS[team.icon] ?? Brain;
  return (
    <span
      className="relative inline-flex shrink-0 items-center justify-center rounded-2xl"
      style={{
        width: size, height: size,
        background: `linear-gradient(150deg, ${team.color}22, ${team.color}0a 60%, transparent)`,
        border: `1px solid ${team.color}45`,
        boxShadow: `inset 0 1px 0 ${team.color}30, 0 8px 24px -14px ${team.color}66`,
      }}
    >
      <Icon style={{ color: team.color, width: size * 0.45, height: size * 0.45 }} strokeWidth={1.8} />
      <span
        className="absolute -bottom-1 -end-1 grid size-4 place-items-center rounded-full text-[8px] font-black text-abyss-950"
        style={{ background: team.color }}
      >
        {team.teamId.slice(-1)}
      </span>
    </span>
  );
}

export function TeamCard({
  team, locale, dict, stance, compact = false,
}: {
  team: TeamRow; locale: Locale; dict: Dict; stance?: Stance | null; compact?: boolean;
}) {
  const acc = team.calls > 0 ? Math.round((team.correct / team.calls) * 100) : 0;
  const fa = locale === "fa";
  return (
    <div className="glass flex h-full flex-col gap-3 rounded-3xl p-5 panel-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <TeamAvatar team={team} />
          <div>
            <div className="text-sm font-extrabold text-frost">
              {fa ? team.nameFa : team.nameEn}
            </div>
            <div className="text-[11px] text-mist">{fa ? team.personaFa : team.personaEn}</div>
          </div>
        </div>
        {stance ? <Badge label={dict.stance[stance]} tone={STANCE_TONE[stance]} pulse={stance === "ALARM"} /> : null}
      </div>
      {!compact && (
        <p className="line-clamp-2 text-[11.5px] leading-5 text-mist">
          {fa ? team.specialtyFa : team.specialtyEn}
        </p>
      )}
      <div className="mt-auto space-y-1.5">
        <div className="flex items-center justify-between text-[10px] text-mist">
          <span>{dict.council.performance}</span>
          <span className="num text-frost/80">{fmtPct(locale, acc, false)}</span>
        </div>
        <div className="h-1 overflow-hidden rounded-full bg-white/5">
          <div
            className="bar-grow h-full rounded-full"
            style={{ width: `${acc}%`, background: `linear-gradient(90deg,${team.color}66,${team.color})` }}
          />
        </div>
        <div className="flex justify-between pt-0.5 text-[9.5px] text-mist/80">
          <span>{fmtInt(locale, team.calls)} {dict.council.calls}</span>
          <span>{fmtInt(locale, team.abstains)} {dict.council.abstain}</span>
        </div>
      </div>
    </div>
  );
}

export function DisagreementMeter({ value, label, locale }: { value: number; label: string; locale: Locale }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <span className="text-[11px] text-mist">{label}</span>
      <div className="relative h-1.5 w-28 overflow-hidden rounded-full bg-white/5">
        <div
          className={cx("bar-grow h-full rounded-full", pct > 55 ? "bg-flare" : pct > 30 ? "bg-gild-400" : "bg-jade-400")}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="num text-[11px] font-bold text-frost/90">{fmtPct(locale, pct, false)}</span>
    </div>
  );
}
