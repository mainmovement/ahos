"use client";

import { useEffect, useState } from "react";
import { MEDIA, TEAMS } from "@/lib/constants";
import { SoundButton } from "@/components/sound-button";
import { VoidScene } from "@/components/void-scene";
import { useAudio } from "@/components/providers";

export function Landing() {
  const audio = useAudio();
  const [boot, setBoot] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setBoot(false), 2200);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="relative bg-[#05070b] text-[#efe6d6]">
      <div className="vignette" />
      {boot && (
        <div className="fixed inset-0 z-[90] grid place-items-center bg-[#05070b]">
          <div className="text-center">
            <div className="loader-ring mx-auto" />
            <p className="kicker mt-6">Initializing roots</p>
            <h2 className="font-display mt-3 text-4xl italic gold-text">AHOS</h2>
            <p className="mt-2 font-mono text-xs text-[#f3d5a0]/50">EVIDENCE BEFORE DECISION</p>
          </div>
        </div>
      )}

      <section className="relative min-h-screen overflow-hidden">
        <div className="absolute inset-0">
          <img src="/images/hero.jpg" alt="" className="hero-mask h-full w-full object-cover opacity-50" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#05070b]/30 via-[#05070b]/40 to-[#05070b]" />
          <VoidScene />
        </div>
        <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col justify-end px-6 pb-20 pt-28">
          <p className="kicker">Artificial Hybrid Opportunity Scoring System</p>
          <h1 className="font-display mt-5 max-w-5xl text-[clamp(3.4rem,12vw,9.5rem)] leading-[0.78] italic">
            <span className="gold-text">Find the fruit.</span>
            <br />
            Refuse the trap.
          </h1>
          <p className="mt-8 max-w-xl text-lg text-[#efe6d6]/75">
            AHOS is not a trading bot. It is a searching, questioning, risk-gating intelligence that scores
            emerging tokens with evidence — then learns from every win, loss, and skip.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <SoundButton href="/dashboard" tone="gold" sound="enter" className="px-8 py-4 text-base">
              Enter the chamber
            </SoundButton>
            <SoundButton href="/tokens" tone="ghost" className="px-8 py-4 text-base">
              Open discovery
            </SoundButton>
            <SoundButton tone="ghost" className="px-8 py-4 text-base" onClick={audio.toggle}>
              {audio.enabled ? "Mute the void" : "Hear the void"}
            </SoundButton>
          </div>
        </div>
      </section>

      <section className="relative mx-auto grid max-w-6xl gap-10 px-6 py-28 md:grid-cols-2">
        <div>
          <p className="kicker">Doctrine</p>
          <h2 className="font-display mt-3 text-5xl italic leading-tight">Evidence before decision.</h2>
          <p className="mt-5 text-[#efe6d6]/70">
            A tweet is not a market. A Telegram rumor is not liquidity. A pump is not a thesis. AHOS collects
            independent sources, tags the unverified, and lets security veto opportunity.
          </p>
        </div>
        <div className="panel relative overflow-hidden rounded-3xl p-0">
          <img src={MEDIA.roots} alt="Roots" className="h-80 w-full object-cover opacity-80" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#05070b] to-transparent" />
          <p className="absolute bottom-6 left-6 right-6 font-display text-2xl italic">Roots seeking water.</p>
        </div>
      </section>

      <section className="px-6 py-10">
        <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-3">
          {[
            { q: "Can this asset be an opportunity?", a: "Discovery across pre-launch, newly launched, and hidden names." },
            { q: "Is it a trap?", a: "Honeypot, mint, freeze, tax, LP, deployer history — the risk gate can REJECT a high score." },
            { q: "What do we still not know?", a: "UNKNOWN. INSUFFICIENT EVIDENCE. CONFLICTED. The anti-illusion rule." },
          ].map((item) => (
            <article key={item.q} className="panel rounded-3xl p-6">
              <h3 className="font-display text-3xl italic text-[#f3d5a0]">{item.q}</h3>
              <p className="mt-4 text-sm text-[#efe6d6]/70">{item.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-24">
        <p className="kicker">Ten specialist teams</p>
        <h2 className="font-display mt-3 text-5xl italic">The council does not vote as one.</h2>
        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {TEAMS.map((t) => (
            <article key={t.no} className="panel rounded-2xl p-4">
              <div className="font-mono text-xs text-[#6ee7f9]">{String(t.no).padStart(2, "0")} · {t.code}</div>
              <h3 className="mt-2 font-display text-xl italic">{t.name}</h3>
              <p className="mt-2 text-xs text-[#efe6d6]/60">{t.focus}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="relative overflow-hidden py-24">
        <img src="/images/council.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="absolute inset-0 bg-[#05070b]/70" />
        <div className="relative mx-auto grid max-w-6xl gap-8 px-6 md:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="kicker">Scoring</p>
            <h2 className="font-display mt-3 text-5xl italic">Eight numbers, never one lie.</h2>
            <p className="mt-4 max-w-lg text-[#efe6d6]/70">
              Opportunity, security, liquidity, social, whale, narrative, evidence, confidence. A loud tape
              cannot outrun a dead sell path.
            </p>
          </div>
          <div className="panel rounded-3xl p-6 font-mono text-sm">
            {[
              ["Opportunity", "0–100"],
              ["Security", "0–100 · can veto"],
              ["Confidence", "independent"],
              ["Decision", "WATCH / INVESTIGATE / PAPER / SKIP / REJECT"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between border-b border-[rgba(201,163,106,0.12)] py-3">
                <span className="text-[#f3d5a0]">{k}</span>
                <span className="text-[#efe6d6]/60">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-8 px-6 py-24 md:grid-cols-2">
        <div className="relative overflow-hidden rounded-3xl">
          <img src="/images/fruit.jpg" alt="Golden fruit" className="h-[420px] w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#05070b] via-transparent to-transparent" />
          <div className="absolute bottom-6 left-6">
            <p className="kicker">Golden fruit</p>
            <h3 className="font-display text-4xl italic">Exceptional, not numerous.</h3>
          </div>
        </div>
        <div className="relative overflow-hidden rounded-3xl">
          <img src="/images/tree.jpg" alt="Roots" className="h-[420px] w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#05070b] via-transparent to-transparent" />
          <div className="absolute bottom-6 left-6">
            <p className="kicker">Paper loop</p>
            <h3 className="font-display text-4xl italic">Trade the hypothesis. Keep the lesson.</h3>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-28">
        <div className="panel overflow-hidden rounded-[2rem]">
          <div className="grid md:grid-cols-2">
            <img src={MEDIA.palace} alt="" className="h-full min-h-[320px] w-full object-cover opacity-70" />
            <div className="p-8 md:p-12">
              <p className="kicker">Enter</p>
              <h2 className="font-display mt-3 text-5xl italic leading-tight">The chamber is single-user, local-first, $0 to begin.</h2>
              <p className="mt-4 text-[#efe6d6]/70">
                GitHub is the source of truth. Telegram is the relay. The dashboard is the mind. Beauty never
                outranks auditability.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <SoundButton href="/dashboard" tone="gold" sound="enter" className="px-8 py-4">
                  Open command
                </SoundButton>
                <SoundButton href="/github" tone="ghost" className="px-8 py-4">
                  GitHub hub
                </SoundButton>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
