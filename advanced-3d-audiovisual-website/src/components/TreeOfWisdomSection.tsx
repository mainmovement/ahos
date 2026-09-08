"use client";

import React, { useState, useEffect } from "react";
import { soundFx } from "@/utils/audio";
import {
  Terminal,
  GitBranch,
  Layers,
  Sparkles,
  Droplets,
  Shield,
  Activity,
  Award,
} from "lucide-react";

interface TreeOfWisdomSectionProps {
  onSelectLayer: (layer: string) => void;
}

export function TreeOfWisdomSection({ onSelectLayer }: TreeOfWisdomSectionProps) {
  const [learningLogs, setLearningLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<string>("ALL");

  useEffect(() => {
    fetch("/api/learning")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setLearningLogs(data.learningLogs);
        }
      })
      .catch(console.error);
  }, []);

  const treeLayers = [
    {
      id: "ROOTS",
      title: "1. Roots (ریشه‌ها)",
      sub: "Data Sources & Sensors",
      desc: "DEX Scrapers, RPC Nodes, Smart Money Wallets, Telegram Crawlers, GitHub Repos.",
      color: "border-[#ffaa00] text-[#ffaa00] bg-[rgba(255,170,0,0.08)]",
    },
    {
      id: "TRUNK",
      title: "2. Trunk (تنه)",
      sub: "Core Architecture",
      desc: "Drizzle ORM, Next.js Engine, Provider Abstraction, Risk Gate, n8n Orchestrator.",
      color: "border-[#00f3ff] text-[#00f3ff] bg-[rgba(0,243,255,0.08)]",
    },
    {
      id: "BRANCHES",
      title: "3. Branches (شاخه‌ها)",
      sub: "Specialized AI Teams",
      desc: "10-Team Conclave: Math, Market, On-Chain, Cybersecurity, OSINT, News, Social, Engineering, RAG, Red Team.",
      color: "border-[#00ff88] text-[#00ff88] bg-[rgba(0,255,136,0.08)]",
    },
    {
      id: "LEAVES",
      title: "4. Leaves & Fruit (میوه‌ها)",
      sub: "Discovered Opportunities",
      desc: "Validated Token Dossiers, Golden Opportunities, High Conviction Signals.",
      color: "border-[#b026ff] text-[#d884ff] bg-[rgba(176,38,255,0.08)]",
    },
    {
      id: "OCEAN",
      title: "5. Groundwater Ocean (اقیانوس دانش)",
      sub: "Collective Intelligence Memory",
      desc: "Post-Mortem Win/Loss Learning Loops, Automated Failure Pattern Neutralizers.",
      color: "border-[#0077ff] text-[#3399ff] bg-[rgba(0,119,255,0.08)]",
    },
  ];

  const filteredLogs =
    activeTab === "ALL" ? learningLogs : learningLogs.filter((l) => l.treeLayer === activeTab);

  return (
    <div className="p-6 rounded-2xl bg-[#0a0e17] border border-[rgba(0,243,255,0.2)] shadow-[0_0_50px_rgba(0,243,255,0.08)]">
      {/* Banner */}
      <div className="border-b border-[rgba(255,255,255,0.08)] pb-5 mb-6">
        <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded bg-[rgba(255,170,0,0.15)] text-[#ffaa00] border border-[rgba(255,170,0,0.3)] mb-1 inline-block">
          SELF-EVOLUTION PHILOSOPHY
        </span>
        <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
          <Terminal className="w-6 h-6 text-[#ffaa00]" />
          Tree of Wisdom & Ocean of Intelligence
        </h2>
        <p className="text-xs font-mono text-gray-400 mt-1">
          Sections 25-27 Master Spec: Roots seek knowledge through obstacles until reaching the deep groundwater ocean of collective intelligence.
        </p>
      </div>

      {/* Layer Hierarchy Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-8">
        {treeLayers.map((layer) => (
          <div
            key={layer.id}
            onClick={() => {
              soundFx.playClick();
              setActiveTab(layer.id);
              onSelectLayer(layer.id);
            }}
            className={`p-3.5 rounded-xl border cursor-pointer transition-all hover:scale-[1.02] ${layer.color} ${
              activeTab === layer.id ? "ring-2 ring-white shadow-lg" : "opacity-80 hover:opacity-100"
            }`}
          >
            <h4 className="text-xs font-mono font-bold mb-1">{layer.title}</h4>
            <span className="text-[10px] font-mono font-bold block mb-2 opacity-90">{layer.sub}</span>
            <p className="text-[10px] font-mono text-gray-300 leading-snug">{layer.desc}</p>
          </div>
        ))}
      </div>

      {/* Post-Mortem & Knowledge Logs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-mono font-bold text-gray-300 uppercase tracking-widest flex items-center gap-2">
            <Droplets className="w-4 h-4 text-[#00f3ff]" />
            Groundwater Knowledge Ingestion Telemetry ({filteredLogs.length} Records)
          </h3>

          <div className="flex gap-1 font-mono text-[10px]">
            {["ALL", "ROOTS", "BRANCHES", "OCEAN"].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  soundFx.playClick();
                  setActiveTab(tab);
                  onSelectLayer(tab === "ALL" ? "" : tab);
                }}
                className={`px-2.5 py-1 rounded-lg border transition-all ${
                  activeTab === tab
                    ? "bg-[#00f3ff] text-black font-bold border-[#00f3ff]"
                    : "bg-[rgba(255,255,255,0.05)] text-gray-400 border-[rgba(255,255,255,0.08)] hover:text-white"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          {filteredLogs.map((log) => (
            <div
              key={log.id}
              className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:border-[rgba(0,243,255,0.3)] transition-colors font-mono"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#00ff88]" />
                  {log.title}
                </span>
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[rgba(0,243,255,0.15)] text-[#00f3ff] border border-[rgba(0,243,255,0.3)] uppercase">
                  {log.treeLayer}
                </span>
              </div>
              <p className="text-xs text-gray-300 mb-2 leading-relaxed">{log.description}</p>
              <div className="p-2 rounded bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.15)] text-[11px] text-[#00ff88]">
                <strong>IMPACT ON SYSTEM:</strong> {log.impact}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
