"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import { Bot, Send, X, ShieldAlert, Sparkles, User } from "lucide-react";

interface AIChatTelegramDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AIChatTelegramDrawer({ isOpen, onClose }: AIChatTelegramDrawerProps) {
  const [messages, setMessages] = useState<
    { sender: "user" | "bot"; text: string; time: string }[]
  >([
    {
      sender: "bot",
      text: "سلام! من ربات و دستیار هوشمند AHOS در تلگرام هستم. پاسخگو به پرسش‌های شما بر اساس اصل Evidence Before Decision. چگونه می‌توانم کمک کنم؟",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    soundFx.playClick();
    const userMsg = input.trim();
    const nowStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    setMessages((prev) => [...prev, { sender: "user", text: userMsg, time: nowStr }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      if (data.success) {
        soundFx.playAgentBlip(100);
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: data.reply,
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "بهترین فرصت امروز چیه؟",
    "وضعیت معاملات فرضی چیه؟",
    "سیستم امنیت و ضد سکم چگونه کار می‌کند؟",
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0a0e17] border-l border-[rgba(0,243,255,0.3)] shadow-[0_0_80px_rgba(0,243,255,0.2)] flex flex-col animate-slideLeft">
      {/* Header */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.1)] flex items-center justify-between bg-[rgba(0,243,255,0.05)]">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00f3ff] to-[#00ff88] p-[1px]">
            <div className="w-full h-full bg-[#0a0e17] rounded-[11px] flex items-center justify-center text-[#00f3ff]">
              <Bot className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h3 className="font-mono font-bold text-sm text-white">AHOS Telegram AI Bot</h3>
            <span className="text-[10px] font-mono text-[#00ff88] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00ff88] animate-ping" />
              Online & Connected to n8n Agent
            </span>
          </div>
        </div>

        <button
          onClick={() => {
            soundFx.playClick();
            onClose();
          }}
          className="p-2 rounded-lg hover:bg-[rgba(255,0,85,0.2)] text-gray-400 hover:text-[#ff0055] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 font-mono text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[85%] p-3 rounded-2xl leading-relaxed whitespace-pre-wrap ${
                m.sender === "user"
                  ? "bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-medium rounded-br-none shadow-[0_0_15px_rgba(0,243,255,0.2)]"
                  : "bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] text-gray-200 rounded-bl-none"
              }`}
            >
              {m.text}
            </div>
            <span className="text-[9px] text-gray-500 mt-1 px-1">{m.time}</span>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs font-mono text-[#00f3ff] animate-pulse">
            <Sparkles className="w-4 h-4 animate-spin" />
            شورای ۱۰ تایی AI در حال بررسی شواهد...
          </div>
        )}
      </div>

      {/* Quick Prompts */}
      <div className="p-2 px-4 border-t border-[rgba(255,255,255,0.05)] flex flex-wrap gap-1.5 bg-[rgba(0,0,0,0.2)]">
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => {
              soundFx.playClick();
              setInput(qp);
            }}
            className="px-2.5 py-1 rounded-full bg-[rgba(0,243,255,0.1)] border border-[rgba(0,243,255,0.2)] text-[10px] font-mono text-[#00f3ff] hover:bg-[rgba(0,243,255,0.2)] transition-colors"
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-[rgba(255,255,255,0.1)] flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="پیام یا آدرس توکن را وارد کنید..."
          className="flex-1 px-3 py-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] font-mono text-xs text-white focus:outline-none focus:border-[#00f3ff]"
        />
        <button
          type="submit"
          disabled={loading}
          className="p-2.5 rounded-xl bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-bold hover:opacity-90 transition-opacity"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
