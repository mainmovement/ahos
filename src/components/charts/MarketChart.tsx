"use client";
import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";

import type { EChartsOption } from "echarts";
import { getMarketCandles, getMarkets } from "../../lib/api/dashboard";
import type { Language } from "../../lib/navigation";
import { DataCard } from "../cards/DataCard";
const EChart = dynamic(() => import("echarts-for-react"), {
  ssr: false,
  loading: () => (
    <div className="dc-chart-loading" role="status">
      Loading chart…
    </div>
  ),
});
type Palette = {
  gold: string;
  cyan: string;
  muted: string;
  border: string;
  surface: string;
  green: string;
  danger: string;
  font: string;
};
export function MarketChart({
  language,
  symbol = "BTC",
}: {
  language: Language;
  symbol?: string;
}) {
  const fa = language === "fa";
  const [range, setRange] = useState("1D");
  const [mode, setMode] = useState<"line" | "candlestick">("line");
  const [palette, setPalette] = useState<Palette | null>(null);
  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      const style = getComputedStyle(document.documentElement);
      const token = (name: string) =>
        style.getPropertyValue(`--ah-${name}`).trim();
      setPalette({
        gold: token("gold"),
        cyan: token("cyan"),
        muted: token("muted"),
        border: token("border"),
        surface: token("surface"),
        green: token("green"),
        danger: token("danger"),
        font: token("font"),
      });
    });
    return () => cancelAnimationFrame(raf);
  }, []);
  const asset =
    getMarkets().find((item) => item.symbol === symbol) ?? getMarkets()[0];
  const candles = useMemo(
    () =>
      getMarketCandles(symbol).slice(
        range === "6H" ? -12 : range === "12H" ? -24 : 0,
      ),
    [symbol, range],
  );
  const option = useMemo<EChartsOption>(() => {
    if (!palette) return {};
    return {
      animation: false,
      backgroundColor: "transparent",
      aria: {
        enabled: true,
        description: `${asset.name[language]} — DEMO. ${candles.length} synthetic price samples. Not live data.`,
      },
      textStyle: { fontFamily: palette.font },
      grid: { left: 58, right: 18, top: 15, bottom: 32 },
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        backgroundColor: palette.surface,
        borderColor: palette.border,
        textStyle: { color: palette.muted, fontSize: 10 },
      },
      xAxis: {
        type: "category",
        data: candles.map((item) => item.time),
        boundaryGap: mode === "candlestick",
        axisLine: { lineStyle: { color: palette.border } },
        axisTick: { show: false },
        axisLabel: {
          color: palette.muted,
          fontSize: 9,
          interval: Math.max(1, Math.floor(candles.length / 6)),
        },
      },
      yAxis: {
        type: "value",
        scale: true,
        splitNumber: 4,
        axisLabel: { color: palette.muted, fontSize: 9 },
        splitLine: { lineStyle: { color: palette.border, type: "dashed" } },
      },
      series:
        mode === "line"
          ? [
              {
                name: `${symbol} · DEMO`,
                type: "line",
                data: candles.map((item) => item.close),
                symbol: "none",
                smooth: 0.16,
                lineStyle: { width: 2, color: palette.cyan },
                areaStyle: {
                  color: {
                    type: "linear",
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [
                      { offset: 0, color: palette.cyan + "28" },
                      { offset: 1, color: palette.cyan + "00" },
                    ],
                  },
                },
              },
            ]
          : [
              {
                name: `${symbol} OHLC · DEMO`,
                type: "candlestick",
                data: candles.map((item) => [
                  item.open,
                  item.close,
                  item.low,
                  item.high,
                ]),
                itemStyle: {
                  color: palette.green,
                  color0: palette.danger,
                  borderColor: palette.green,
                  borderColor0: palette.danger,
                },
              },
            ],
    };
  }, [palette, candles, mode, asset.name, language, symbol]);
  return (
    <DataCard
      title={fa ? "نبض بازار" : "Market pulse"}
      icon="nav/market-prices"
      language={language}
      className="dc-market-chart"
      action={
        <div
          className="dc-segmented"
          aria-label={fa ? "نوع نمودار" : "Chart type"}
        >
          <button
            aria-pressed={mode === "line"}
            onClick={() => setMode("line")}
          >
            {fa ? "خطی" : "Line"}
          </button>
          <button
            aria-pressed={mode === "candlestick"}
            onClick={() => setMode("candlestick")}
          >
            {fa ? "شمعی" : "Candles"}
          </button>
        </div>
      }
    >
      <div className="dc-chart-topline">
        <div>
          <bdi className="dc-asset-title">
            {symbol}
            <span> / {asset.unit}</span>
          </bdi>
          <strong dir="ltr">
            {asset.price.toLocaleString("en-US", { maximumFractionDigits: 2 })}
            <small className={asset.change < 0 ? "dc-down" : "dc-up"}>
              {asset.change > 0 ? "+" : ""}
              {asset.change}%
            </small>
          </strong>
        </div>
        <div className="dc-segmented" dir="ltr">
          {["6H", "12H", "1D"].map((value) => (
            <button
              key={value}
              aria-pressed={range === value}
              onClick={() => setRange(value)}
            >
              {value}
            </button>
          ))}
        </div>
      </div>
      <div
        className="dc-chart-canvas"
        dir="ltr"
        aria-label={`${symbol} DEMO chart`}
      >
        {palette && (
          <EChart
            option={option}
            notMerge
            opts={{ renderer: "svg" }}
            style={{ height: 205, width: "100%" }}
          />
        )}
      </div>
      <div className="dc-chart-note">
        {fa
          ? "۱۶ اکتبر ۲۰۲۶ · دادهٔ ساختگی · نمودار جایگزین توصیهٔ مالی نیست"
          : "16 OCT 2026 · Synthetic series · Not financial advice"}
      </div>
    </DataCard>
  );
}
