"use client";

import { ArrowDownRight, ArrowUpRight, CircleAlert, CircleCheck, History, Lock, OctagonAlert, ShieldCheck, TrendingUp, Wallet } from "lucide-react";
import type { DataEnvelope, PaperAccount } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { AreaSeriesChart } from "@/components/charts/charts";
import { Chip } from "@/components/ui/chip";
import { Delta, Meter, Num, TimeAgo } from "@/components/ui/primitives";
import { StatusChip } from "@/components/ui/status";

export function PaperView({ account }: { account: DataEnvelope<PaperAccount> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const a = account.data;
  const side = (s: "LONG" | "SHORT") => (
    <Chip tone={s === "LONG" ? "up" : "down"} icon={s === "LONG" ? ArrowUpRight : ArrowDownRight}>
      {s === "LONG" ? tx("خرید (کاغذی)", "Long (paper)") : tx("فروش (کاغذی)", "Short (paper)")}
    </Chip>
  );
  return (
    <PageBody>
      <PageHeader title={t.nav.items.paperTrading} subtitle={tx("موقعیت‌ها، سود/زیان و محدودیت‌های ریسک — حساب شبیه‌سازی", "Positions, PnL and risk limits — simulated account")} icon={Wallet} />
      <div role="note" className="glass-strong gold-border-strong flex flex-wrap items-center gap-3 rounded-[var(--radius-lg)] px-4 py-3">
        <span className="flex size-10 items-center justify-center rounded-full border border-gold-300/50 bg-gold-400/10 text-gold-200 shadow-[var(--shadow-glow-md)]">
          <Lock aria-hidden className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold text-gold-100">
            <span dir="ltr">PAPER_ONLY</span> · {tx("معامله واقعی در این سامانه وجود ندارد", "Real trading does not exist in this system")}
          </div>
          <p className="text-2xs text-fg-3">
            {tx("بدون کیف پول، بدون کلید خصوصی، بدون اتصال به صرافی. موقعیت‌ها فقط پس از مجوز paper_allowed از مرجع کانونی باز می‌شوند.", "No wallets, no private keys, no exchange connectivity. Positions open only after paper_allowed from the canonical authority.")}
          </p>
        </div>
        <Chip tone="gold" icon={ShieldCheck} size="sm">
          {tx("قانون اساسی C2", "Constitution C2")}
        </Chip>
      </div>
      <section className="grid grid-cols-2 gap-3 @2xl:grid-cols-4 @6xl:grid-cols-8">
        <StatTile label={tx("ارزش حساب", "Equity")} value={f.usd(a.equity, 0)} tone="gold" />
        <StatTile label={tx("نقد", "Cash")} value={f.usd(a.cash, 0)} />
        <StatTile label={tx("سود/زیان امروز", "Today PnL")} value={f.usd(a.pnlDay, 0)} delta={a.pnlDayPct} tone="up" />
        <StatTile label={tx("سود/زیان کل", "Total PnL")} value={f.usd(a.pnlTotal, 0)} delta={a.pnlTotalPct} tone="up" />
        <StatTile label={tx("نرخ برد", "Win rate")} value={a.winRate === null ? "—" : f.pct(a.winRate * 100, 0, false)} />
        <StatTile label={tx("شارپ", "Sharpe")} value={f.num(a.sharpe, 2)} />
        <StatTile label={tx("افت حداکثر", "Max drawdown")} value={f.pct(a.maxDrawdownPct, 1)} tone="down" />
        <StatTile label={tx("تعداد معاملات", "Trades")} value={f.num(a.tradeCount, 0)} />
      </section>
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-8" title={tx("منحنی ارزش حساب", "Equity curve")} subtitle={tx("۹۰ روز — شبیه‌سازی", "90 days — simulated")} icon={TrendingUp} meta={account.meta}>
          <AreaSeriesChart points={a.equityCurve} height={260} label={tx("منحنی ارزش", "Equity curve")} color="gold" />
        </DataCard>
        <DataCard className="@4xl:col-span-4" title={tx("محدودیت‌های ریسک", "Risk limits")} subtitle={tx("اعمال‌شده توسط مرجع کانونی", "Enforced by the canonical authority")} icon={ShieldCheck} meta={account.meta}>
          <ul className="space-y-3">
            {a.limits.map((lim) => {
              const Icon = lim.state === "ok" ? CircleCheck : lim.state === "warn" ? CircleAlert : OctagonAlert;
              const unit = lim.unit === "pct" ? "%" : lim.unit === "usd" ? "$" : "";
              return (
                <li key={lim.id}>
                  <div className="mb-1 flex items-center gap-1.5 text-2xs">
                    <Icon aria-label={lim.state} className={cn("size-3.5", lim.state === "ok" ? "text-up" : lim.state === "warn" ? "text-warn" : "text-down")} />
                    <span className="min-w-0 flex-1 truncate text-fg-2">{l(lim.label)}</span>
                    <Num className="text-3xs text-fg-3">
                      {f.num(lim.used, 1)}
                      {unit} / {f.num(lim.limit, 0)}
                      {unit}
                    </Num>
                  </div>
                  <Meter value={lim.used} max={lim.limit} tone={lim.state === "ok" ? "gold" : lim.state === "warn" ? "warn" : "down"} label={l(lim.label)} height={5} />
                </li>
              );
            })}
          </ul>
        </DataCard>
      </div>
      <DataCard title={tx("موقعیت‌های باز (کاغذی)", "Open positions (paper)")} icon={Wallet} meta={account.meta} bodyClassName="px-0 pb-0">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.symbol}</th>
                <th scope="col">{tx("جهت", "Side")}</th>
                <th scope="col" className="num-cell">{tx("مقدار", "Qty")}</th>
                <th scope="col" className="num-cell">{tx("ورود", "Entry")}</th>
                <th scope="col" className="num-cell">{tx("قیمت جاری", "Mark")}</th>
                <th scope="col" className="num-cell">{tx("سود/زیان", "PnL")}</th>
                <th scope="col" className="num-cell">{tx("حد ضرر / هدف", "Stop / target")}</th>
                <th scope="col">{tx("راهبرد", "Strategy")}</th>
                <th scope="col">{t.common.status}</th>
                <th scope="col" className="pe-3.5">{tx("بازشده", "Opened")}</th>
              </tr>
            </thead>
            <tbody>
              {a.positions.map((p) => (
                <tr key={p.id}>
                  <td className="ps-3.5"><bdi className="text-xs font-semibold text-fg-1">{p.symbol}</bdi></td>
                  <td>{side(p.side)}</td>
                  <td className="num-cell"><Num className="text-2xs text-fg-2">{f.num(p.qty, 4)}</Num></td>
                  <td className="num-cell"><Num className="text-2xs text-fg-2">{f.num(p.entry, 4)}</Num></td>
                  <td className="num-cell"><Num className={cn("text-2xs", p.mark === null ? "text-fg-4" : "text-fg-1")}>{f.num(p.mark, 4)}</Num></td>
                  <td className="num-cell">
                    <Num className={cn("block text-2xs font-semibold", p.pnl === null ? "text-fg-4" : p.pnl >= 0 ? "text-up" : "text-down")}>{f.usd(p.pnl, 0)}</Num>
                    <Delta value={p.pnlPct} size="xs" />
                  </td>
                  <td className="num-cell"><Num className="text-3xs text-fg-3">{f.num(p.stop, 2)} / {f.num(p.target, 2)}</Num></td>
                  <td className="max-w-[180px] truncate text-3xs text-fg-3">{l(p.strategy)}</td>
                  <td><StatusChip status={p.status} /></td>
                  <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={p.openedAt} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
      <DataCard title={tx("تاریخچه اجرای کاغذی", "Paper fill history")} icon={History} meta={account.meta} bodyClassName="px-0 pb-0">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{t.common.symbol}</th>
              <th scope="col">{tx("نوع", "Kind")}</th>
              <th scope="col">{tx("جهت", "Side")}</th>
              <th scope="col" className="num-cell">{t.common.price}</th>
              <th scope="col" className="num-cell">{tx("سود/زیان", "PnL")}</th>
              <th scope="col">{tx("دلیل", "Reason")}</th>
              <th scope="col" className="pe-3.5">{t.common.time}</th>
            </tr>
          </thead>
          <tbody>
            {a.fills.map((x) => (
              <tr key={x.id}>
                <td className="ps-3.5"><bdi className="text-xs font-semibold text-fg-1">{x.symbol}</bdi></td>
                <td><Chip tone={x.kind === "OPEN" ? "info" : "muted"}>{x.kind === "OPEN" ? tx("باز", "Open") : tx("بسته", "Close")}</Chip></td>
                <td>{side(x.side)}</td>
                <td className="num-cell"><Num className="text-2xs text-fg-2">{f.num(x.price, 4)}</Num></td>
                <td className="num-cell"><Num className={cn("text-2xs", x.pnl === null ? "text-fg-4" : x.pnl >= 0 ? "text-up" : "text-down")}>{f.usd(x.pnl, 0)}</Num></td>
                <td className="text-3xs text-fg-3">{l(x.reason)}</td>
                <td className="pe-3.5 text-3xs text-fg-4"><TimeAgo iso={x.at} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </DataCard>
    </PageBody>
  );
}
