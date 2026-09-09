import { notFound } from "next/navigation";
import {
  BookOpen, Droplets, GitBranch, Mountain, MoveLeft, MoveRight, Network,
  Recycle, RefreshCcw, Satellite, Scale, Sprout, Target, Trophy,
} from "lucide-react";
import { getTreeView } from "@/lib/engine";
import { getDict, isLocale, type Locale } from "@/lib/dict";
import { fmtInt, timeAgo } from "@/lib/format";
import Reveal from "@/components/reveal";
import Counter from "@/components/counter";
import TreeCanvas from "@/components/tree-canvas";
import { Kicker, Panel } from "@/components/primitives";
import { cx, type Tone } from "@/lib/ui";

export const dynamic = "force-dynamic";

const EVENT_ICON: Record<string, { icon: typeof Trophy; tone: Tone }> = {
  GOLDEN_FRUIT: { icon: Trophy, tone: "gold" },
  FRUIT: { icon: Sprout, tone: "jade" },
  WATER: { icon: Droplets, tone: "cyan" },
  ROCK: { icon: Mountain, tone: "rose" },
  LESSON: { icon: Recycle, tone: "violet" },
  ROOT: { icon: Network, tone: "jade" },
  BRANCH: { icon: GitBranch, tone: "sky" },
  NEW_SOURCE: { icon: Satellite, tone: "jade" },
};

const LEGEND_META: { key: "roots" | "water" | "rocks" | "branches" | "leaves" | "fruit" | "goldenFruit"; hex: string }[] = [
  { key: "roots", hex: "#34d399" },
  { key: "water", hex: "#67e8f9" },
  { key: "rocks", hex: "#fb7185" },
  { key: "branches", hex: "#a78bfa" },
  { key: "leaves", hex: "#6ee7b7" },
  { key: "fruit", hex: "#34d399" },
  { key: "goldenFruit", hex: "#f5b73f" },
];

export default async function WiseTreePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const loc: Locale = locale;
  const dict = getDict(loc);
  const fa = loc === "fa";
  const { events, vitals } = await getTreeView();
  const LoopArrow = fa ? MoveLeft : MoveRight;

  const vitalChips = [
    { v: vitals.healthyRoots, l: dict.tree.legend.roots.split("—")[0] },
    { v: vitals.rocks, l: dict.tree.legend.rocks.split("—")[0] },
    { v: vitals.branches, l: dict.tree.legend.branches.split("—")[0] },
    { v: vitals.leaves, l: dict.tree.legend.leaves.split("—")[0] },
    { v: vitals.water, l: dict.tree.legend.water.split("—")[0] },
    { v: vitals.fruits, l: dict.tree.legend.fruit.split("—")[0] },
    { v: vitals.goldenFruits, l: dict.tree.legend.goldenFruit.split("—")[0] },
  ];

  const loop = [
    { icon: BookOpen, label: dict.tree.loop.knowledge, tone: "sky" as Tone },
    { icon: Scale, label: dict.tree.loop.decision, tone: "violet" as Tone },
    { icon: Target, label: dict.tree.loop.result, tone: "gold" as Tone },
    { icon: RefreshCcw, label: dict.tree.loop.learning, tone: "jade" as Tone },
  ];

  return (
    <div className="mx-auto max-w-7xl px-5 pb-10">
      <header className="py-12 text-center">
        <Reveal>
          <div className="flex justify-center">
            <Kicker tone="gold">{dict.tree.kicker}</Kicker>
          </div>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">
            <span className="text-grad-gold">{dict.tree.title}</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-mist">{dict.tree.sub}</p>
        </Reveal>
      </header>

      {/* vitals */}
      <Reveal delay={80}>
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-7">
          {vitalChips.map((c) => (
            <div key={c.l} className="glass-soft rounded-2xl px-2 py-3 text-center">
              <Counter locale={loc} value={c.v} className="num block text-2xl font-black text-frost" />
              <span className="mt-1 block text-[9.5px] leading-4 text-mist">{c.l}</span>
            </div>
          ))}
        </div>
      </Reveal>

      {/* the tree */}
      <Reveal delay={140}>
        <Panel hover={false} className="mt-6 overflow-hidden !p-2">
          <TreeCanvas vitals={vitals} />
        </Panel>
      </Reveal>

      {/* legend */}
      <Reveal delay={180}>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          {LEGEND_META.map((m) => (
            <span key={m.key} className="glass-soft inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[10.5px] font-semibold text-frost/80">
              <span className="size-2 rounded-full" style={{ background: m.hex, boxShadow: `0 0 8px ${m.hex}` }} />
              {dict.tree.legend[m.key]}
            </span>
          ))}
        </div>
      </Reveal>

      <div className="mt-14 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        {/* growth events */}
        <Reveal>
          <Panel hover={false} className="h-full">
            <h2 className="text-xl font-black"><span className="text-grad-jade">{dict.tree.growth}</span></h2>
            <div className="mt-6 space-y-0">
              {events.map((e, i) => {
                const meta = EVENT_ICON[e.kind] ?? EVENT_ROOT_DEFAULT;
                return (
                  <div key={e.id} className="relative flex gap-4 pb-6 last:pb-0">
                    {i < events.length - 1 ? (
                      <span className="absolute start-[15px] top-9 h-full w-px bg-white/8" />
                    ) : null}
                    <span
                      className="relative z-10 grid size-8 shrink-0 place-items-center rounded-xl border"
                      style={{
                        background: "rgba(255,255,255,0.03)",
                        borderColor: `${toneHex(meta.tone)}55`,
                      }}
                    >
                      <meta.icon className="size-3.5" style={{ color: toneHex(meta.tone) }} />
                    </span>
                    <div className="grow">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[13px] font-extrabold text-frost">{fa ? e.titleFa : e.titleEn}</span>
                        <span className="text-[10px] text-mist/70">{timeAgo(loc, e.createdAt)}</span>
                      </div>
                      <p className="mt-1 text-[12px] leading-6 text-mist">{fa ? e.detailFa : e.detailEn}</p>
                    </div>
                    <span className="num shrink-0 text-[10px] font-black text-mist/60">+{fmtInt(loc, e.weight)}</span>
                  </div>
                );
              })}
            </div>
          </Panel>
        </Reveal>

        {/* impact loop */}
        <Reveal delay={100}>
          <Panel hover={false} className="flex h-full flex-col">
            <h2 className="text-xl font-black"><span className="text-grad-gold">{dict.tree.loopTitle}</span></h2>
            <div className="mt-8 flex items-center justify-between gap-1">
              {loop.map((s, i) => (
                <div key={s.label} className="flex items-center gap-1">
                  <div className="flex flex-col items-center gap-2">
                    <span
                      className="grid size-14 place-items-center rounded-2xl border"
                      style={{ borderColor: `${toneHex(s.tone)}55`, background: `${toneHex(s.tone)}14` }}
                    >
                      <s.icon className="size-5" style={{ color: toneHex(s.tone) }} />
                    </span>
                    <span className="text-[10.5px] font-bold text-frost/80">{s.label}</span>
                  </div>
                  {i < loop.length - 1 ? <LoopArrow className="mx-1 size-4 shrink-0 text-mist/60" /> : null}
                </div>
              ))}
            </div>
            <div className="mt-auto space-y-3 pt-8">
              <div className="rounded-2xl border border-jade-400/20 bg-jade-400/[0.05] p-4 text-[12px] leading-6 text-mist">
                <span className="mb-1 block font-extrabold text-jade-300">{dict.learning.positive}</span>
                {fa ? "«سکوت پیش از موج» سه بار از چهار بار به میوه تبدیل شد — شاخهٔ زنجیره قوی‌تر شد." : "“Silence before the wave” hit 3 of 4 times — the on-chain branch grew stronger."}
              </div>
              <div className="rounded-2xl border border-flare/25 bg-flare/[0.05] p-4 text-[12px] leading-6 text-mist">
                <span className="mb-1 block font-extrabold text-flare">{dict.learning.failure}</span>
                {fa ? "«فریب انباشت نهنگی» از شکست TIRO ثبت شد — برگ پوسیده شد و خاک حاصل‌خیزتر گردید." : "“Whale-accumulation spoof” was recorded after the TIRO loss — a leaf composted into richer soil."}
              </div>
              <p className="pt-2 text-center text-[10.5px] text-mist/70">{dict.tree.notDecider}</p>
            </div>
          </Panel>
        </Reveal>
      </div>
    </div>
  );
}

const EVENT_ROOT_DEFAULT = { icon: Network, tone: "jade" as Tone };

function toneHex(t: Tone): string {
  return {
    gold: "#f5b73f", jade: "#34d399", rose: "#fb7185", sky: "#7dd3fc",
    violet: "#c4b5fd", amber: "#fbbf24", zinc: "#a1a1aa", cyan: "#67e8f9",
  }[t];
}
