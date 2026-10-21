"use client";

import { useCallback, useEffect, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { ensureDashboardSession, hasDashboardSession, webApiFetch } from "@/web_api_client";

type Msg = { id: number; role: "user" | "assistant"; text: string; meta?: string };

function authStatus(): ChipStatus {
  if (typeof window === "undefined") return "UNKNOWN";
  return hasDashboardSession() ? "PARTIAL" : "UNAVAILABLE";
}

export function KianArenaChat({ fa }: { fa: boolean }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [gate, setGate] = useState<ChipStatus>("UNKNOWN");
  const [bootHint, setBootHint] = useState(false);

  useEffect(() => {
    void ensureDashboardSession().then((ok) => {
      setGate(ok ? "PARTIAL" : "UNAVAILABLE");
      setBootHint(!ok);
    });
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    const userId = messages.length ? messages[messages.length - 1].id + 1 : 1;
    setMessages((m) => [...m.slice(-14), { id: userId, role: "user", text }]);
    setInput("");
    try {
      const res = await webApiFetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          channel: "Kian chat",
          history: messages.slice(-10).map((h) => ({ role: h.role, content: h.text })),
        }),
      });
      const json = (await res.json().catch(() => ({}))) as {
        reply?: string;
        answer?: string;
        intent?: string;
        evidence?: { error?: string };
      };
      if (res.status === 401) {
        setBootHint(true);
        setGate("UNAVAILABLE");
        setMessages((m) => [
          ...m,
          {
            id: userId + 1,
            role: "assistant",
            text: fa
              ? "برای گفت‌وگوی واقعی، آهوس را از میانبر دسکتاپ باز کنید (نشست یک‌بارمصرف)."
              : "Open AHOS from the desktop shortcut for a real session (one-time boot token).",
            meta: "AUTH",
          },
        ]);
        return;
      }
      const answer = String(json.reply ?? json.answer ?? "").trim();
      setMessages((m) => [
        ...m,
        {
          id: userId + 1,
          role: "assistant",
          text: answer || (fa ? "پاسخی دریافت نشد." : "No reply received."),
          meta: json.intent ?? undefined,
        },
      ]);
      setGate("PARTIAL");
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: userId + 1,
          role: "assistant",
          text: fa ? "خطا در ارتباط با دروازهٔ گفت‌وگو." : "Could not reach the chat gateway.",
          meta: "ERROR",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }, [busy, fa, input, messages]);

  return (
    <div className="mb-page kian-arena" data-page="kian">
      <header className="mb-head">
        <div>
          <h1 className="mb-title">{fa ? "گفت‌وگو با کیان" : "Kian chat"}</h1>
          <p className="mb-sub">
            {fa
              ? "مسیر کانونی /api/chat · PAPER_ONLY · بدون معاملهٔ واقعی"
              : "Canonical /api/chat path · PAPER_ONLY · no live trading"}
          </p>
        </div>
        <div className="mb-chips">
          <TruthChip status="PARTIAL" size="sm" labelFa={fa ? "فقط کاغذی" : "Paper only"} hideCode />
          <TruthChip status={gate} size="sm" labelFa={fa ? "نشست" : "Session"} />
          <TruthChip status={authStatus()} size="sm" labelFa="CSRF" hideCode />
        </div>
      </header>
      {bootHint ? (
        <p className="mb-note" role="status">
          {fa
            ? "نشست داشبورد فعال نیست — از AHOS.vbs روی دسکتاپ باز کنید؛ URL با #boot= یک‌بارمصرف است."
            : "No dashboard session — launch via AHOS.vbs; the URL carries a one-time #boot= token."}
        </p>
      ) : null}
      <div className="dc-kian-identity mb-sec">
        <span className="dc-kian-avatar"><Sparkles size={22} /></span>
        <div>
          <strong>{fa ? "کیان · رابط پژوهش" : "Kian · research interface"}</strong>
          <small>{fa ? "پاسخ از موتور قطعی + پل ۸۷۸۷ (در صورت تنظیم)" : "Deterministic engine + bridge :8787 when configured"}</small>
        </div>
      </div>
      <div className="dc-chat-messages mb-sec" role="log" aria-live="polite">
        {messages.length === 0 ? (
          <p className="mb-empty">
            {fa ? "سؤال خود را بنویسید — مثلاً وضعیت طلا یا PAPER_ONLY." : "Ask about gold status or PAPER_ONLY."}
          </p>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`dc-chat-message dc-chat-${m.role}`}>
              <p>{m.text}</p>
              {m.meta ? <small className="mb-hl__detail" dir="ltr">{m.meta}</small> : null}
            </div>
          ))
        )}
      </div>
      <form
        className="dc-kian-form"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          className="dc-kian-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
          placeholder={fa ? "پیام به کیان…" : "Message Kian…"}
          aria-label={fa ? "پیام" : "Message"}
        />
        <button type="submit" className="ah-btn ah-btn--gold" disabled={busy || !input.trim()} aria-busy={busy}>
          <Send size={16} />
          <span>{fa ? "ارسال" : "Send"}</span>
        </button>
      </form>
    </div>
  );
}
