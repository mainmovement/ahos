"use client";

/**
 * Domain charts built on <EChart>. All colours come from tokens via
 * useChartContext(). Time axes are NOT mirrored in RTL (chronology reads
 * left→right, matching financial-terminal convention); chart chrome (legend,
 * tooltip text alignment) follows the UI direction.
 */
import { useMemo } from "react";
import type { Candle, NamedSeries, SeriesPoint } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { alpha } from "@/lib/tokens";
import { EChart, useChartContext } from "./echart";

/* ----------------------------------------------------------- candles */

export function CandlesChart({ candles, height = 320, label, mode = "candles", showVolume = true, decimals = 2 }: { candles: Candle[]; height?: number; label: string; mode?: "candles" | "line"; showVolume?: boolean; decimals?: number }) {
  const c = useChartContext();
  const f = useFormat();
  const option = useMemo(() => {
    const { p } = c;
    const times = candles.map((k) => k.t);
    const closes = candles.map((k) => k.c);
    const ma = (n: number) => closes.map((_, i) => (i < n - 1 ? null : closes.slice(i - n + 1, i + 1).reduce((a, b) => a + b, 0) / n));
    const ohlc = candles.map((k) => [k.o, k.c, k.l, k.h]);
    const vols = candles.map((k) => ({ value: k.v, itemStyle: { color: k.c >= k.o ? alpha(p.up, 0.35) : alpha(p.down, 0.35) } }));
    return {
      backgroundColor: "transparent",
      grid: showVolume
        ? [
            { left: 8, right: 64, top: 12, height: "66%" },
            { left: 8, right: 64, top: "80%", bottom: 26 },
          ]
        : [{ left: 8, right: 64, top: 12, bottom: 26 }],
      tooltip: {
        ...c.tooltip,
        trigger: "axis",
        axisPointer: { type: "cross", lineStyle: { color: alpha(p.gold, 0.45) }, crossStyle: { color: alpha(p.gold, 0.45) }, label: { backgroundColor: p.panel, color: p.fg1, borderColor: alpha(p.gold, 0.4), borderWidth: 1 } },
        valueFormatter: (v: number) => f.num(v, decimals),
      },
      axisPointer: { link: [{ xAxisIndex: "all" }] },
      xAxis: [
        { type: "category", data: times, boundaryGap: true, axisLine: c.axisLine, axisTick: { show: false }, axisLabel: { ...c.axisLabel, formatter: (v: string) => f.date(Number(v)) }, splitLine: { show: false }, gridIndex: 0, inverse: false },
        ...(showVolume ? [{ type: "category", data: times, gridIndex: 1, axisLabel: { show: false }, axisLine: c.axisLine, axisTick: { show: false } }] : []),
      ],
      yAxis: [
        { scale: true, position: "right", axisLabel: { ...c.axisLabel, formatter: (v: number) => f.num(v, decimals) }, splitLine: c.splitLine, axisLine: { show: false }, gridIndex: 0 },
        ...(showVolume ? [{ scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, splitLine: { show: false }, axisLine: { show: false } }] : []),
      ],
      dataZoom: [{ type: "inside", xAxisIndex: showVolume ? [0, 1] : [0], start: 35, end: 100 }],
      series: [
        mode === "candles"
          ? {
              name: label,
              type: "candlestick",
              data: ohlc,
              itemStyle: { color: p.up, color0: p.down, borderColor: p.up, borderColor0: p.down },
              barMaxWidth: 9,
            }
          : {
              name: label,
              type: "line",
              data: closes,
              showSymbol: false,
              lineStyle: { color: p.data, width: 1.6 },
              areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(p.data, 0.28) }, { offset: 1, color: alpha(p.data, 0) }] } },
            },
        { name: "MA20", type: "line", data: ma(20), showSymbol: false, smooth: true, lineStyle: { color: alpha(p.gold, 0.85), width: 1.1 } },
        { name: "MA50", type: "line", data: ma(50), showSymbol: false, smooth: true, lineStyle: { color: alpha(p.violet, 0.7), width: 1, type: "dashed" } },
        ...(showVolume ? [{ name: "Vol", type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: vols, barMaxWidth: 8 }] : []),
      ],
    };
  }, [c, f, candles, label, mode, showVolume, decimals]);
  return <EChart option={option} height={height} label={label} />;
}

/* -------------------------------------------------------------- lines */

export function LinesChart({ series, height = 240, label, area = false, normalize = false, valueFormat, percentAxis = false }: { series: NamedSeries[]; height?: number; label: string; area?: boolean; normalize?: boolean; valueFormat?: (v: number) => string; percentAxis?: boolean }) {
  const c = useChartContext();
  const f = useFormat();
  const { l } = useI18n();
  const option = useMemo(() => {
    const { p } = c;
    const colors = [p.data, p.gold, p.violet, p.info, p.up];
    const fmt = valueFormat ?? ((v: number) => (percentAxis ? f.pct(v, 1) : f.num(v, 2)));
    return {
      backgroundColor: "transparent",
      color: colors,
      grid: { left: 8, right: 56, top: series.length > 1 ? 30 : 12, bottom: 24 },
      legend: series.length > 1 ? { top: 0, [c.rtl ? "right" : "left"]: 0, icon: "roundRect", itemWidth: 10, itemHeight: 3, textStyle: { color: p.fg3, fontFamily: p.fontFamily, fontSize: 10 } } : undefined,
      tooltip: { ...c.tooltip, trigger: "axis", valueFormatter: fmt, axisPointer: { lineStyle: { color: alpha(p.gold, 0.4) } } },
      xAxis: { type: "time", axisLine: c.axisLine, axisTick: { show: false }, axisLabel: { ...c.axisLabel, formatter: (v: number) => f.date(v), hideOverlap: true }, splitLine: { show: false } },
      yAxis: { type: "value", scale: true, position: "right", axisLabel: { ...c.axisLabel, formatter: fmt }, splitLine: c.splitLine },
      series: series.map((s, i) => {
        const base = s.points[0]?.v ?? 1;
        const data = s.points.map((pt) => [pt.t, normalize ? ((pt.v - base) / base) * 100 : pt.v]);
        const color = colors[i % colors.length]!;
        return {
          name: l(s.label),
          type: "line",
          data,
          showSymbol: false,
          smooth: 0.25,
          lineStyle: { width: i === 0 ? 1.8 : 1.3, color },
          areaStyle: area && i === 0 ? { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(color, 0.26) }, { offset: 1, color: alpha(color, 0) }] } } : undefined,
          emphasis: { focus: "series" },
        };
      }),
    };
  }, [c, f, l, series, area, normalize, valueFormat, percentAxis]);
  return <EChart option={option} height={height} label={label} />;
}

export function AreaSeriesChart({ points, height = 160, label, color }: { points: SeriesPoint[]; height?: number; label: string; color?: "data" | "gold" | "up" | "down" }) {
  const c = useChartContext();
  const f = useFormat();
  const option = useMemo(() => {
    const { p } = c;
    const col = color === "gold" ? p.gold : color === "up" ? p.up : color === "down" ? p.down : p.data;
    return {
      backgroundColor: "transparent",
      grid: { left: 4, right: 44, top: 8, bottom: 20 },
      tooltip: { ...c.tooltip, trigger: "axis", valueFormatter: (v: number) => f.num(v, 2) },
      xAxis: { type: "time", axisLine: c.axisLine, axisTick: { show: false }, axisLabel: { ...c.axisLabel, formatter: (v: number) => f.time(v), hideOverlap: true }, splitLine: { show: false } },
      yAxis: { type: "value", scale: true, position: "right", axisLabel: { ...c.axisLabel, formatter: (v: number) => f.compact(v, 1) }, splitLine: c.splitLine },
      series: [
        {
          type: "line",
          data: points.map((pt) => [pt.t, pt.v]),
          showSymbol: false,
          smooth: 0.3,
          lineStyle: { color: col, width: 1.5 },
          areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(col, 0.3) }, { offset: 1, color: alpha(col, 0) }] } },
        },
      ],
    };
  }, [c, f, points, color]);
  return <EChart option={option} height={height} label={label} />;
}

/* --------------------------------------------------------------- bars */

export function BarsChart({ categories, values, height = 200, label, signed = false, horizontal = false, unit = "", decimals = 1 }: { categories: string[]; values: (number | null)[]; height?: number; label: string; signed?: boolean; horizontal?: boolean; unit?: string; decimals?: number }) {
  const c = useChartContext();
  const f = useFormat();
  const option = useMemo(() => {
    const { p } = c;
    const data = values.map((v) => ({
      value: v,
      itemStyle: {
        color: v === null ? alpha(p.violet, 0.25) : signed ? (v >= 0 ? alpha(p.up, 0.75) : alpha(p.down, 0.75)) : { type: "linear", x: 0, y: 0, x2: horizontal ? 1 : 0, y2: horizontal ? 0 : 1, colorStops: [{ offset: 0, color: p.goldSoft }, { offset: 1, color: alpha(p.goldDeep, 0.5) }] },
        borderRadius: horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0],
      },
    }));
    const catAxis = { type: "category", data: categories, axisLine: c.axisLine, axisTick: { show: false }, axisLabel: { ...c.axisLabel, interval: 0, hideOverlap: true }, inverse: horizontal && c.rtl ? false : horizontal };
    const valAxis = { type: "value", axisLabel: { ...c.axisLabel, formatter: (v: number) => `${f.num(v, decimals)}${unit}` }, splitLine: c.splitLine, position: horizontal ? undefined : "right" };
    return {
      backgroundColor: "transparent",
      grid: horizontal ? { left: 8, right: 16, top: 6, bottom: 18, containLabel: true } : { left: 8, right: 48, top: 10, bottom: 22 },
      tooltip: { ...c.tooltip, trigger: "axis", axisPointer: { type: "shadow", shadowStyle: { color: alpha(p.gold, 0.06) } }, valueFormatter: (v: number | null) => (v === null ? "—" : `${f.num(v, decimals)}${unit}`) },
      xAxis: horizontal ? valAxis : catAxis,
      yAxis: horizontal ? catAxis : valAxis,
      series: [{ type: "bar", data, barMaxWidth: 18 }],
    };
  }, [c, f, categories, values, signed, horizontal, unit, decimals]);
  return <EChart option={option} height={height} label={label} />;
}

/* -------------------------------------------------------------- donut */

export function DonutChart({ items, height = 200, label, centerLabel }: { items: { name: string; value: number }[]; height?: number; label: string; centerLabel?: string }) {
  const c = useChartContext();
  const f = useFormat();
  const option = useMemo(() => {
    const { p } = c;
    const colors = [alpha(p.fg3, 0.55), p.data, p.gold, p.violet, p.info, p.up];
    return {
      backgroundColor: "transparent",
      color: colors,
      tooltip: { ...c.tooltip, trigger: "item", valueFormatter: (v: number) => f.usd(v, 0) },
      series: [
        {
          type: "pie",
          radius: ["62%", "84%"],
          center: ["50%", "50%"],
          padAngle: 2,
          itemStyle: { borderRadius: 4, borderColor: p.bg, borderWidth: 1 },
          label: { show: !!centerLabel, position: "center", formatter: () => centerLabel ?? "", color: p.fg1, fontFamily: p.fontFamily, fontSize: 13, fontWeight: 600 },
          labelLine: { show: false },
          data: items,
        },
      ],
    };
  }, [c, f, items, centerLabel]);
  return <EChart option={option} height={height} label={label} />;
}

/* -------------------------------------------------------------- graph */

export function NetworkGraph({ nodes, links, height = 420, label, categories }: { nodes: { id: string; name: string; category: number; value: number }[]; links: { source: string; target: string; value: number }[]; height?: number; label: string; categories: string[] }) {
  const c = useChartContext();
  const option = useMemo(() => {
    const { p } = c;
    const catColors = [p.gold, p.data, p.violet, p.info, p.up];
    return {
      backgroundColor: "transparent",
      tooltip: { ...c.tooltip, trigger: "item" },
      legend: { bottom: 0, data: categories, textStyle: { color: p.fg3, fontFamily: p.fontFamily, fontSize: 10 }, icon: "circle", itemWidth: 8, itemHeight: 8 },
      series: [
        {
          type: "graph",
          layout: "force",
          roam: true,
          draggable: true,
          animation: !c.reduced,
          force: { repulsion: 210, edgeLength: [50, 120], gravity: 0.08, friction: 0.2, layoutAnimation: !c.reduced },
          categories: categories.map((name, i) => ({ name, itemStyle: { color: catColors[i % catColors.length] } })),
          data: nodes.map((n) => ({
            id: n.id,
            name: n.name,
            category: n.category,
            value: n.value,
            symbolSize: 8 + Math.sqrt(n.value) * 3.2,
            itemStyle: { shadowBlur: 16, shadowColor: alpha(catColors[n.category % catColors.length]!, 0.6), borderColor: alpha("#ffffff", 0.35), borderWidth: 0.6 },
            label: { show: n.value >= 30, color: p.fg2, fontFamily: p.fontFamily, fontSize: 10, position: "right" },
          })),
          links: links.map((l) => ({ source: l.source, target: l.target, value: l.value, lineStyle: { width: 0.6 + l.value * 0.18, color: alpha(p.data, 0.35), curveness: 0.12 } })),
          emphasis: { focus: "adjacency", lineStyle: { width: 2.4, color: p.data } },
          lineStyle: { opacity: 0.9 },
        },
      ],
    };
  }, [c, nodes, links, categories]);
  return <EChart option={option} height={height} label={label} />;
}

/* ------------------------------------------------------------ treemap */

export function SectorTreemap({ items, height = 260, label }: { items: { name: string; weight: number; change: number | null }[]; height?: number; label: string }) {
  const c = useChartContext();
  const f = useFormat();
  const option = useMemo(() => {
    const { p } = c;
    const colorFor = (chg: number | null) => {
      if (chg === null) return alpha(p.violet, 0.22);
      const a = Math.min(0.85, 0.18 + Math.abs(chg) / 4);
      return chg >= 0 ? alpha(p.up, a) : alpha(p.down, a);
    };
    return {
      backgroundColor: "transparent",
      tooltip: { ...c.tooltip, formatter: (info: { name: string; data: { change: number | null } }) => `${info.name}: ${f.pct(info.data.change)}` },
      series: [
        {
          type: "treemap",
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          width: "100%",
          height: "100%",
          itemStyle: { borderColor: p.bg, borderWidth: 2, gapWidth: 2, borderRadius: 4 },
          label: {
            show: true,
            formatter: (info: { name: string; data: { change: number | null } }) => `{n|${info.name}}\n{c|${f.pct(info.data.change)}}`,
            rich: {
              n: { color: p.fg1, fontFamily: p.fontFamily, fontSize: 11, fontWeight: 600, lineHeight: 16 },
              c: { color: p.fg2, fontFamily: p.fontFamily, fontSize: 10 },
            },
          },
          data: items.map((it) => ({ name: it.name, value: it.weight, change: it.change, itemStyle: { color: colorFor(it.change) } })),
        },
      ],
    };
  }, [c, f, items]);
  return <EChart option={option} height={height} label={label} />;
}
