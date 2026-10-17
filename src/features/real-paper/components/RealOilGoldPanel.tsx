import { tr } from "@/src/lib/i18n";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { loadLatestJudge, loadReplayLessons, loadReplaySummary, loadReplayTrades, loadSoakLedger, REPLAY_DIR, REPLAY_MARKETS } from "../lib/data.server";
import { replayAge } from "../lib/model";
import { Kpi, Tbl, ageText, ni, nz, stamp } from "./shared";

const t = (k: string) => tr("fa", `realOilGold.${k}`);

/** LIVE gold soak and REPLAY_NOT_LIVE results as two separate, labelled sections. Read-only. */
export function RealOilGoldPanel({ nowMs = Date.now() }: { nowMs?: number }) {
  const led = loadSoakLedger(nowMs);
  const judge = loadLatestJudge();
  const rep = loadReplaySummary();
  const les = loadReplayLessons();
  const trades = REPLAY_MARKETS.map((m) => ({ m, r: loadReplayTrades(m) }));
  const age = rep.state === "ok" ? replayAge(rep.mtimeIso, nowMs) : null;
  return (
    <div data-real-oilgold="">
      <section className="mb-sec" data-real-live="">
        <h2 className="mb-h2">{t("liveTitle")} <TruthChip status={led.state === "ok" ? led.value.status : "UNAVAILABLE"} size="sm" /></h2>
        {led.state !== "ok" ? <p className="mb-empty">{led.state === "missing" ? t("liveMissing") : t("liveMalformed")}</p> : (
          <div className="mb-kpis">
            <Kpi k={t("goldEquity")} v={nz(led.value.equityUsd)} chip={led.value.status} />
            <Kpi k={t("lastCycle")} v={`${stamp(led.value.lastCycleIso)} (${ageText(led.value.ageMin)})`} />
            <Kpi k={t("openPos")} v={led.value.positionOpen === null ? "-" : led.value.positionOpen ? "1" : "0"} />
            <Kpi k={t("closed")} v={ni(led.value.closedTrades)} />
            <Kpi k={t("winsLosses")} v={judge.state === "ok" ? `${ni(judge.value.wins)} / ${ni(judge.value.losses)}` : "-"} />
            <Kpi k={t("witness")} v={led.value.witnessState ?? "-"} />
            <Kpi k={t("tier")} v={led.value.tier?.tier ?? "-"} />
          </div>
        )}
        <div className="mb-kpis">
          <Kpi k={t("liveOil")} v={t("noOil")} chip="UNKNOWN" />
        </div>
      </section>
      <section className="mb-sec" data-real-replay="" data-label="REPLAY_NOT_LIVE">
        <h2 className="mb-h2">{t("replayTitle")} <span className="mb-tag" dir="ltr">REPLAY_NOT_LIVE</span> {age ? <TruthChip status={age.status} size="sm" /> : <TruthChip status="UNAVAILABLE" size="sm" />}</h2>
        <p className="mb-note">{t("replayNote")}{age && age.ageHours !== null ? <> {t("fileAge")}: <span dir="ltr">{age.ageHours} h</span></> : null}</p>
        {rep.state !== "ok" ? <p className="mb-empty">{rep.state === "missing" ? t("replayMissing") : t("replayMalformed")}</p> : (
          <>
            <p className="mb-note" data-mb-edge="" lang="en" dir="ltr">{rep.value.edge === "NO_PROVEN_EDGE" ? "no proven edge yet" : "edge verdict: UNKNOWN"} &mdash; {t("edgeFa")}</p>
            <Tbl heads={[t("market"), t("buyHold"), t("best"), t("lab"), t("verdict")]}>
              {rep.value.rows.map((r) => (
                <tr key={r.market} data-real-replay-row=""><td dir="auto">{r.market}</td><td dir="ltr" className="tv-mono">{r.buyHold}</td><td dir="ltr" className="tv-mono">{r.bestBaseline}</td><td dir="ltr" className="tv-mono">{r.labPick}</td><td dir="ltr">{r.verdict}</td></tr>
              ))}
            </Tbl>
          </>
        )}
        <h3 className="mb-h2">{t("tradesTitle")}</h3>
        <Tbl heads={[t("market"), t("tradesAll"), t("tradesTest"), t("tradesLabel")]}>
          {trades.map(({ m, r }) => (
            <tr key={m} data-real-trades-row=""><td dir="ltr">{m}</td>
              <td dir="ltr" className="tv-mono">{r.state === "ok" ? r.value.rows : "-"}</td>
              <td dir="ltr" className="tv-mono">{r.state === "ok" ? (r.value.byPeriod.TEST ?? "-") : "-"}</td>
              <td dir="ltr">{r.state === "ok" ? r.value.labels.join(",") : r.state === "missing" ? "MISSING" : "MALFORMED"}</td></tr>
          ))}
        </Tbl>
        {les.state === "ok" ? <p className="mb-note" dir="auto" data-real-lessons="">{t("lessons")}: {les.value.title ?? "lessons.md"} ({ni(les.value.sections)})</p> : null}
        <div className="mb-links" data-real-equity="">
          {REPLAY_MARKETS.map((m) => (
            // eslint-disable-next-line @next/next/no-img-element
            <figure key={m}><img src={`/arena/oil-gold/equity/${m}`} alt={`equity ${m} (REPLAY_NOT_LIVE)`} width={380} loading="lazy" /><figcaption dir="ltr">equity_{m}.png | REPLAY_NOT_LIVE</figcaption></figure>
          ))}
        </div>
        <p className="mb-note tv-faint" dir="ltr">{REPLAY_DIR.replace(/^.*[\\/]robat[\\/]/, "")}</p>
      </section>
    </div>
  );
}
