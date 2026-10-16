"use client";
import { tr } from "../../lib/i18n";
import { useMemo, useState } from "react";
import { ArrowDownUp, Search } from "lucide-react";
import type { Language } from "../../lib/navigation";
import type { MarketAsset } from "../../lib/api/types";
import { getMarkets } from "../../lib/api/dashboard";
import { DataCard, StatusChip } from "./DataCard";
import { Sparkline } from "../charts/Sparkline";
export function MarketTable({
  language,
  selected,
  onSelect,
  category,
  expanded = false,
}: {
  language: Language;
  selected?: string;
  onSelect: (symbol: string) => void;
  category?: MarketAsset["category"];
  expanded?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState(false);
  const fa = language === "fa";
  const rows = useMemo(() => {
    const list = getMarkets(category).filter((item) =>
      `${item.symbol} ${item.name.fa} ${item.name.en}`
        .toLowerCase()
        .includes(query.toLowerCase()),
    );
    return sort ? list.sort((a, b) => b.change - a.change) : list;
  }, [category, query, sort]);
  return (
    <DataCard
      title={fa ? "دیده‌بان دارایی‌ها" : "Asset watchlist"}
      icon="nav/market-prices"
      language={language}
      className="dc-watchlist"
      action={
        <button
          className="ah-icon-button"
          aria-label={fa ? "مرتب‌سازی بر اساس تغییر" : "Sort by change"}
          aria-pressed={sort}
          onClick={() => setSort(!sort)}
        >
          <ArrowDownUp size={13} />
        </button>
      }
    >
      <label className="dc-table-search">
        <Search size={13} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={fa ? "جست‌وجوی دارایی..." : "Find an asset…"}
          aria-label={fa ? "جست‌وجوی دارایی" : "Search assets"}
        />
      </label>
      <div className="dc-table-scroll">
        <table>
          <thead>
            <tr>
              <th>{fa ? "دارایی" : "Asset"}</th>
              <th>{fa ? tr("fa", "common.labels.price") : "Price"}</th>
              <th>{fa ? "۲۴ ساعت" : "24h"}</th>
              {expanded && <th>{fa ? tr("fa", "common.labels.volume") : "Volume"}</th>}
              <th>{fa ? "روند" : "Trend"}</th>
              <th>{fa ? tr("fa", "common.labels.status") : "Status"}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((asset) => (
              <tr
                key={asset.symbol}
                className={selected === asset.symbol ? "is-selected" : ""}
              >
                <td>
                  <button
                    className="dc-asset-button"
                    onClick={() => onSelect(asset.symbol)}
                    aria-pressed={selected === asset.symbol}
                  >
                    <span className={`dc-coin dc-coin-${asset.category}`}>
                      {asset.symbol.slice(0, 1)}
                    </span>
                    <span>
                      <bdi>{asset.symbol}</bdi>
                      <small>{asset.name[language]}</small>
                    </span>
                  </button>
                </td>
                <td>
                  <bdi>
                    {asset.price.toLocaleString("en-US", {
                      maximumFractionDigits: 2,
                    })}
                  </bdi>
                </td>
                <td className={asset.change < 0 ? "dc-down" : "dc-up"}>
                  <bdi>
                    {asset.change > 0 ? "+" : ""}
                    {asset.change}%
                  </bdi>
                </td>
                {expanded && (
                  <td>
                    <bdi>{asset.volume}</bdi>
                  </td>
                )}
                <td>
                  <Sparkline
                    values={asset.history.slice(-12)}
                    tone={asset.change < 0 ? "danger" : "cyan"}
                  />
                </td>
                <td>
                  <StatusChip status={asset.freshness} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="dc-empty" role="status">
            {fa ? "دارایی مطابق جست‌وجو یافت نشد." : "No matching assets."}
          </p>
        )}
      </div>
    </DataCard>
  );
}
