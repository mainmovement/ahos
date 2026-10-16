"use client";

/**
 * The text view: every market, signal and department as plain text.
 *
 * It is always in the DOM for screen readers and low-power devices (CSS keeps it off-canvas until
 * the operator opens it with the "فهرست متنی" toggle). Relative times are computed from the caller's
 * reference clock; when there is no timestamp the row says so instead of guessing.
 */

import type { Dictionary } from "../../lib/i18n";
import { asOfText, formatPercent, localizeNumber } from "../../lib/i18n";
import { gateMath, tableOrder } from "../../lib/style";
import type { Department, Gate, Health, Lang, MarketNode, Signal } from "../../types/globe";

export type TextTableProps = {
  markets: readonly MarketNode[];
  signals: readonly Signal[];
  departments: readonly Department[];
  gate: Gate;
  health: Health;
  lang: Lang;
  dict: Dictionary;
  now: number | null;
  open: boolean;
};

export function TextTable({ markets, signals, departments, gate, health, lang, dict, now, open }: TextTableProps) {
  const math = gateMath(gate);
  const nodeNames = new Map(markets.map((market) => [market.id, lang === "fa" ? market.nameFa : market.nameEn]));

  return (
    <section className="ahos-textview" data-open={open ? "true" : "false"} aria-label={dict.tableCaption}>
      <h3 className="ahos-textview-title">{dict.tableCaption}</h3>
      <table className="ahos-table" data-table="markets">
        <caption className="ahos-visually-hidden">{dict.tableCaption}</caption>
        <thead>
          <tr>
            <th scope="col">{dict.columnName}</th>
            <th scope="col">{dict.columnFreshness}</th>
            <th scope="col">{dict.columnAsOf}</th>
            <th scope="col">{dict.columnChange}</th>
            <th scope="col">{dict.columnAttention}</th>
          </tr>
        </thead>
        <tbody>
          {tableOrder(markets).map((market) => {
            const stamp = asOfText(market.asOf, now, lang);
            const change = formatPercent(market.changePct, lang);
            return (
              <tr key={market.id} data-freshness={market.freshness}>
                <th scope="row">{lang === "fa" ? market.nameFa : market.nameEn}</th>
                <td>
                  <span className="ahos-chip" data-freshness={market.freshness}>
                    {dict.freshness[market.freshness]}
                  </span>
                </td>
                <td>
                  {stamp.display ?? dict.unknownValue}
                  {stamp.relative && stamp.absolute ? (
                    <span className="ahos-table-dim">{` · ${stamp.absolute}`}</span>
                  ) : null}
                </td>
                <td>{change ?? dict.unknownValue}</td>
                <td>{market.needsAttention ? dict.attentionYes : dict.attentionNo}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h4 className="ahos-textview-subtitle">{lang === "fa" ? "سیگنال‌ها" : "Signals"}</h4>
      <table className="ahos-table" data-table="signals">
        <thead>
          <tr>
            <th scope="col">{lang === "fa" ? "از" : "From"}</th>
            <th scope="col">{lang === "fa" ? "به" : "To"}</th>
            <th scope="col">{lang === "fa" ? "نتیجه" : "Outcome"}</th>
            <th scope="col">{lang === "fa" ? "دلیل" : "Reason"}</th>
            <th scope="col">{dict.columnAsOf}</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((signal) => (
            <tr key={signal.id} data-outcome={signal.outcome}>
              <td>{nodeNames.get(signal.fromNodeId) ?? signal.fromNodeId}</td>
              <td>{nodeNames.get(signal.toNodeId) ?? signal.toNodeId}</td>
              <td>
                {signal.outcome === "absorbed"
                  ? dict.outcomeAbsorbed
                  : signal.outcome === "dissipated"
                    ? dict.outcomeDissipated
                    : dict.outcomePending}
              </td>
              <td>{signal.reasonFa ?? dict.unknownValue}</td>
              <td>{asOfText(signal.at, now, lang).display ?? dict.unknownValue}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4 className="ahos-textview-subtitle">{lang === "fa" ? "دپارتمان‌ها" : "Departments"}</h4>
      <ul className="ahos-department-list">
        {departments.map((department) => (
          <li key={department.id} data-freshness={department.freshness}>
            <span>{department.nameFa}</span>
            <span className="ahos-chip" data-freshness={department.freshness}>
              {dict.freshness[department.freshness]}
            </span>
            {department.needsAttention ? <span className="ahos-chip" data-tone="attention">{dict.columnAttention}</span> : null}
          </li>
        ))}
      </ul>

      <p className="ahos-textview-note">
        {dict.gateAria}:{" "}
        {math.known
          ? `${localizeNumber(math.absorbed, lang)} ${dict.gateAbsorbed} · ${localizeNumber(math.dissipated, lang)} ${dict.gateDissipated}`
          : dict.unknownValue}
        {math.strictness === null ? "" : ` · ${lang === "fa" ? "سختگیری" : "strictness"} ${localizeNumber(math.strictness.toFixed(2), lang)}`}
        {" · "}
        {health.stale
          ? dict.heartbeatStale
          : dict.heartbeatLive(localizeNumber(health.bpm, lang), localizeNumber(health.jitterMs, lang))}
      </p>
    </section>
  );
}
