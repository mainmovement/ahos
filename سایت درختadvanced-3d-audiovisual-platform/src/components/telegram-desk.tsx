"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { SoundButton } from "@/components/sound-button";
import type { TelegramMessage } from "@/db/schema";

export function TelegramDesk({ initial }: { initial: TelegramMessage[] }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!text.trim() || busy) return;
    setBusy(true);
    await fetch("/api/telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });
    setText("");
    setBusy(false);
    router.refresh();
  }

  return (
    <div className="panel mx-auto flex min-h-[70vh] max-w-lg flex-col rounded-[2rem] p-4">
      <div className="kicker px-2">AHOS relay</div>
      <div className="mt-3 flex-1 space-y-2 overflow-auto">
        {initial.map((m) => (
          <div
            key={m.id}
            className={`max-w-[90%] rounded-2xl px-3 py-2 text-sm ${m.direction === "in" ? "bg-[#1d4ed8]/40" : "ml-auto bg-[#0f3d2e]"}`}
          >
            {m.content}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder="بهترین فرصت امروز چیه؟" />
        <SoundButton tone="gold" disabled={busy} onClick={() => void send()}>
          Send
        </SoundButton>
      </div>
    </div>
  );
}
