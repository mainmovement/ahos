"use client";

/**
 * Domain status chips. Each semantic class has its own icon SHAPE (AGENT_18
 * trust-interface taxonomy) — colour is secondary. Forbidden equivalences are
 * respected: REGISTERED ≠ OPERATIONAL, PLANNED ≠ LIVE, UNKNOWN ≠ VERIFIED.
 */
import {
  Ban,
  BadgeCheck,
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleDot,
  CircleHelp,
  CircleMinus,
  CirclePause,
  CircleSlash,
  CircleX,
  ClockAlert,
  Clock,
  Eye,
  FileText,
  Fingerprint,
  FlaskConical,
  Gauge,
  Hourglass,
  Info,
  KeyRound,
  Lock,
  OctagonAlert,
  Package,
  PackageOpen,
  PencilRuler,
  Play,
  ScanSearch,
  ScrollText,
  SearchX,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  SignalHigh,
  SignalLow,
  SignalMedium,
  Split,
  Timer,
  TriangleAlert,
  Unplug,
  User,
  Users,
} from "lucide-react";
import type {
  AgentRuntimeState,
  AlertTier,
  CanonicalOutcome,
  Confidence,
  DataMeta,
  DataStatus,
  IdentityState,
  ImplementationStatus,
  ProviderHealthStatus,
  SecurityGateState,
  Severity,
  TriState,
  VerificationKind,
  VerificationState,
  VerificationStatus,
} from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useNow } from "@/lib/time/now";
import { Chip, type ChipTone } from "./chip";
import { Tip } from "./tooltip";

type IconT = typeof CircleDot;

/* ---------------------------------------------------------- data status */

const DATA: Record<DataStatus, { icon: IconT; tone: ChipTone }> = {
  LIVE: { icon: CircleDot, tone: "up" },
  STALE: { icon: Clock, tone: "warn" },
  UNKNOWN: { icon: CircleHelp, tone: "violet" },
  UNAVAILABLE: { icon: CircleSlash, tone: "down" },
  DEMO: { icon: FlaskConical, tone: "demo" },
};

/**
 * Never fake LIVE: a LIVE payload older than its TTL is downgraded to STALE,
 * and a missing timestamp is downgraded to UNKNOWN.
 */
export function resolveStatus(status: DataStatus, retrievedAt: string | null, ttlSec: number | undefined, now: number | null): DataStatus {
  if (status !== "LIVE") return status;
  if (!retrievedAt) return "UNKNOWN";
  if (ttlSec && now !== null && now - new Date(retrievedAt).getTime() > ttlSec * 1000) return "STALE";
  return status;
}

export function StatusChip({ status, size = "xs", showLabel = true, className }: { status: DataStatus; size?: "xs" | "sm"; showLabel?: boolean; className?: string }) {
  const { t } = useI18n();
  const cfg = DATA[status];
  const label = status === "DEMO" ? "DEMO" : t.status[status];
  return (
    <Tip content={<span><b className="text-fg-1">{t.status[status]}</b> — {t.status.desc[status]}</span>}>
      <span tabIndex={0} className="inline-flex rounded-full" aria-label={`${t.common.status}: ${t.status[status]}`}>
        <Chip tone={cfg.tone} icon={cfg.icon} size={size} pulse={status === "LIVE"} className={className}>
          {showLabel ? label : null}
        </Chip>
      </span>
    </Tip>
  );
}

/** Status chip resolved from envelope metadata (auto-STALE for live data). */
export function MetaStatusChip({ meta, size }: { meta: DataMeta; size?: "xs" | "sm" }) {
  const now = useNow();
  return <StatusChip status={resolveStatus(meta.status, meta.retrievedAt, meta.ttlSec, now)} size={size} />;
}

/* ------------------------------------------------------------- runtime */

const RUNTIME: Record<AgentRuntimeState, { icon: IconT; tone: ChipTone }> = {
  running: { icon: Play, tone: "up" },
  idle: { icon: CirclePause, tone: "slate" },
  blocked: { icon: OctagonAlert, tone: "warn" },
  failed: { icon: CircleX, tone: "down" },
  registered: { icon: CircleDashed, tone: "info" },
  planned: { icon: Hourglass, tone: "muted" },
  suspended: { icon: Lock, tone: "violet" },
};

export function RuntimeChip({ state, size }: { state: AgentRuntimeState; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = RUNTIME[state];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size} pulse={state === "running"} title={t.runtime.desc[state]}>
      {t.runtime[state]}
    </Chip>
  );
}

const IMPL: Record<ImplementationStatus, { icon: IconT; tone: ChipTone }> = {
  IMPLEMENTED: { icon: Package, tone: "gold" },
  PARTIAL: { icon: PackageOpen, tone: "info" },
  DOCUMENTED_ONLY: { icon: FileText, tone: "slate" },
  PLANNED: { icon: PencilRuler, tone: "muted" },
};

export function ImplementationChip({ status, size }: { status: ImplementationStatus; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = IMPL[status];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.implementation[status]}
    </Chip>
  );
}

const VERIF: Record<VerificationStatus, { icon: IconT; tone: ChipTone }> = {
  PASS: { icon: CircleCheck, tone: "up" },
  FAIL: { icon: CircleX, tone: "down" },
  INCONCLUSIVE: { icon: CircleHelp, tone: "violet" },
  UNVERIFIED: { icon: CircleDashed, tone: "muted" },
};

export function VerificationChip({ status, kind, size }: { status: VerificationStatus; kind?: VerificationKind | null; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = VERIF[status];
  return (
    <span className="inline-flex items-center gap-1">
      <Chip tone={c.tone} icon={c.icon} size={size}>
        {t.verification[status]}
      </Chip>
      {kind && (
        <Chip tone={kind === "INDEPENDENT" ? "info" : "muted"} icon={kind === "INDEPENDENT" ? Users : User} size={size}>
          {t.verification[kind]}
        </Chip>
      )}
    </span>
  );
}

/* ------------------------------------------------------------ decisions */

const OUTCOME: Record<CanonicalOutcome, { icon: IconT; tone: ChipTone }> = {
  WATCH: { icon: Eye, tone: "gold" },
  MONITOR_ONLY: { icon: ScanSearch, tone: "info" },
  PAPER_CANDIDATE: { icon: ScrollText, tone: "data" },
  REJECT: { icon: Ban, tone: "down" },
  ABSTAIN: { icon: CircleMinus, tone: "slate" },
  INSUFFICIENT_EVIDENCE: { icon: SearchX, tone: "violet" },
  UNKNOWN: { icon: CircleHelp, tone: "violet" },
};

export function OutcomeChip({ outcome, size }: { outcome: CanonicalOutcome; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = OUTCOME[outcome];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.outcome[outcome]}
    </Chip>
  );
}

const IDENTITY: Record<IdentityState, { icon: IconT; tone: ChipTone }> = {
  VERIFIED: { icon: BadgeCheck, tone: "up" },
  PROBABLE: { icon: Fingerprint, tone: "info" },
  CONFLICT: { icon: Split, tone: "down" },
  UNKNOWN: { icon: CircleHelp, tone: "violet" },
};

export function IdentityChip({ state, size }: { state: IdentityState; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = IDENTITY[state];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.identity[state]}
    </Chip>
  );
}

const GATE: Record<SecurityGateState, { icon: IconT; tone: ChipTone }> = {
  PASS: { icon: ShieldCheck, tone: "up" },
  REJECT: { icon: ShieldX, tone: "down" },
  INCOMPLETE: { icon: ShieldAlert, tone: "warn" },
  STALE: { icon: ClockAlert, tone: "warn" },
};

export function GateChip({ state, size }: { state: SecurityGateState; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = GATE[state];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.gate[state]}
    </Chip>
  );
}

const SEVERITY: Record<Severity, { icon: IconT; tone: ChipTone }> = {
  CRITICAL: { icon: OctagonAlert, tone: "down" },
  HIGH: { icon: TriangleAlert, tone: "warn" },
  MEDIUM: { icon: CircleAlert, tone: "gold" },
  LOW: { icon: Info, tone: "info" },
  INFO: { icon: Info, tone: "slate" },
};

export function SeverityChip({ severity, size }: { severity: Severity; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = SEVERITY[severity];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.severity[severity]}
    </Chip>
  );
}

export function severityIcon(severity: Severity): IconT {
  return SEVERITY[severity].icon;
}

const CONF: Record<Confidence, { icon: IconT; tone: ChipTone }> = {
  HIGH: { icon: SignalHigh, tone: "gold" },
  MED: { icon: SignalMedium, tone: "slate" },
  LOW: { icon: SignalLow, tone: "muted" },
  UNKNOWN: { icon: CircleHelp, tone: "violet" },
};

export function ConfidenceChip({ confidence, size }: { confidence: Confidence; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = CONF[confidence];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.confidence[confidence]}
    </Chip>
  );
}

const PROVIDER: Record<ProviderHealthStatus, { icon: IconT; tone: ChipTone }> = {
  LIVE: { icon: CircleDot, tone: "up" },
  DEGRADED: { icon: TriangleAlert, tone: "warn" },
  TIMEOUT: { icon: Timer, tone: "warn" },
  RATE_LIMITED: { icon: Gauge, tone: "warn" },
  NO_KEY: { icon: KeyRound, tone: "slate" },
  AUTH_FAILED: { icon: Lock, tone: "down" },
  NETWORK_UNAVAILABLE: { icon: Unplug, tone: "down" },
  SOURCE_UNAVAILABLE: { icon: CircleSlash, tone: "down" },
  UNKNOWN: { icon: CircleHelp, tone: "violet" },
};

/** Provider health as reported by a probe. In this build the probes are mocked. */
export function ProviderChip({ status, size }: { status: ProviderHealthStatus; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = PROVIDER[status];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.provider[status]}
    </Chip>
  );
}

const NEWS: Record<VerificationState, { icon: IconT; tone: ChipTone }> = {
  VERIFIED: { icon: BadgeCheck, tone: "up" },
  UNVERIFIED: { icon: CircleDashed, tone: "slate" },
  CONFLICTING: { icon: Split, tone: "warn" },
};

export function NewsStateChip({ state, size }: { state: VerificationState; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = NEWS[state];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.newsState[state]}
    </Chip>
  );
}

/** Tri-state flag. `bad` = which answer is the risky one (e.g. honeypot YES). */
export function TriChip({ value, bad, size }: { value: TriState; bad: "YES" | "NO"; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  if (value === "UNKNOWN")
    return (
      <Chip tone="violet" icon={CircleHelp} size={size}>
        {t.tri.UNKNOWN}
      </Chip>
    );
  const isBad = value === bad;
  return (
    <Chip tone={isBad ? "down" : "up"} icon={isBad ? CircleX : CircleCheck} size={size}>
      {t.tri[value]}
    </Chip>
  );
}

const TIER: Record<AlertTier, { icon: IconT; tone: ChipTone }> = {
  SECURITY: { icon: ShieldAlert, tone: "down" },
  HIGH_ATTENTION: { icon: TriangleAlert, tone: "warn" },
  WATCH: { icon: Eye, tone: "gold" },
  INFO: { icon: Info, tone: "slate" },
};

export function AlertTierChip({ tier, size }: { tier: AlertTier; size?: "xs" | "sm" }) {
  const { t } = useI18n();
  const c = TIER[tier];
  return (
    <Chip tone={c.tone} icon={c.icon} size={size}>
      {t.alertTier[tier]}
    </Chip>
  );
}

export function alertTierIcon(tier: AlertTier): IconT {
  return TIER[tier].icon;
}
