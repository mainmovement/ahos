"use client";

import { useMemo } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { BarChart, CandlestickChart, GraphChart, LineChart, PieChart, ScatterChart, TreemapChart } from "echarts/charts";
import {
  AxisPointerComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { useSettings } from "@/lib/settings/provider";
import { alpha, readChartPalette, type ChartPalette } from "@/lib/tokens";
import { cn } from "@/lib/utils";

echarts.use([
  LineChart,
  BarChart,
  CandlestickChart,
  PieChart,
  GraphChart,
  TreemapChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  AxisPointerComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

export interface ChartContext {
  p: ChartPalette;
  rtl: boolean;
  reduced: boolean;
  /** Shared tooltip styling (glass, RTL-aware). */
  tooltip: Record<string, unknown>;
  axisLabel: Record<string, unknown>;
  splitLine: Record<string, unknown>;
  axisLine: Record<string, unknown>;
}

/** Build token-driven chart styling. Charts read colours from tokens.css at runtime. */
export function useChartContext(): ChartContext {
  const { settings, reducedMotion } = useSettings();
  const rtl = settings.locale === "fa";
  return useMemo(() => {
    const p = readChartPalette();
    return {
      p,
      rtl,
      reduced: reducedMotion,
      tooltip: {
        backgroundColor: "rgba(9, 15, 29, 0.94)",
        borderColor: alpha(p.gold, 0.28),
        borderWidth: 1,
        padding: [8, 10],
        textStyle: { color: p.fg2, fontFamily: p.fontFamily, fontSize: 11 },
        extraCssText: `border-radius: 10px; box-shadow: 0 18px 40px -16px rgba(0,0,0,.9); direction: ${rtl ? "rtl" : "ltr"}; text-align: ${rtl ? "right" : "left"};`,
        className: "echarts-tooltip-ahos",
      },
      axisLabel: { color: p.fg4, fontFamily: p.fontFamily, fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.045)" } },
      axisLine: { lineStyle: { color: alpha(p.gold, 0.16) } },
    };
    // settings.theme changes CSS variables → re-read palette
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rtl, reducedMotion, settings.theme]);
}

interface EChartProps {
  option: EChartsCoreOption;
  className?: string;
  height?: number | string;
  label: string;
  onEvents?: Record<string, (params: unknown) => void>;
}

/**
 * Tree-shaken ECharts wrapper (echarts/core + echarts-for-react/lib/core).
 * Rendered on the canvas renderer; the container gets an ARIA label summary.
 */
export function EChart({ option, className, height = 260, label, onEvents }: EChartProps) {
  const { reducedMotion } = useSettings();
  const finalOption = useMemo(() => ({ animation: !reducedMotion, animationDuration: 600, animationEasing: "cubicOut", ...option }), [option, reducedMotion]);
  return (
    <div role="img" aria-label={label} className={cn("relative w-full", className)} style={{ height }}>
      <ReactEChartsCore
        echarts={echarts}
        option={finalOption}
        notMerge
        lazyUpdate
        style={{ height: "100%", width: "100%" }}
        opts={{ renderer: "canvas" }}
        onEvents={onEvents}
      />
    </div>
  );
}
