"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { NAV } from "@/lib/constants";
import { useAudio } from "@/components/providers";
import { SoundButton } from "@/components/sound-button";

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const audio = useAudio();
  const [open, setOpen] = useState(false);
  const [cmd, setCmd] = useState(false);
  const [q, setQ] = useState("");
  const [clock, setClock] = useState("--:--:--");

  useEffect(() => {
    const tick = () => setClock(new Date().toISOString().slice(11, 19) + "Z");
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmd(true);
      }
      if (e.key === "Escape") setCmd(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const items = useMemo(() => NAV.flatMap((g) => g.items), []);
  const filtered = items.filter((i) => (i.label + i.hint + i.href).toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="min-h-screen bg-[#05070b] text-[#efe6d6]">
      <div className="pointer-events-none fixed inset-0 opacity-40">
        <div className="orb h-72 w-72 bg-[#c9a36a]/25 -left-10 top-10" />
        <div className="orb h-80 w-80 bg-[#6ee7f9]/10 right-0 top-40" style={{ animationDelay: "1.4s" }} />
      </div>

      <header className="sticky top-0 z-40 border-b border-[rgba(201,163,106,0.12)] bg-[#05070b]/75 backdrop-blur-xl">
        <div className="flex items-center gap-3 px-4 py-3 lg:px-6">
          <button className="sound-btn rounded-lg border border-[rgba(201,163,106,0.2)] px-3 py-2 lg:hidden" onClick={() => setOpen((v) => !v)}>
            Menu
          </button>
          <Link href="/" className="flex items-center gap-3" onMouseEnter={() => audio.play("hover")}>
            <img src="/images/mark.png" alt="AHOS" className="h-8 w-8 rounded-full object-cover ring-1 ring-[#c9a36a]/40" />
            <div>
              <div className="font-display text-xl leading-none gold-text">AHOS</div>
              <div className="kicker mt-1">Opportunity intelligence</div>
            </div>
          </Link>
          <div className="ml-auto hidden items-center gap-4 md:flex">
            <button
              className="sound-btn rounded-full border border-[rgba(201,163,106,0.2)] px-4 py-2 text-xs tracking-[0.2em] uppercase text-[#f3d5a0]/80"
              onClick={() => {
                audio.play("click");
                setCmd(true);
              }}
            >
              ⌘K Command
            </button>
            <div className="font-mono text-xs text-[#f3d5a0]/70">{clock}</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full bg-[#4ade80] animate-pulse" />
              ROOTS LIVE
            </div>
            <SoundButton tone="ghost" className="!px-3 !py-2 text-xs" onClick={audio.toggle}>
              {audio.enabled ? "AUDIO ON" : "AUDIO OFF"}
            </SoundButton>
          </div>
        </div>
        <div className="overflow-hidden border-t border-[rgba(201,163,106,0.08)] py-2">
          <div className="ticker flex w-max gap-10 whitespace-nowrap px-6 font-mono text-[11px] text-[#f3d5a0]/55">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="flex gap-10">
                <span>EVIDENCE BEFORE DECISION</span>
                <span>RUMOR ≠ FACT</span>
                <span>HIGH OPPORTUNITY + CRITICAL RISK = REJECT</span>
                <span>SKIP IS A RESULT</span>
                <span>ROOTS SEEKING WATER</span>
                <span>PHASE 1 · TOKEN DISCOVERY</span>
                <span>$0 BUDGET · LOCAL FIRST</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      <div className="relative mx-auto flex max-w-[1600px]">
        <aside
          className={`fixed inset-y-0 left-0 z-30 w-72 overflow-y-auto border-r border-[rgba(201,163,106,0.12)] bg-[#070a10]/95 pt-24 backdrop-blur-xl transition lg:sticky lg:top-[105px] lg:h-[calc(100vh-105px)] lg:translate-x-0 lg:pt-6 ${
            open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          }`}
        >
          <div className="px-4 pb-10">
            {NAV.map((group) => (
              <div key={group.label} className="mb-5">
                <div className="kicker px-2 pb-2">{group.label}</div>
                <div className="space-y-0.5">
                  {group.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`nav-link ${path === item.href ? "active" : ""}`}
                      onMouseEnter={() => audio.play("hover")}
                      onClick={() => {
                        audio.play("click");
                        setOpen(false);
                      }}
                    >
                      <span>{item.label}</span>
                      <span className="font-mono text-[10px] text-[#f3d5a0]/35">{item.hint}</span>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
            <SoundButton href="/" tone="ghost" className="mt-4 w-full">
              Leave chamber
            </SoundButton>
          </div>
        </aside>

        <main className="min-h-[calc(100vh-105px)] flex-1 px-4 py-6 lg:px-8">{children}</main>
      </div>

      {cmd && (
        <div
          className="fixed inset-0 z-50 grid place-items-start bg-black/70 px-4 pt-[15vh] backdrop-blur-sm"
          onClick={() => setCmd(false)}
        >
          <div className="panel w-full max-w-xl rounded-2xl p-4" onClick={(e) => e.stopPropagation()}>
            <input
              autoFocus
              className="input"
              placeholder="Jump to a chamber, token, or doctrine…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <div className="mt-3 max-h-72 overflow-auto">
              {filtered.map((item) => (
                <button
                  key={item.href}
                  className="table-row flex w-full items-center justify-between px-3 py-3 text-left"
                  onMouseEnter={() => audio.play("hover")}
                  onClick={() => {
                    audio.play("enter");
                    setCmd(false);
                    router.push(item.href);
                  }}
                >
                  <span>{item.label}</span>
                  <span className="font-mono text-xs text-[#f3d5a0]/50">{item.href}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
