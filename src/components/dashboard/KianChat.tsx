"use client";
import { useState } from "react";
import { ChevronDown, MessageCircle, Send, Sparkles } from "lucide-react";
import { getDemoAnswer } from "../../lib/api/dashboard";
import type { Localized } from "../../lib/api/types";
import type { Language } from "../../lib/navigation";
import { DataCard } from "../cards/DataCard";
type Message = {
  id: number;
  role: "user" | "assistant";
  content: string | Localized;
  source?: string;
};
export function KianChat({ language }: { language: Language }) {
  const fa = language === "fa";
  const [collapsed, setCollapsed] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  function send(text: string) {
    if (!text.trim()) return;
    const answer = getDemoAnswer(text);
    setMessages((old) => [
      ...old.slice(-14),
      {
        id: old.length ? old[old.length - 1].id + 1 : 1,
        role: "user",
        content: text.trim(),
      },
      {
        id: old.length ? old[old.length - 1].id + 2 : 2,
        role: "assistant",
        content: answer.answer,
        source: answer.source,
      },
    ]);
    setInput("");
  }
  return (
    <DataCard
      title={fa ? "گفت‌وگو با کیان" : "Kian assistant"}
      icon={MessageCircle}
      language={language}
      className="dc-kian"
      action={
        <button
          className="ah-icon-button"
          aria-label={fa ? "باز و بسته کردن گفت‌وگو" : "Toggle chat"}
          aria-expanded={!collapsed}
          onClick={() => setCollapsed(!collapsed)}
        >
          <ChevronDown size={14} className={collapsed ? "is-collapsed" : ""} />
        </button>
      }
    >
      {!collapsed && (
        <>
          <div className="dc-kian-identity">
            <span className="dc-kian-avatar">
              <Sparkles size={22} />
            </span>
            <div>
              <strong>
                {fa ? "کیان، همراه پژوهش شما" : "Kian, your research companion"}
              </strong>
              <small>
                {fa
                  ? "پاسخ‌های از پیش نوشته‌شده · بدون مدل متصل"
                  : "Scripted responses · No AI connected"}
              </small>
            </div>
          </div>
          <div
            className="dc-chat-messages"
            aria-live="polite"
            role="log"
            aria-label={fa ? "پیام‌های گفت‌وگو" : "Chat messages"}
          >
            <div className="dc-chat-message dc-chat-assistant">
              {fa
                ? "سلام مهرداد. برای بررسی داده‌های نمونه کنارتان هستم. کدام بخش را مرور کنیم؟"
                : "Hello Mehrdad. I can help you explore the demo fixtures. Where would you like to start?"}
            </div>
            {messages.map((message) => (
              <div
                className={`dc-chat-message dc-chat-${message.role}`}
                key={message.id}
              >
                <span dir="auto">
                  {typeof message.content === "string"
                    ? message.content
                    : message.content[language]}
                </span>
                {message.source && <small>{message.source}</small>}
              </div>
            ))}
          </div>
          <div className="dc-chat-prompts">
            {(fa
              ? ["وضعیت بازار", "بررسی ریسک", "عامل‌ها"]
              : ["Markets", "Risk review", "Agents"]
            ).map((prompt) => (
              <button key={prompt} onClick={() => send(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
          <form
            className="dc-chat-form"
            onSubmit={(event) => {
              event.preventDefault();
              send(input);
            }}
          >
            <input
              aria-label={fa ? "پیام به کیان" : "Message Kian"}
              placeholder={fa ? "از کیان بپرسید..." : "Ask Kian…"}
              value={input}
              maxLength={500}
              onChange={(event) => setInput(event.target.value)}
            />
            <button
              type="submit"
              disabled={!input.trim()}
              aria-label={fa ? "ارسال پیام" : "Send message"}
            >
              <Send size={14} />
            </button>
          </form>
        </>
      )}
    </DataCard>
  );
}
