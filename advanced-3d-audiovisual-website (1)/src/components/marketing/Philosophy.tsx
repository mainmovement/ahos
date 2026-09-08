"use client";

import { motion } from "framer-motion";
import { RevealCard } from "@/components/ui/Card";

const layers = [
  { title: "Roots", subtitle: "Data Sources", desc: "Market data, blockchains, social platforms, news, GitHub — every root searches independently for water." },
  { title: "Soil", subtitle: "Internet & Markets", desc: "The medium every root must push through — noisy, chaotic, and full of obstacles." },
  { title: "Stones", subtitle: "Errors & Failures", desc: "Blocked APIs, bad models, wrong assumptions. Roots don't stop — they redirect." },
  { title: "Groundwater", subtitle: "Deep Knowledge", desc: "Verified, cross-referenced intelligence the system can actually stand on." },
  { title: "Ocean", subtitle: "Collective Intelligence", desc: "The deep reserve every root is ultimately reaching toward." },
  { title: "Golden Fruit", subtitle: "Exceptional Opportunity", desc: "From a thousand candidates, the rare few worth the council's full attention." },
];

export function Philosophy() {
  return (
    <section id="philosophy" className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-violet-300">The Central Metaphor</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            AHOS grows like the <span className="text-gradient">Wise Tree.</span>
          </h2>
          <p className="mt-5 max-w-2xl text-slate-300">
            Every root that hits a stone doesn&apos;t fail — it redirects. Every obstacle is data, not defeat.
            The system&apos;s philosophy: grow deeper before you grow wider, and never mistake motion for knowledge.
          </p>
        </RevealCard>

        <div className="relative mt-20">
          <div className="absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-white/15 to-transparent lg:block" />
          <div className="grid gap-6 lg:grid-cols-3">
            {layers.map((layer, i) => (
              <RevealCard key={layer.title} delay={i * 0.08}>
                <motion.div
                  whileHover={{ y: -6 }}
                  className="glass noise-border group relative h-full rounded-2xl p-6"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full border border-cyan-300/30 font-display text-sm text-cyan-300">
                    {i + 1}
                  </div>
                  <h3 className="font-display text-lg font-semibold text-white">{layer.title}</h3>
                  <p className="mt-1 text-xs uppercase tracking-wider text-violet-300">{layer.subtitle}</p>
                  <p className="mt-3 text-sm leading-relaxed text-slate-400">{layer.desc}</p>
                </motion.div>
              </RevealCard>
            ))}
          </div>
        </div>

        <RevealCard delay={0.2} className="mt-16">
          <div className="glass-strong noise-border rounded-3xl p-8 text-center sm:p-12">
            <p className="mx-auto max-w-3xl font-display text-xl leading-relaxed text-slate-100 sm:text-2xl">
              &ldquo;Every obstacle is not a failure — it&apos;s data. Every success is not just profit — it&apos;s a lesson.
              Every loss is not just a loss — it&apos;s an experiment.&rdquo;
            </p>
          </div>
        </RevealCard>
      </div>
    </section>
  );
}
