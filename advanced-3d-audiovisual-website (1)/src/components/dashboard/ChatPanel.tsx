"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Bot, Send, User, Sparkles } from "lucide-react";
import { useAudio } from "@/components/system/AudioProvider";

type Message = { id: number | string; role: "user" | "assistant"; content: string; createdAt?: string };

const suggestions = [
  "What's the best opportunity today?",
  "Explain SOLV",
  "Show open trades",
  "Any new alerts?",
];

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { play } = useAudio();

  useEffect(() => {
    fetch("/api/chat")
      .then((r) => r.json())
      .then((data) => {
        if (data.ok) setMessages(data.messages);
      })
      .finally(() => setInitialLoading(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setInput("");
    play.click();
    setMessages((prev) => [...prev, { id: `local-${Date.now()}`, role: "user", content }]);
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
      });
      const data = await res.json();
      if (data.ok) {
        setMessages((prev) => [...prev, data.reply]);
        play.success();
      } else {
        setMessages((prev) => [...prev, { id: `err-${Date.now()}`, role: "assistant", content: "AHOS could not process this message. Please try again." }]);
      }
    } catch {
      setMessages((prev) => [...prev, { id: `err-${Date.now()}`, role: "assistant", content: "Connection error — the reasoning engine is unreachable." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass noise-border flex flex-1 flex-col overflow-hidden rounded-2xl">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-5">
        {initialLoading && <p className="text-sm text-slate-500">Loading conversation history...</p>}
        {!initialLoading && messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-full border border-cyan-300/30 bg-cyan-300/10 text-cyan-300">
              <Bot size={24} />
            </div>
            <p className="max-w-sm text-sm text-slate-400">
              Ask AHOS about today&apos;s top opportunity, a specific token, open paper trades, or recent alerts.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  data-cursor-interactive
                  onClick={() => send(s)}
                  className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 hover:border-cyan-300/50 hover:text-cyan-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-full border ${m.role === "user" ? "border-violet-400/30 bg-violet-400/10 text-violet-300" : "border-cyan-300/30 bg-cyan-300/10 text-cyan-300"}`}>
              {m.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "bg-violet-400/10 text-slate-100" : "bg-white/5 text-slate-200"}`}>
              {m.content}
            </div>
          </motion.div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Sparkles className="animate-pulse-glow text-cyan-300" size={14} /> AHOS is reasoning...
          </div>
        )}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex items-center gap-2 border-t border-white/10 p-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask AHOS anything about the market..."
          className="flex-1 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-300/50"
        />
        <button
          type="submit"
          data-cursor-interactive
          disabled={loading || !input.trim()}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-r from-cyan-300 to-violet-400 text-slate-950 disabled:opacity-40"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
