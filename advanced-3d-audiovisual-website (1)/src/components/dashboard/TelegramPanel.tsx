"use client";

import { useState } from "react";
import { Send, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAudio } from "@/components/system/AudioProvider";

type TelegramConfig = { botConnected: boolean; chatId: string; dailyReportEnabled: boolean; alertTypes: string[] };

export function TelegramPanel({ initial }: { initial: TelegramConfig }) {
  const [config, setConfig] = useState<TelegramConfig>(initial);
  const [chatIdInput, setChatIdInput] = useState(initial.chatId);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<null | { ok: boolean; mode?: string; error?: string }>(null);
  const { play } = useAudio();

  async function save(next: Partial<TelegramConfig>) {
    setSaving(true);
    const merged = { ...config, ...next };
    setConfig(merged);
    try {
      await fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: "telegram", value: merged }),
      });
      play.success();
    } finally {
      setSaving(false);
    }
  }

  async function runTest() {
    setTesting(true);
    play.click();
    try {
      const res = await fetch("/api/telegram/test", { method: "POST" });
      const data = await res.json();
      setTestResult(data);
      data.ok ? play.success() : play.alert();
    } catch {
      setTestResult({ ok: false, error: "Network error" });
      play.alert();
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader
          title="Bot Connection"
          subtitle="Chat with AHOS directly from Telegram"
          icon={<Send size={16} />}
          right={<Badge tone={config.botConnected ? "good" : "neutral"}>{config.botConnected ? "Connected" : "Not connected"}</Badge>}
        />
        <ol className="space-y-2.5 text-sm text-slate-300">
          <li>1. Open Telegram and message <span className="font-mono text-cyan-300">@BotFather</span> to create a bot and get a token.</li>
          <li>2. Set the token as <span className="kbd">TELEGRAM_BOT_TOKEN</span> in your environment secrets.</li>
          <li>3. Message your bot once, then paste your numeric chat ID below.</li>
        </ol>
        <div className="mt-4 flex flex-wrap gap-2">
          <input
            value={chatIdInput}
            onChange={(e) => setChatIdInput(e.target.value)}
            placeholder="Telegram chat ID"
            className="flex-1 min-w-[180px] rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-300/50"
          />
          <Button
            size="md"
            variant="secondary"
            disabled={saving}
            onClick={() => save({ chatId: chatIdInput, botConnected: chatIdInput.length > 0 })}
          >
            Save Chat ID
          </Button>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <Button size="sm" variant="outline" onClick={runTest} disabled={testing} icon={testing ? <Loader2 className="animate-spin" size={14} /> : <Send size={14} />}>
            Send Test Message
          </Button>
          {testResult && (
            <span className={`flex items-center gap-1.5 text-xs ${testResult.ok ? "text-emerald-300" : "text-rose-300"}`}>
              {testResult.ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
              {testResult.ok ? `Sent (${testResult.mode})` : testResult.error}
            </span>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader title="Alert Preferences" subtitle="Choose what gets pushed to Telegram" />
        <label className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
          <span className="text-sm text-slate-200">Daily Intelligence Report</span>
          <ToggleSwitch checked={config.dailyReportEnabled} onChange={(v) => save({ dailyReportEnabled: v })} />
        </label>
        <div className="mt-3 space-y-2">
          {["discovery", "opportunity", "security", "whale", "news", "exit"].map((type) => {
            const checked = config.alertTypes.includes(type);
            return (
              <label key={type} className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 capitalize">
                <span className="text-sm text-slate-200">{type} alerts</span>
                <ToggleSwitch
                  checked={checked}
                  onChange={(v) => {
                    const alertTypes = v ? [...config.alertTypes, type] : config.alertTypes.filter((t) => t !== type);
                    save({ alertTypes });
                  }}
                />
              </label>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  const { play } = useAudio();
  return (
    <button
      type="button"
      data-cursor-interactive
      role="switch"
      aria-checked={checked}
      onClick={() => {
        onChange(!checked);
        checked ? play.toggleOff() : play.toggleOn();
      }}
      className={`relative h-6 w-11 rounded-full transition-colors ${checked ? "bg-cyan-400" : "bg-white/15"}`}
    >
      <span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${checked ? "translate-x-5" : "translate-x-0"}`} />
    </button>
  );
}
