"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { SoundButton } from "@/components/sound-button";

export function SettingsForm({ initial }: { initial: Record<string, unknown> }) {
  const router = useRouter();
  const [owner, setOwner] = useState(String(initial.owner ?? "AHOS Prime"));
  const [paper, setPaper] = useState(String(initial.paperDefaultUsd ?? 150));
  const [risk, setRisk] = useState(Boolean(initial.riskGate ?? true));
  const [msg, setMsg] = useState("");

  return (
    <form
      className="panel max-w-xl space-y-4 rounded-3xl p-6"
      onSubmit={async (e) => {
        e.preventDefault();
        await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ owner, paperDefaultUsd: Number(paper), riskGate: risk }),
        });
        setMsg("Recorded. No change without a document.");
        router.refresh();
      }}
    >
      <label className="block text-sm">
        Operator
        <input className="input mt-1" value={owner} onChange={(e) => setOwner(e.target.value)} />
      </label>
      <label className="block text-sm">
        Default paper capital (USDT)
        <input className="input mt-1" value={paper} onChange={(e) => setPaper(e.target.value)} />
      </label>
      <label className="flex items-center gap-3 text-sm">
        <input type="checkbox" checked={risk} onChange={(e) => setRisk(e.target.checked)} />
        Security risk gate armed
      </label>
      <SoundButton tone="gold" type="submit">Save control surface</SoundButton>
      {msg && <p className="text-sm text-[#4ade80]">{msg}</p>}
    </form>
  );
}
