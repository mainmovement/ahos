"use client";

import { useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAudio } from "@/components/system/AudioProvider";
import { Bell, ShieldAlert, Cpu, Wallet, Save } from "lucide-react";

type Notifications = { minOpportunityScore: number; minConfidence: number; criticalSecurityOnly: boolean };
type RiskGate = { maxAcceptableRisk: string; autoRejectCritical: boolean };
type AiProviders = { primary: string; fallbacks: string[] };
type Budget = { monthlyUsd: number; infrastructure: string };

export function SettingsForm({
  notifications: initialNotifications,
  riskGate: initialRiskGate,
  aiProviders,
  budget,
}: {
  notifications: Notifications;
  riskGate: RiskGate;
  aiProviders: AiProviders;
  budget: Budget;
}) {
  const [notifications, setNotifications] = useState(initialNotifications);
  const [riskGate, setRiskGate] = useState(initialRiskGate);
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const { play } = useAudio();

  async function save(key: string, value: Record<string, unknown>) {
    await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, value }),
    });
    setSavedKey(key);
    play.success();
    setTimeout(() => setSavedKey(null), 2000);
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader title="Notification Thresholds" icon={<Bell size={16} />} subtitle="Only surface signals worth your attention" />
        <div className="space-y-4">
          <SliderField
            label="Minimum Opportunity Score"
            value={notifications.minOpportunityScore}
            onChange={(v) => setNotifications((p) => ({ ...p, minOpportunityScore: v }))}
          />
          <SliderField
            label="Minimum Confidence"
            value={notifications.minConfidence}
            onChange={(v) => setNotifications((p) => ({ ...p, minConfidence: v }))}
          />
          <label className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 text-sm text-slate-200">
            Critical security alerts only
            <input
              type="checkbox"
              checked={notifications.criticalSecurityOnly}
              onChange={(e) => setNotifications((p) => ({ ...p, criticalSecurityOnly: e.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>
        </div>
        <SaveRow saved={savedKey === "notifications"} onSave={() => save("notifications", notifications)} />
      </Card>

      <Card>
        <CardHeader title="Risk Gate" icon={<ShieldAlert size={16} />} subtitle="High opportunity never overrides critical risk" />
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs text-slate-400">Maximum Acceptable Risk Level</label>
            <select
              data-cursor-interactive
              value={riskGate.maxAcceptableRisk}
              onChange={(e) => setRiskGate((p) => ({ ...p, maxAcceptableRisk: e.target.value }))}
              className="w-full rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-cyan-300/50"
            >
              <option value="low">Low only</option>
              <option value="medium">Low + Medium</option>
              <option value="high">Up to High</option>
            </select>
          </div>
          <label className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 text-sm text-slate-200">
            Auto-reject critical risk (recommended)
            <input
              type="checkbox"
              checked={riskGate.autoRejectCritical}
              onChange={(e) => setRiskGate((p) => ({ ...p, autoRejectCritical: e.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>
        </div>
        <SaveRow saved={savedKey === "risk_gate"} onSave={() => save("risk_gate", riskGate)} />
      </Card>

      <Card>
        <CardHeader title="AI Providers" icon={<Cpu size={16} />} subtitle="Provider abstraction — no single vendor owns the architecture" />
        <div className="space-y-2.5">
          <div className="flex items-center justify-between rounded-xl border border-cyan-300/20 bg-cyan-300/5 px-4 py-3">
            <span className="text-sm text-slate-100">Primary</span>
            <Badge tone="cyan">{aiProviders.primary}</Badge>
          </div>
          {aiProviders.fallbacks.map((f) => (
            <div key={f} className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
              <span className="text-sm text-slate-300">{f}</span>
              <Badge tone="neutral">fallback · needs API key</Badge>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-slate-500">
          Set provider API keys as environment secrets to activate them — the system will automatically prefer configured providers over the local reasoning engine.
        </p>
      </Card>

      <Card>
        <CardHeader title="Budget" icon={<Wallet size={16} />} subtitle="Zero-budget principle (§32)" />
        <div className="flex items-center justify-between rounded-xl border border-emerald-400/20 bg-emerald-400/5 px-4 py-3">
          <span className="text-sm text-slate-100">Monthly infrastructure budget</span>
          <span className="font-display text-lg font-bold text-emerald-300">${budget.monthlyUsd}</span>
        </div>
        <p className="mt-3 text-xs text-slate-500">{budget.infrastructure}</p>
      </Card>
    </div>
  );
}

function SliderField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-cyan-300">{value}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-cyan-400"
      />
    </div>
  );
}

function SaveRow({ saved, onSave }: { saved: boolean; onSave: () => void }) {
  return (
    <div className="mt-5 flex items-center gap-3">
      <Button size="sm" variant="secondary" onClick={onSave} icon={<Save size={14} />}>
        Save
      </Button>
      {saved && <span className="text-xs text-emerald-300">Saved</span>}
    </div>
  );
}
