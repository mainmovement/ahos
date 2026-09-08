"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { SoundButton } from "@/components/sound-button";
import type { ChatMessage } from "@/db/schema";

export function ChatDesk({ initial }: { initial: ChatMessage[] }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function send() {
    if (!text.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text }),
      });
      if (!res.ok) throw new Error("Council unreachable");
      setText("");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel flex min-h-[70vh] flex-col rounded-3xl p-5">
      <div className="flex-1 space-y-3 overflow-auto pr-1">
        {initial.map((m) => (
          <div key={m.id} className={`max-w-[48rem] rounded-2xl px-4 py-3 ${m.role === "user" ? "ml-auto bg-[#c9a36a]/15" : "bg-black/30"}`}>
            <div className="kicker">{m.role}</div>
            <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
          </div>
        ))}
      </div>
      {error && <p className="mt-3 text-sm text-[#fb7185]">{error}</p>}
      <div className="mt-4 flex gap-2">
        <input
          className="input"
          value={text}
          placeholder="Ask why. Ask the gate. Ask what we do not know."
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void send();
          }}
        />
        <SoundButton tone="gold" disabled={busy} onClick={() => void send()}>
          {busy ? "…" : "Ask"}
        </SoundButton>
      </div>
    </div>
  );
}
