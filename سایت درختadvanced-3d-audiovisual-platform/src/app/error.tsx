"use client";

import { SoundButton } from "@/components/sound-button";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="grid min-h-screen place-items-center bg-[#05070b] px-6">
      <div className="panel max-w-lg rounded-3xl p-8 text-center">
        <p className="kicker">Fault</p>
        <h1 className="font-display mt-3 text-4xl italic">A root hit stone.</h1>
        <p className="mt-3 text-[#efe6d6]/70">The failure is data. Retry, then file it in GitHub.</p>
        <SoundButton tone="gold" className="mt-6" onClick={reset}>
          Retest
        </SoundButton>
      </div>
    </div>
  );
}
