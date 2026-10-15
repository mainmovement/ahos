"use client";

import { useState } from "react";
import { BadgeCheck, CircleHelp, CircleX, FileSearch, Fingerprint, Gavel, ShieldCheck, TrendingUp, Waypoints } from "lucide-react";
import type { DataEnvelope, TokenDossier } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn, shortenAddress } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice, StatTile } from "@/components/cards/blocks";
import { Sparkline } from "@/components/charts/sparkline";
import { RingGauge } from "@/components/charts/ring-gauge";
import { Chip } from "@/components/ui/chip";
import { CopyButton, Delta, Num, TimeAgo } from "@/components/ui/primitives";
import { ConfidenceChip, GateChip, IdentityChip, OutcomeChip, ProviderChip, TriChip } from "@/components/ui/status";

export function TokensView({ dossiers, initialToken }: { dossiers: DataEnvelope<TokenDossier[]>; initialToken?: string }) {
  const { t, tx } = useI18n();
  const list = dossiers.data;
  const [active, setActive] = useState(() => (initialToken && list.some((d) => d.tokenKey === initialToken) ? initialToken : list[0]?.tokenKey ?? ""));
  const d = list.find((x) => x.tokenKey === active);

  return (
    <PageBody>
      <PageHeader title={t.nav.items.tokens} subtitle={tx("پرونده توکن: قرارداد، زنجیره، اطمینان هویت، بررسی امنیتی و تصمیم کانونی", "Token dossier: contract, chain, identity confidence, security checks and canonical decision")} icon={Fingerprint} />
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-[280px_1fr]">
        <nav aria-label={tx("فهرست توکن‌ها", "Token list")} className="glass gold-border flex flex-col p-2">
          <h2 className="px-2 pb-2 pt-1 text-xs font-semibold text-fg-1">{tx("توکن‌های تحت بررسی", "Tokens under review")}</h2>
          <ul className="space-y-1">
            {list.map((x) => (
              <li key={x.tokenKey}>
                <button
                  type="button"
                  onClick={() => setActive(x.tokenKey)}
                  aria-current={x.tokenKey === active ? "true" : undefined}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-[var(--radius-md)] px-2.5 py-2 text-start transition-colors",
                    x.tokenKey === active ? "bg-[var(--surface-active)] shadow-[inset_0_0_0_1px_rgb(230_191_95/0.25)]" : "hover:bg-[var(--surface-hover)]",
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <bdi className="block text-xs font-semibold text-fg-1">{x.symbol}</bdi>
                    <span className="block truncate text-3xs text-fg-4">{x.chain} · {x.dex ?? "—"}</span>
                  </div>
                  <OutcomeChip outcome={x.decision.outcome} />
                </button>
              </li>
            ))}
          </ul>
        </nav>
        {d && <Dossier d={d} meta={dossiers.meta} />}
      </div>
    </PageBody>
  );
}

function Dossier({ d, meta }: { d: TokenDossier; meta: DataEnvelope<TokenDossier[]>["meta"] }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const conf = d.identity.confidence;
  return (
    <div className="flex min-w-0 flex-col gap-3">
      <DataCard
        title={`${d.symbol} — ${d.name}`}
        subtitle={tx("هویت پیش از هر چیز: نماد ≠ هویت", "Identity first: symbol ≠ identity")}
        icon={Fingerprint}
        meta={{ ...meta, retrievedAt: d.retrievedAt }}
        highlight
      >
        <div className="grid grid-cols-1 gap-3 @3xl:grid-cols-[1fr_auto]">
          <dl className="grid grid-cols-1 gap-2 @lg:grid-cols-2">
            <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
              <dt className="text-3xs text-fg-4">{t.common.chain}</dt>
              <dd className="mt-0.5 flex items-center gap-1.5 text-xs text-fg-1">
                <Chip tone="data" icon={Waypoints}>{d.chain}</Chip>
                <span className="text-3xs text-fg-4">DEX: <bdi>{d.dex ?? "—"}</bdi></span>
              </dd>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5">
              <dt className="text-3xs text-fg-4">{t.common.contract}</dt>
              <dd className="mt-0.5 flex items-center gap-1">
                {d.contract ? (
                  <>
                    <bdi className="mono truncate text-2xs text-gold-100" title={d.contract}>{shortenAddress(d.contract, 10, 8)}</bdi>
                    <CopyButton value={d.contract} />
                  </>
                ) : (
                  <span className="text-2xs text-fg-4">{t.common.unknownValue}</span>
                )}
              </dd>
            </div>
            <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5 @lg:col-span-2">
              <dt className="text-3xs text-fg-4">{tx("آدرس جفت معاملاتی", "Pair address")}</dt>
              <dd className="mt-0.5 flex items-center gap-1">
                {d.pairAddress ? (
                  <>
                    <bdi className="mono truncate text-2xs text-fg-2">{d.pairAddress}</bdi>
                    <CopyButton value={d.pairAddress} />
                  </>
                ) : (
                  <span className="text-2xs text-fg-4">{tx("هنوز جفت مهاجرت‌یافته ندارد", "No migrated pair yet")}</span>
                )}
              </dd>
            </div>
          </dl>
          <div className="flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-3">
            <RingGauge value={conf === null ? null : conf * 100} size={92} label={tx("اطمینان هویت", "Identity confidence")} caption={tx("اطمینان هویت", "identity")} display={conf === null ? "—" : f.pct(conf * 100, 0, false)} tone={conf === null ? "gold" : conf < 0.5 ? "down" : conf < 0.8 ? "warn" : "up"} />
            <div className="space-y-1">
              <IdentityChip state={d.identity.state} size="sm" />
              <p className="max-w-[180px] text-3xs leading-relaxed text-fg-4">
                {conf === null ? tx("قابل محاسبه نیست — منبع شناسایی در دسترس نیست.", "Cannot be computed — identity source unavailable.") : tx("سهم شواهد هویتی سازگار از منابع مستقل.", "Share of consistent identity evidence from independent sources.")}
              </p>
            </div>
          </div>
        </div>
        <ul className="mt-3 grid grid-cols-1 gap-1.5 @2xl:grid-cols-3">
          {d.identity.evidence.map((e) => (
            <li key={e.source} className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] px-2.5 py-2">
              {e.matched === true ? <BadgeCheck aria-label="match" className="mt-0.5 size-3.5 shrink-0 text-up" /> : e.matched === false ? <CircleX aria-label="mismatch" className="mt-0.5 size-3.5 shrink-0 text-down" /> : <CircleHelp aria-label="unknown" className="mt-0.5 size-3.5 shrink-0 text-violet" />}
              <div className="min-w-0">
                <bdi className="block text-2xs font-medium text-fg-1">{e.source}</bdi>
                <span className="text-3xs text-fg-3">{l(e.note)}</span>
              </div>
            </li>
          ))}
        </ul>
      </DataCard>

      <div className="grid grid-cols-1 gap-3 @6xl:grid-cols-2">
        <DataCard title={tx("بررسی امنیتی", "Security checks")} subtitle={tx("نامعلوم ≠ امن · رد پیش‌فرض در نبود شواهد", "Unknown ≠ safe · fail-closed without evidence")} icon={ShieldCheck} meta={meta} actions={<GateChip state={d.security.gate} size="sm" />}>
          <dl className="grid grid-cols-2 gap-2 @lg:grid-cols-3">
            {(
              [
                [tx("هانی‌پات", "Honeypot"), <TriChip key="h" value={d.security.honeypot} bad="YES" />],
                [tx("قابل فروش", "Sellable"), <TriChip key="s" value={d.security.sellable} bad="NO" />],
                [tx("قابل ضرب", "Mintable"), <TriChip key="m" value={d.security.mintable} bad="YES" />],
                [tx("قابل انجماد", "Freezeable"), <TriChip key="f" value={d.security.freezeable} bad="YES" />],
                [
                  tx("مالکیت", "Ownership"),
                  <Chip key="o" tone={d.security.ownership === "RENOUNCED" ? "up" : d.security.ownership === "OPEN" ? "warn" : "violet"}>
                    {d.security.ownership === "RENOUNCED" ? tx("واگذارشده", "Renounced") : d.security.ownership === "OPEN" ? tx("باز", "Open") : t.common.unknownValue}
                  </Chip>,
                ],
              ] as const
            ).map(([label, chip]) => (
              <div key={label} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2.5 py-2">
                <dt className="mb-1 text-3xs text-fg-4">{label}</dt>
                <dd>{chip}</dd>
              </div>
            ))}
          </dl>
          {d.security.flags.length > 0 && (
            <ul className="mt-2.5 space-y-1">
              {d.security.flags.map((fl) => (
                <li key={fl.en} className="flex items-center gap-1.5 text-2xs text-warn">
                  <span aria-hidden>▲</span>
                  {l(fl)}
                </li>
              ))}
            </ul>
          )}
        </DataCard>

        <DataCard title={tx("داده بازار", "Market facts")} subtitle={tx("هر مقدار نامعلوم با «—» نمایش داده می‌شود", "Unknown values render as “—”")} icon={TrendingUp} meta={meta}>
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-baseline gap-2">
              <Num className="text-xl font-semibold text-fg-1">{f.usd(d.market.priceUsd, d.market.priceUsd !== null && d.market.priceUsd < 0.01 ? 8 : 4)}</Num>
              <Delta value={d.market.change24h} />
            </div>
            <div className="w-40">
              <Sparkline data={d.spark} height={30} label={`${d.symbol}`} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 @lg:grid-cols-3">
            <StatTile label={tx("نقدینگی", "Liquidity")} value={f.usdCompact(d.market.liquidityUsd)} />
            <StatTile label={tx("حجم ۲۴س", "24h volume")} value={f.usdCompact(d.market.volume24h)} />
            <StatTile label="FDV" value={f.usdCompact(d.market.fdv)} />
            <StatTile label={tx("دارندگان", "Holders")} value={f.compact(d.market.holders)} />
            <StatTile label={tx("عمر", "Age")} value={d.market.ageHours === null ? "—" : f.duration(d.market.ageHours * 3600)} />
            <StatTile label={tx("نسبت حجم/نقدینگی", "Vol/Liq ratio")} value={d.market.volume24h && d.market.liquidityUsd ? f.num(d.market.volume24h / d.market.liquidityUsd, 2) : "—"} />
          </div>
        </DataCard>
      </div>

      <div className="grid grid-cols-1 gap-3 @6xl:grid-cols-2">
        <DataCard title={tx("تصمیم مرجع کانونی", "Canonical decision")} subtitle={tx("خروجی پایتون — رابط هیچ تصمیمی نمی‌سازد", "Python output — the UI never creates a decision")} icon={Gavel} meta={meta} actions={<OutcomeChip outcome={d.decision.outcome} size="sm" />}>
          <div className="mb-3 flex items-center gap-3">
            <RingGauge value={d.decision.score} size={76} label={t.common.score} caption={t.common.score} />
            <div className="space-y-1">
              <ConfidenceChip confidence={d.decision.confidence} size="sm" />
              <p className="text-3xs text-fg-4">{tx("امتیاز ترتیبی است، نه احتمال سود.", "The score is ordinal, not a probability of profit.")}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 @2xl:grid-cols-2">
            {[
              { title: tx("دلایل", "Reasons"), items: d.decision.reasons, tone: "text-up" },
              { title: tx("ریسک‌ها", "Risks"), items: d.decision.risks, tone: "text-down" },
              { title: tx("ناشناخته‌ها", "Unknowns"), items: d.decision.unknowns, tone: "text-violet" },
              { title: tx("شرایط ابطال", "Invalidation"), items: d.decision.invalidation, tone: "text-warn" },
            ].map((b) => (
              <div key={b.title} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] p-2.5">
                <div className={cn("mb-1 text-3xs font-semibold", b.tone)}>{b.title}</div>
                {b.items.length ? (
                  <ul className="space-y-0.5 text-2xs text-fg-2">
                    {b.items.map((it) => (
                      <li key={it.en}>• {l(it)}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-3xs text-fg-5">{tx("ثبت نشده", "None recorded")}</p>
                )}
              </div>
            ))}
          </div>
        </DataCard>

        <DataCard title={tx("شواهد منابع", "Provider evidence")} subtitle={tx("وضعیت هر منبع در این پرونده", "Status of each source in this dossier")} icon={FileSearch} meta={meta}>
          <ul className="space-y-1.5">
            {d.providers.map((p) => (
              <li key={p.provider} className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2.5 py-2">
                <bdi className="w-28 shrink-0 text-2xs font-medium text-fg-1">{p.provider}</bdi>
                <ProviderChip status={p.status} />
                <span className="min-w-0 flex-1 truncate text-3xs text-fg-3">{l(p.summary)}</span>
                <Num className="shrink-0 text-3xs text-fg-4">{p.latencyMs === null ? "—" : `${f.num(p.latencyMs, 0)}ms`}</Num>
              </li>
            ))}
          </ul>
          <Notice className="mt-3" tone="violet" icon={<CircleHelp />}>
            {tx("منبعی که پاسخ نمی‌دهد «نامعلوم» ثبت می‌شود و هرگز به‌عنوان «سالم» شمرده نمی‌شود.", "A source that does not respond is recorded as UNKNOWN and is never counted as healthy.")}{" "}
            <TimeAgo iso={d.retrievedAt} className="text-fg-4" />
          </Notice>
        </DataCard>
      </div>
    </div>
  );
}
