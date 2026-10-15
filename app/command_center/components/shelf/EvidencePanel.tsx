"use client";

/**
 * M-D7 — the evidence graph, as a right-side panel.
 *
 * Presentation only (AGENTS.md). This reads `/api/command`'s
 * `canonicalDecisions` and draws the chain each of those decisions actually
 * passed through — identity, evidence, security, liquidity, score, risk,
 * confidence, decision — as a force graph. It is the canonical pipeline from
 * `AGENTS.md` laid out so a decision's *path* is visible, and it decides
 * nothing: the Python authority already decided, this just shows the walk.
 *
 * The layout is Apache ECharts' graph series (`layout: 'force'`), taken from
 * the owner's vendor kit (`vendor_assets/charts/echarts-6.1.0`, Apache-2.0)
 * rather than hand-written — a force simulation is exactly the kind of thing
 * the 18:00 rule says not to rebuild. Only the graph series, the tooltip and
 * the canvas renderer are imported, so the bundle carries those and not the
 * whole library.
 *
 * Colours come from `styleFor` — the same table TruthBadge renders — so a
 * REJECTED edge is the same colour in the graph as it is in the strip. The
 * palette cannot drift between the two surfaces because they read one object.
 *
 * No data is graph filler. If `canonicalDecisions` is empty the panel says so
 * in plain grey UNKNOWN text rather than drawing an empty force field, because
 * a graph of nothing is not a graph of UNKNOWN — it is nothing, and the
 * difference is worth stating.
 */
import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts/core";
import { GraphChart } from "echarts/charts";
import { TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import { webApiFetch } from "@/web_api_client";
import { badgeForState, styleFor } from "@/dashboard_truth_badge";
import { useStageStore } from "@/components/stage/store";
import type { RenderTier } from "@/components/stage/quality";

echarts.use([GraphChart, TooltipComponent, CanvasRenderer]);

/** The canonical pipeline spine, in order. AGENTS.md: identity → evidence →
 *  security → liquidity → score → risk → confidence → decision. */
const STAGES = [
  "identity",
  "evidence",
  "security",
  "liquidity",
  "score",
  "risk",
  "confidence",
  "decision",
] as const;

const STAGE_LABEL_FA: Record<string, string> = {
  identity: "هویت",
  evidence: "شواهد",
  security: "امنیت",
  liquidity: "نقدشوندگی",
  score: "امتیاز",
  risk: "ریسک",
  confidence: "اطمینان",
  decision: "تصمیم",
};

/** How many token nodes the graph lays out, by tier. Real canonical decisions
 *  are few, so this is a ceiling rather than a target — and a low one, because
 *  a force graph on an 8 GB machine pays per node. */
const NODE_CEIL: Record<RenderTier, number> = { T0: 0, T1: 12, T2: 40, T3: 120 };

interface CanonicalDecisionView {
  symbol: string | null;
  chain: string | null;
  identityState: string | null;
  securityState: string | null;
  confidence: string | null;
  outcome: string;
  opportunityScore: number | null;
  primaryReason: string | null;
}

interface GraphSlice {
  canonicalDecisions: CanonicalDecisionView[] | null;
}

/**
 * A CSS custom property, resolved to a real colour. ECharts draws on a canvas,
 * and a canvas context does not resolve `var(--…)` — the string is silently
 * ignored and the stroke falls back to black. Resolving through the computed
 * style keeps the tokens as the single source of truth and still hands the
 * chart a colour it can paint with. Re-read per build, so a theme switch
 * (imperial ↔ neon) reaches the graph.
 */
function cssVar(name: string): string {
  if (typeof window === "undefined") return "#9AA3B2";
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || "#9AA3B2";
}

/** The truth palette, so a REJECTED edge is the colour TruthBadge would show. */
function badgeColor(state: string | null | undefined): string {
  if (!state) return cssVar("--ahos-text-muted");
  return cssVar(styleFor(badgeForState(state)).colorVar);
}

/** Build the graph: the pipeline spine, plus one arm per decision. */
function buildGraph(decisions: CanonicalDecisionView[]) {
  const gold = cssVar("--ahos-gold");
  const panel = cssVar("--ahos-panel");
  const text = cssVar("--ahos-text");
  const border = cssVar("--ahos-border");
  // Built against permissive rows, not echarts' option types: echarts 6 does
  // not export the node/link item types, and its `data` union
  // (GraphNodeItemOption | GraphDataValue) rejects the per-node `tooltip` and
  // string `value` this graph carries. The runtime shapes are echarts' —
  // `setOption` is called under `EChartsCoreOption`, which absorbs them at
  // that one boundary. Presentation only; nothing here decides anything.
  const nodes: Record<string, unknown>[] = [];
  const links: Record<string, unknown>[] = [];

  // The spine: each stage chained to the next, in the canonical order.
  for (const stage of STAGES) {
    nodes.push({
      id: stage,
      name: STAGE_LABEL_FA[stage],
      symbolSize: 22,
      category: 0,
      label: { show: true, color: text },
      itemStyle: { color: panel, borderColor: gold },
    });
  }
  for (let i = 0; i < STAGES.length - 1; i++) {
    links.push({ source: STAGES[i], target: STAGES[i + 1], lineStyle: { color: border, width: 1 } });
  }

  // One arm per decision: the token, linked to the stages its record names a
  // state for, and to the decision node by its outcome.
  for (const d of decisions) {
    const id = d.symbol || d.chain || "token";
    if (nodes.some((n) => n.id === id)) continue;
    nodes.push({
      id,
      name: d.symbol ?? "؟",
      symbolSize: 14,
      category: 1,
      label: { show: true, color: text },
      itemStyle: { color: gold },
      tooltip: {
        formatter: `${d.symbol ?? "؟"} (${d.chain ?? "؟"}) — ${d.outcome}${d.primaryReason ? `\n${d.primaryReason}` : ""}`,
      },
    });
    for (const [state, stage] of [
      [d.identityState, "identity"],
      [d.securityState, "security"],
      [d.confidence, "confidence"],
    ] as const) {
      if (!state) continue;
      links.push({
        source: id,
        target: stage,
        value: state,
        lineStyle: { color: badgeColor(state), width: 1.5, opacity: 0.75 },
      });
    }
    links.push({
      source: id,
      target: "decision",
      value: d.outcome,
      lineStyle: { color: badgeColor(d.outcome), width: 2 },
    });
  }

  return { nodes, links };
}

export function EvidencePanel() {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const tier = useStageStore((s) => s.tier);
  const reducedMotion = useStageStore((s) => s.reducedMotion);
  const [decisions, setDecisions] = useState<CanonicalDecisionView[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void webApiFetch("/api/command")
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = (await res.json()) as GraphSlice;
        if (!cancelled) setDecisions(body.canonicalDecisions ?? []);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!ref.current) return;
    if (!chart.current) chart.current = echarts.init(ref.current);
    const ceil = NODE_CEIL[tier];
    const rows = decisions === null ? [] : decisions.slice(0, ceil);
    const { nodes, links } = buildGraph(rows);
    const option: echarts.EChartsCoreOption = {
      animation: !reducedMotion && tier !== "T1",
      // The panel's own background comes from the DOM; the chart is transparent
      // so it cannot disagree with it.
      backgroundColor: "transparent",
      tooltip: {
        confine: true,
        backgroundColor: cssVar("--ahos-panel"),
        borderColor: cssVar("--ahos-border"),
        textStyle: { color: cssVar("--ahos-text") },
      },
      // No legend: two node kinds are already distinguished by size and colour,
      // and an unregistered legend component would warn on every load.
      series: [
        {
          type: "graph",
          layout: "force",
          roam: true,
          // Still unless the tier allows motion; a roaming graph on T1 is not
          // what the low tier's budget is for.
          force: {
            repulsion: reducedMotion ? 0 : 260,
            edgeLength: [50, 120],
            gravity: 0.09,
            layoutAnimation: !reducedMotion && tier !== "T1",
          },
          emphasis: { focus: "adjacency" },
          categories: [
            { name: "مرحلهٔ خط لوله" },
            { name: "توکن" },
          ],
          data: nodes,
          links,
          lineStyle: { curveness: 0.18 },
        },
      ],
    };
    chart.current.setOption(option, true);
  }, [decisions, tier, reducedMotion]);

  useEffect(() => {
    const onResize = () => void chart.current?.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <aside className="evidence-panel" dir="rtl" lang="fa" aria-label="گرافِ شواهد">
      <h2 className="evidence-panel__title">گرافِ شواهد</h2>
      <p className="evidence-panel__hint">
        خط لولهٔ کانونیکال: هویت ← شواهد ← امنیت ← نقدشوندگی ← امتیاز ← ریسک ←
        اطمینان ← تصمیم. هر توکن به مرحله‌ای می‌رسد که رکوردش حالتی برایش دارد.
      </p>
      {failed ? (
        <p className="evidence-panel__unknown">
          <span className="evidence-panel__unknown-glyph">؟</span>
          شواهد بارگذاری نشد — پاسخِ API در دسترس نیست.
        </p>
      ) : decisions !== null && decisions.length === 0 ? (
        <p className="evidence-panel__unknown">
          <span className="evidence-panel__unknown-glyph">؟</span>
          هیچ تصمیمِ کانونیکالی در مدلِ خواندنی نیست. گراف خالی است، نه ناشناخته.
        </p>
      ) : (
        <div ref={ref} className="evidence-panel__canvas" role="img" aria-label="گرافِ نیروی شواهد" />
      )}
    </aside>
  );
}
