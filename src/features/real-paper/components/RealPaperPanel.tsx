import { tr } from "@/src/lib/i18n";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { PaperOnlyPill } from "@/src/features/trade-venue/components/PaperOnlyGuard";
import { loadLatestJudge, loadSoakLedger, SOAK_STATUS_FILE } from "../lib/data.server";
import { Kpi, Tbl, ageText, ni, nz, stamp } from "./shared";

const t = (k: string) => tr("fa", `realPaper.${k}`);

/** REAL read-only paper ledger (M13 gold soak). Server component. No controls, no forms, no PnL colours. */
export function RealPaperPanel({ nowMs = Date.now() }: { nowMs?: number }) {
  const led = loadSoakLedger(nowMs);
  const judge = loadLatestJudge();
  const src = SOAK_STATUS_FILE.replace(/^.*[\\/]reports[\\/]/, "reports/");
  return (
    <section className="mb-body" data-real-paper="" data-real-state={led.state} aria-label={t("title")}>
      <header className="mb-head">
        <div><h2 className="mb-title">{t("title")}</h2><p className="mb-sub">{t("note")}</p></div>
        <div className="mb-head__chips">
          <PaperOnlyPill />
          <TruthChip status={led.state === "ok" ? led.value.status : led.state === "missing" ? "UNAVAILABLE" : "ERROR"} />
        </div>
      </header>
      <p className="mb-source" data-mb-source="">
        <span>{t("source")}:</span> <span dir="ltr" className="tv-mono">{src}</span>
        {led.state === "ok" ? <><span className="mb-dot">|</span><span>{t("lastCycle")}:</span> <span dir="ltr" className="tv-mono" data-real-ts="">{stamp(led.value.lastCycleIso)}</span> <span className="tv-faint">({t("age")}: <span dir="ltr">{ageText(led.value.ageMin)}</span>)</span></> : null}
      </p>
      {led.state !== "ok" ? <p className="mb-empty" data-real-block="">{led.state === "missing" ? t("missing") : t("malformed")} <TruthChip status="UNKNOWN" size="sm" /></p> : (() => {
        const v = led.value;
        const j = judge.state === "ok" ? judge.value : null;
        return (
          <>
            {!v.paperOnly ? <p className="mb-note" data-real-warn="">{t("notPaper")}</p> : null}
            {v.status === "STALE" ? <p className="mb-note" data-real-stale="">{t("stale")} <span dir="ltr">{ageText(v.ageMin)}</span></p> : null}
            <div className="mb-kpis" data-real-kpis="">
              <Kpi k={t("equity")} v={nz(v.equityUsd)} chip={v.status} />
              <Kpi k={t("bankroll")} v={nz(v.bankrollUsd)} />
              <Kpi k={t("realized")} v={nz(v.cumulativeRealizedUsd)} />
              <Kpi k={t("unrealized")} v={t("unknown")} chip="UNKNOWN" />
              <Kpi k={t("tradeCount")} v={ni(v.closedTrades)} />
              <Kpi k={t("settled")} v={ni(v.settledTrades)} />
              <Kpi k={t("invalidated")} v={j ? ni(j.invalidated) : "-"} />
              <Kpi k={t("winsLosses")} v={j ? `${ni(j.wins)} / ${ni(j.losses)}` : "-"} />
              <Kpi k={t("tier")} v={v.tier ? `${v.tier.tier ?? "-"} (${ni(v.tier.trades)})` : "-"} chip={v.tier ? undefined : "UNKNOWN"} />
              <Kpi k={t("breaker")} v={v.breakerState ?? "-"} />
            </div>
            {v.tier ? <p className="mb-note" data-real-tier="">{t("tierNote")}</p> : null}
            <h3 className="mb-h2">{t("positions")}</h3>
            {v.position ? (
              <Tbl heads={[t("entryTime"), t("entryPx"), t("execPx"), t("notional"), t("qty"), t("unrealized")]}>
                <tr data-real-position="">
                  <td dir="ltr" className="tv-mono">{stamp(v.position.entryIso)}</td>
                  <td dir="ltr" className="tv-mono">{nz(v.position.entryPrice)}</td>
                  <td dir="ltr" className="tv-mono">{nz(v.position.execPrice)}</td>
                  <td dir="ltr" className="tv-mono">{nz(v.position.notionalUsd)}</td>
                  <td dir="ltr" className="tv-mono">{nz(v.position.qtyOz, 4)}</td>
                  <td><TruthChip status="UNKNOWN" size="sm" /></td>
                </tr>
              </Tbl>
            ) : <p className="mb-empty" data-real-nopos="">{v.positionOpen === false ? t("noPosition") : t("unknown")}</p>}
            <h3 className="mb-h2">{t("witness")}</h3>
            <p className="mb-note" data-real-witness="" dir="auto">{v.witnessState ?? "-"}{v.witnessReason ? ` - ${v.witnessReason}` : ""}</p>
            {v.witnessQuotes.length > 0 ? (
              <Tbl heads={[t("provider"), t("instrument"), t("price"), t("observed"), t("age")]}>
                {v.witnessQuotes.map((q) => (
                  <tr key={q.provider}><td dir="ltr" className="tv-mono">{q.provider}</td><td dir="ltr">{q.instrument ?? "-"}</td><td dir="ltr" className="tv-mono">{nz(q.priceUsd)}</td><td dir="ltr" className="tv-mono">{stamp(q.observedIso)}</td><td dir="ltr">{ageText(q.ageMin)}</td></tr>
                ))}
              </Tbl>
            ) : null}
            <p className="mb-note" dir="auto">{t("judge")}: {judge.state === "ok" ? `${judge.value.verdict ?? "-"} | ${judge.file ?? ""}` : t("unknown")} | {t("reconcile")}: {v.reconcile ? `${v.reconcile.verdict ?? "-"} (${ni(v.reconcile.entries)})` : t("unknown")}</p>
          </>
        );
      })()}
      <p className="mb-note" data-real-demo-note="">{t("demoBelow")}</p>
    </section>
  );
}
