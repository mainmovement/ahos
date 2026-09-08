"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import {
  Search,
  ShieldCheck,
  AlertOctagon,
  Award,
  Zap,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  SlidersHorizontal,
} from "lucide-react";

interface TokenDiscoveryGridProps {
  tokens: any[];
  onSelectToken: (token: any) => void;
  onOpenScanner: () => void;
}

export function TokenDiscoveryGrid({
  tokens,
  onSelectToken,
  onOpenScanner,
}: TokenDiscoveryGridProps) {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedChain, setSelectedChain] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const categories = [
    { id: "all", label: "All Candidates" },
    { id: "newly-launched", label: "Group B — Newly Launched" },
    { id: "hidden-opportunity", label: "Group C — Hidden Opportunities" },
    { id: "pre-launch", label: "Group A — Pre-Launch" },
  ];

  const chains = ["all", "Solana", "Base", "Ethereum", "BNB"];

  const filteredTokens = tokens.filter((t) => {
    if (selectedCategory !== "all" && t.category !== selectedCategory) return false;
    if (selectedChain !== "all" && t.chain.toLowerCase() !== selectedChain.toLowerCase()) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        t.name.toLowerCase().includes(q) ||
        t.symbol.toLowerCase().includes(q) ||
        t.contractAddress.toLowerCase().includes(q) ||
        t.narrative.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Category Tabs & Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[rgba(255,255,255,0.02)] p-4 rounded-2xl border border-[rgba(255,255,255,0.06)]">
        {/* Category Buttons */}
        <div className="flex flex-wrap gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                soundFx.playClick();
                setSelectedCategory(cat.id);
              }}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs transition-all ${
                selectedCategory === cat.id
                  ? "bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-bold shadow-[0_0_15px_rgba(0,243,255,0.3)]"
                  : "bg-[rgba(255,255,255,0.04)] text-gray-400 hover:text-white"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Chain Filters & Search Input */}
        <div className="flex items-center gap-2">
          <select
            value={selectedChain}
            onChange={(e) => {
              soundFx.playClick();
              setSelectedChain(e.target.value);
            }}
            className="px-3 py-1.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(0,243,255,0.2)] font-mono text-xs text-white"
          >
            {chains.map((c) => (
              <option key={c} value={c} className="bg-[#0a0e17]">
                {c === "all" ? "All Chains" : c}
              </option>
            ))}
          </select>

          <div className="relative flex-1 md:w-56">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Search token or contract..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] font-mono text-xs text-white focus:outline-none focus:border-[#00f3ff]"
            />
          </div>
        </div>
      </div>

      {/* Grid of Tokens */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTokens.map((token) => {
          const isRejected = token.status === "rejected" || token.securityScore < 40;
          const isPriceUp = parseFloat(token.priceChange24h || "0") >= 0;

          return (
            <div
              key={token.id}
              onClick={() => {
                soundFx.playClick();
                onSelectToken(token);
              }}
              className={`p-5 rounded-2xl border cursor-pointer transition-all duration-300 hover:scale-[1.01] hover:shadow-2xl relative overflow-hidden group ${
                isRejected
                  ? "bg-[rgba(255,0,85,0.03)] border-[rgba(255,0,85,0.25)] hover:border-[#ff0055]"
                  : "bg-[#0a0e17] border-[rgba(0,243,255,0.2)] hover:border-[#00f3ff] hover:shadow-[0_0_30px_rgba(0,243,255,0.15)]"
              }`}
            >
              {/* Top Row: Symbol & Chain */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00f3ff] to-[#b026ff] p-[1.5px] group-hover:scale-110 transition-transform">
                    <div className="w-full h-full bg-[#0a0e17] rounded-[10px] flex items-center justify-center font-mono font-bold text-sm text-[#00f3ff]">
                      {token.symbol.substring(0, 2)}
                    </div>
                  </div>
                  <div>
                    <h3 className="font-mono font-bold text-white text-base flex items-center gap-1.5">
                      {token.name}
                    </h3>
                    <span className="text-xs font-mono text-[#00f3ff] font-semibold">${token.symbol}</span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1">
                  <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-[rgba(0,243,255,0.1)] text-[#00f3ff] border border-[rgba(0,243,255,0.3)]">
                    {token.chain}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[9px] font-mono font-bold rounded ${
                      isRejected
                        ? "bg-[rgba(255,0,85,0.2)] text-[#ff0055]"
                        : "bg-[rgba(0,255,136,0.15)] text-[#00ff88]"
                    }`}
                  >
                    {isRejected ? "REJECTED" : token.category.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Main Gauges: Opportunity & Security */}
              <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)] mb-3">
                <div>
                  <span className="text-[9px] font-mono text-gray-400 block">OPPORTUNITY</span>
                  <span className="text-xl font-mono font-black text-[#00f3ff]">{token.opportunityScore}/100</span>
                </div>

                <div>
                  <span className="text-[9px] font-mono text-gray-400 block">SECURITY RISK</span>
                  <span
                    className={`text-xl font-mono font-black ${
                      token.securityScore < 50 ? "text-[#ff0055]" : "text-[#00ff88]"
                    }`}
                  >
                    {token.securityScore}/100
                  </span>
                </div>
              </div>

              {/* Narrative & Price */}
              <div className="flex items-center justify-between text-xs font-mono mb-3">
                <span className="text-gray-400 truncate max-w-[150px]">
                  Narrative: <span className="text-white font-bold">{token.narrative}</span>
                </span>
                <div className="text-right">
                  <span className="text-white font-bold block">${token.price}</span>
                  <span
                    className={`text-[10px] font-bold flex items-center justify-end gap-0.5 ${
                      isPriceUp ? "text-[#00ff88]" : "text-[#ff0055]"
                    }`}
                  >
                    {isPriceUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                    {token.priceChange24h}%
                  </span>
                </div>
              </div>

              {/* Evidence Snippet */}
              <p className="text-[11px] font-mono text-gray-400 line-clamp-2 mb-3 bg-[rgba(0,0,0,0.3)] p-2 rounded border border-[rgba(255,255,255,0.04)]">
                {token.evidenceSummary}
              </p>

              {/* Action Button */}
              <div className="pt-2 border-t border-[rgba(255,255,255,0.06)] flex justify-between items-center text-xs font-mono text-[#00f3ff] group-hover:text-white transition-colors">
                <span>View Full 360° Dossier</span>
                <span className="text-base font-bold">→</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
