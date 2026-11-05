"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle } from "@/lib/data/series";

/**
 * Candlestick view (TradingView Lightweight Charts v4).
 * Time axis stays LTR in both locales — the captions around it are localized.
 */
export function CandleChart({
  bars,
  upColor = "#22C55E",
  downColor = "#EF4444",
  height = 320,
}: {
  bars: Candle[];
  upColor?: string;
  downColor?: string;
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94A3B8",
        fontSize: 11,
        fontFamily: "InterVar, Inter, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(36, 52, 88, 0.5)" },
        horzLines: { color: "rgba(36, 52, 88, 0.5)" },
      },
      rightPriceScale: { borderColor: "rgba(36, 52, 88, 1)" },
      timeScale: { borderColor: "rgba(36, 52, 88, 1)", timeVisible: false },
      crosshair: { mode: 0 },
      localization: {
        priceFormatter: (p: number) => p.toLocaleString("en-US", { maximumFractionDigits: 2 }),
      },
    });
    chartRef.current = chart;

    const series = chart.addCandlestickSeries({
      upColor,
      downColor,
      borderUpColor: upColor,
      borderDownColor: downColor,
      wickUpColor: upColor,
      wickDownColor: downColor,
    });
    series.setData(
      bars.map((b) => ({
        time: (Date.parse(`${b.time}T00:00:00Z`) / 1000) as UTCTimestamp,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );
    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    ro.observe(container);
    chart.applyOptions({ width: container.clientWidth });

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [bars, upColor, downColor, height]);

  return <div ref={containerRef} className="w-full" dir="ltr" />;
}
