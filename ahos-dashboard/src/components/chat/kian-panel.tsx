"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import Link from "next/link";
import { ArrowUpRight, CornerDownLeft, Eraser, Send, ShieldQuestion } from "lucide-react";
import type { ChatMessage } from "@/lib/api/types";
import { askKian } from "@/lib/api/chat";
import { useI18n } from "@/lib/i18n";
import { useSettings } from "@/lib/settings/provider";
import { useSound } from "@/lib/audio/use-sound";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { StatusChip } from "@/components/ui/status";
import { TimeAgo } from "@/components/ui/primitives";
import { Tip } from "@/components/ui/tooltip";
import { KianOrb } from "./kian-orb";

interface UiMessage extends ChatMessage {
  animate?: boolean;
}

function StreamingText({ text, animate, onDone }: { text: string; animate: boolean; onDone?: () => void }) {
  const [shown, setShown] = useState(animate ? 0 : text.length);
  const done = useRef(!animate);
  useEffect(() => {
    if (!animate) return;
    const step = Math.max(2, Math.round(text.length / 90));
    const id = window.setInterval(() => {
      setShown((s) => {
        const next = Math.min(text.length, s + step);
        if (next >= text.length && !done.current) {
          done.current = true;
          window.clearInterval(id);
          onDone?.();
        }
        return next;
      });
    }, 16);
    return () => window.clearInterval(id);
  }, [animate, text, onDone]);
  const visible = text.slice(0, shown);
  return (
    <span className="whitespace-pre-line">
      {visible}
      {shown < text.length && <span aria-hidden className="ms-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 bg-gold-300 animate-caret" />}
    </span>
  );
}

export function KianPanel({ seed, variant = "rail", className }: { seed: Record<"fa" | "en", ChatMessage[]>; variant?: "rail" | "full"; className?: string }) {
  const { t, locale } = useI18n();
  const { reducedMotion } = useSettings();
  const play = useSound();
  const [conversation, setMessages] = useState<UiMessage[]>([]);
  const messages: UiMessage[] = [...seed[locale], ...conversation];
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: reducedMotion ? "auto" : "smooth" });
  }, [conversation.length, locale, pending, reducedMotion]);

  const send = async (raw: string) => {
    const text = raw.trim();
    if (!text || pending) return;
    play("send");
    const userMsg: UiMessage = { id: `u-${crypto.randomUUID()}`, role: "user", text, at: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setPending(true);
    const started = performance.now();
    const res = await askKian(text, locale);
    const minDelay = reducedMotion ? 0 : 650;
    const wait = Math.max(0, minDelay - (performance.now() - started));
    window.setTimeout(() => {
      setMessages((m) => [...m, { ...res.data, id: `${res.data.id}-${m.length}`, animate: !reducedMotion }]);
      setPending(false);
      play("receive");
    }, wait);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void send(input);
    }
  };

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <section aria-label={t.kian.name} className={cn("flex min-h-0 flex-col", className)}>
      <header className="flex items-center gap-2.5 px-3 pb-2 pt-3">
        <KianOrb size={34} thinking={pending} />
        <div className="min-w-0 flex-1 leading-tight">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-fg-1">
            {t.kian.name}
            <span className="text-3xs font-normal text-fg-4" dir="ltr">
              Kian
            </span>
          </h2>
          <p className="truncate text-3xs text-fg-4">{pending ? t.kian.thinking : t.kian.subtitle}</p>
        </div>
        <StatusChip status="DEMO" />
        <Tip content={t.kian.clear}>
          <Button variant="ghost" size="icon-xs" aria-label={t.kian.clear} onClick={() => setMessages([])}>
            <Eraser aria-hidden />
          </Button>
        </Tip>
        {variant === "rail" && (
          <Tip content={t.kian.openFull}>
            <Button variant="ghost" size="icon-xs" asChild>
              <Link href="/chat" aria-label={t.kian.openFull}>
                <ArrowUpRight aria-hidden className="rtl:-scale-x-100" />
              </Link>
            </Button>
          </Tip>
        )}
      </header>

      <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-2" aria-live="polite" aria-relevant="additions" role="log">
        {messages.map((m) => (
          <MessageBubble key={m.id} m={m} onFollowup={(q) => void send(q)} isLast={m === lastAssistant} />
        ))}
        {pending && (
          <div className="flex items-center gap-2 text-2xs text-fg-4" role="status">
            <span className="flex gap-1" aria-hidden>
              {[0, 1, 2].map((i) => (
                <span key={i} className="size-1.5 rounded-full bg-gold-300 animate-pulse-soft" style={{ animationDelay: `${i * 160}ms` }} />
              ))}
            </span>
            {t.kian.thinking}
          </div>
        )}
      </div>

      <div className="px-3 pb-3 pt-1">
        <div className="glass-strong gold-border flex items-end gap-2 rounded-[var(--radius-lg)] p-1.5 focus-within:shadow-[var(--shadow-glow-sm)]">
          <label htmlFor={`kian-input-${variant}`} className="sr-only">
            {t.kian.placeholder}
          </label>
          <textarea
            id={`kian-input-${variant}`}
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={variant === "full" ? 2 : 1}
            dir="auto"
            placeholder={t.kian.placeholder}
            className="max-h-28 min-h-[30px] flex-1 resize-none bg-transparent px-2 py-1.5 text-xs text-fg-1 placeholder:text-fg-5 focus:outline-none focus-visible:shadow-none"
          />
          <Button variant="gold" size="icon-sm" aria-label={t.kian.send} disabled={!input.trim() || pending} onClick={() => void send(input)}>
            <Send aria-hidden className="rtl:-scale-x-100" />
          </Button>
        </div>
        <p className="mt-1.5 flex items-center gap-1 text-3xs text-fg-5">
          <ShieldQuestion aria-hidden className="size-3" />
          {t.kian.disclaimer}
          <span className="ms-auto hidden items-center gap-0.5 sm:flex" dir="ltr">
            <CornerDownLeft className="size-3" aria-hidden /> Enter
          </span>
        </p>
      </div>
    </section>
  );
}

function MessageBubble({ m, onFollowup, isLast }: { m: UiMessage; onFollowup: (q: string) => void; isLast: boolean }) {
  const { t } = useI18n();
  const [streamed, setStreamed] = useState(!m.animate);
  if (m.role === "user") {
    return (
      <div className="flex flex-col items-end">
        <div dir="auto" className="max-w-[88%] rounded-[var(--radius-lg)] rounded-ee-[4px] border border-gold-400/25 bg-gold-400/[0.09] px-3 py-2 text-xs leading-relaxed text-fg-1">
          {m.text}
        </div>
        <span className="mt-0.5 text-3xs text-fg-5">
          {t.kian.you} · <TimeAgo iso={m.at} />
        </span>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-start animate-rise-in">
      <div className="max-w-[94%] rounded-[var(--radius-lg)] rounded-es-[4px] border border-[var(--line-subtle)] bg-white/[0.03] px-3 py-2 text-xs leading-relaxed text-fg-2">
        <StreamingText text={m.text} animate={!!m.animate} onDone={() => setStreamed(true)} />
        {streamed && (m.evidence?.length || m.uncertainty?.length) ? (
          <div className="mt-2 space-y-1.5 border-t border-[var(--line-subtle)] pt-2">
            {m.evidence && m.evidence.length > 0 && (
              <div>
                <div className="mb-1 text-3xs font-semibold text-fg-4">{t.kian.evidence}</div>
                <ul className="flex flex-wrap gap-1">
                  {m.evidence.map((e, i) => (
                    <li key={i} className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-ink-900/60 py-0.5 pe-0.5 ps-2 text-3xs text-fg-3">
                      <bdi>{e.label}</bdi>
                      <StatusChip status={e.status} showLabel={false} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {m.uncertainty && m.uncertainty.length > 0 && (
              <div>
                <div className="mb-0.5 text-3xs font-semibold text-fg-4">{t.kian.uncertainty}</div>
                <ul className="space-y-0.5 text-3xs text-violet">
                  {m.uncertainty.map((u, i) => (
                    <li key={i}>• {u}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : null}
      </div>
      <span className="mt-0.5 text-3xs text-fg-5">
        {t.kian.name} · <TimeAgo iso={m.at} />
      </span>
      {isLast && streamed && m.followups && m.followups.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1" aria-label={t.kian.followups}>
          {m.followups.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onFollowup(q)}
              className="rounded-full border border-gold-400/25 bg-gold-400/[0.05] px-2 py-0.5 text-3xs text-gold-100 transition-colors hover:border-gold-400/50 hover:bg-gold-400/10"
            >
              {q}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
