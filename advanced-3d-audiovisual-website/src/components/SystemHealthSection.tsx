"use client";

import React, { useState, useEffect } from "react";
import { soundFx } from "@/utils/audio";
import { ShieldCheck, Activity, Cpu, Server, Wifi, RefreshCw } from "lucide-react";

export function SystemHealthSection() {
  const [systemData, setSystemData] = useState<any>(null);

  const fetchStatus = () => {
    fetch("/api/system")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSystemData(data);
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (!systemData) return null;

  return (
    <div className="p-6 rounded-2xl bg-[#0a0e17] border border-[rgba(0,243,255,0.2)] shadow-[0_0_50px_rgba(0,243,255,0.08)]">
      {/* Header */}
      <div className="border-b border-[rgba(255,255,255,0.08)] pb-5 mb-6 flex items-center justify-between">
        <div>
          <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded bg-[rgba(0,243,255,0.15)] text-[#00f3ff] border border-[rgba(0,243,255,0.3)] mb-1 inline-block">
            SYSTEM TELEMETRY
          </span>
          <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-[#00f3ff]" />
            System Health & Provider Fallbacks
          </h2>
          <p className="text-xs font-mono text-gray-400 mt-1">
            Section 21, 33 & 34 Master Spec: Provider abstraction with fallback resilience and $0 budget open-source infrastructure.
          </p>
        </div>

        <button
          onClick={() => {
            soundFx.playClick();
            fetchStatus();
          }}
          className="p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(0,243,255,0.3)] text-[#00f3ff] hover:bg-[rgba(0,243,255,0.15)] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* System Stats Top Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">BUDGET ALLOCATION</span>
          <span className="text-sm font-mono font-bold text-[#00f3ff]">
            {systemData.systemStatus.budget}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">SYSTEM UPTIME</span>
          <span className="text-xl font-mono font-bold text-[#00ff88]">
            {systemData.systemStatus.uptime}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(176,38,255,0.05)] border border-[rgba(176,38,255,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">ACTIVE AI CONCLAVE TEAMS</span>
          <span className="text-xl font-mono font-bold text-[#d884ff]">
            {systemData.systemStatus.activeAgents} Teams
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(255,170,0,0.05)] border border-[rgba(255,170,0,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">AUTOMATION WORKFLOWS</span>
          <span className="text-xl font-mono font-bold text-[#ffaa00]">
            {systemData.systemStatus.activeWorkflows} Pipelines
          </span>
        </div>
      </div>

      {/* Provider Abstraction Status Table */}
      <div className="mb-6">
        <h3 className="text-xs font-mono font-bold text-gray-300 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Server className="w-4 h-4 text-[#00f3ff]" />
          Provider Abstraction Matrix (Section 34)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-[rgba(255,255,255,0.1)] text-gray-400 uppercase text-[10px]">
                <th className="py-2.5 px-3">Provider Name</th>
                <th className="py-2.5 px-3">Primary Integration</th>
                <th className="py-2.5 px-3">Fallback Integration</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(255,255,255,0.05)]">
              {systemData.providers.map((p: any, idx: number) => (
                <tr key={idx} className="hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                  <td className="py-2.5 px-3 font-bold text-white">{p.name}</td>
                  <td className="py-2.5 px-3 text-[#00f3ff]">{p.primary}</td>
                  <td className="py-2.5 px-3 text-gray-400">{p.fallback}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[rgba(0,255,136,0.2)] text-[#00ff88]">
                      {p.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-gray-300">{p.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Logs */}
      <div>
        <h3 className="text-xs font-mono font-bold text-gray-300 uppercase tracking-widest mb-3 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-[#d884ff]" />
          Recent System Event Logs
        </h3>

        <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
          {systemData.logs.map((log: any) => (
            <div
              key={log.id}
              className="p-2.5 rounded bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] font-mono text-xs flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[rgba(0,243,255,0.15)] text-[#00f3ff]">
                  [{log.source}]
                </span>
                <span className="text-gray-300">{log.message}</span>
              </div>
              <span className="text-[10px] text-gray-500">
                {new Date(log.createdAt).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
