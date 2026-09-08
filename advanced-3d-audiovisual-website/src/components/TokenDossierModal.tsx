"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import {
  X,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  Award,
  Lock,
  Layers,
  CheckCircle2,
  XCircle,
  Copy,
  ExternalLink,
  DollarSign,
  Activity,
} from "lucide-react";

interface TokenDossierModalProps {
  token: any;
  councilOpinions: any[];
  onClose: () => void;
  onOpenPaperTrade: (token: any) => void;
}

export function TokenDossierModal({
  token,
  councilOpinions,
  onClose,
  onOpenPaperTrade,
}: TokenDossierModalProps) {
  const [copied, setCopied] = useState(false);

  if (!token) return null;

  const handleCopyContract = () => {
    soundFx.playClick();
    navigator.clipboard.writeText(token.contractAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isRejected = token.status === "rejected" || token.securityScore < 40;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(5,7,12,0.85)] backdrop-blur-md animate-fadeIn overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-[#0a0e17] border border-[rgba(0,243,255,0.3)] rounded-2xl p-6 shadow-[0_0_80px_rgba(0,243,255,0.15)] my-8">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[rgba(255,255,255,0.1)] pb-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00f3ff] to-[#b026ff] p-[1.5px]">
              <div className="w-full h-full bg-[#0a0e17] rounded-[10px] flex items-center justify-center font-mono font-black text-xl text-[#00f3ff]">
                {token.symbol.substring(0, 2)}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold font-mono text-white">{token.name}</h2>
                <span className="text-sm font-mono text-[#00f3ff]">(${token.symbol})</span>
                <span className="px-2 py-0.5 text-[10px] font-mono rounded-full bg-[rgba(0,243,255,0.1)] text-[#00f3ff] border border-[rgba(0,243,255,0.3)]">
                  {token.chain}
                </span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-full ${
                    isRejected
                      ? "bg-[rgba(255,0,85,0.2)] text-[#ff0055] border border-[rgba(255,0,85,0.4)]"
                      : "bg-[rgba(0,255,136,0.2)] text-[#00ff88] border border-[rgba(0,255,136,0.4)]"
                  }`}
                >
                  {isRejected ? "REJECTED BY RISK GATE" : "APPROVED / ACTIVE DOSSIER"}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-mono text-gray-400 truncate max-w-[280px]">
                  Contract: {token.contractAddress}
                </span>
                <button
                  onClick={handleCopyContract}
                  className="p-1 rounded bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(0,243,255,0.2)] text-gray-300 transition-colors"
                  title="Copy Contract"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
                {copied && <span className="text-[10px] font-mono text-[#00ff88]">Copied!</span>}
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="p-2 rounded-lg bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,0,85,0.2)] text-gray-400 hover:text-[#ff0055] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="p-3 rounded-xl bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.2)]">
            <span className="text-[10px] font-mono text-gray-400 block">OPPORTUNITY SCORE</span>
            <span className="text-2xl font-mono font-black text-[#00f3ff]">{token.opportunityScore}/100</span>
          </div>

          <div
            className={`p-3 rounded-xl border ${
              token.securityScore < 50
                ? "bg-[rgba(255,0,85,0.08)] border-[rgba(255,0,85,0.3)]"
                : "bg-[rgba(0,255,136,0.05)] border-[rgba(0,255,136,0.2)]"
            }`}
          >
            <span className="text-[10px] font-mono text-gray-400 block">SECURITY SCORE</span>
            <span
              className={`text-2xl font-mono font-black ${
                token.securityScore < 50 ? "text-[#ff0055]" : "text-[#00ff88]"
              }`}
            >
              {token.securityScore}/100
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[rgba(176,38,255,0.05)] border border-[rgba(176,38,255,0.2)]">
            <span className="text-[10px] font-mono text-gray-400 block">CONFIDENCE</span>
            <span className="text-2xl font-mono font-black text-[#d884ff]">{token.confidenceScore}%</span>
          </div>

          <div className="p-3 rounded-xl bg-[rgba(255,170,0,0.05)] border border-[rgba(255,170,0,0.2)]">
            <span className="text-[10px] font-mono text-gray-400 block">PRICE / 24H</span>
            <span className="text-lg font-mono font-bold text-white block">${token.price}</span>
            <span
              className={`text-xs font-mono font-bold ${
                parseFloat(token.priceChange24h) >= 0 ? "text-[#00ff88]" : "text-[#ff0055]"
              }`}
            >
              {token.priceChange24h}%
            </span>
          </div>
        </div>

        {/* Breakdown Radar Gauges Grid */}
        <div className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] mb-6">
          <h3 className="text-xs font-mono font-bold text-gray-300 uppercase tracking-widest mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#00f3ff]" />
            Multi-Dimensional Intelligence Scores
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Liquidity Depth", val: token.liquidityScore, color: "bg-[#00f3ff]" },
              { label: "Whale Smart Money", val: token.whaleScore, color: "bg-[#00ff88]" },
              { label: "Social Velocity", val: token.socialScore, color: "bg-[#b026ff]" },
              { label: "Narrative Alignment", val: token.narrativeScore, color: "bg-[#ffaa00]" },
            ].map((s, idx) => (
              <div key={idx}>
                <div className="flex justify-between text-[11px] font-mono mb-1">
                  <span className="text-gray-400">{s.label}</span>
                  <span className="text-white font-bold">{s.val}/100</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[rgba(255,255,255,0.1)] overflow-hidden">
                  <div className={`h-full ${s.color}`} style={{ width: `${s.val}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence & Scenarios Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Evidence Summary */}
          <div className="p-4 rounded-xl bg-[rgba(0,243,255,0.03)] border border-[rgba(0,243,255,0.15)]">
            <h4 className="text-xs font-mono font-bold text-[#00f3ff] uppercase mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              Evidence Before Decision Summary
            </h4>
            <p className="text-xs font-mono text-gray-300 leading-relaxed mb-3">
              {token.evidenceSummary || "Multi-source evidence collected."}
            </p>
            <div className="p-2.5 rounded bg-[rgba(255,170,0,0.08)] border border-[rgba(255,170,0,0.2)]">
              <span className="text-[10px] font-mono text-[#ffaa00] font-bold block mb-0.5">RISK AUDIT:</span>
              <p className="text-[11px] font-mono text-gray-300">{token.risksSummary}</p>
            </div>
          </div>

          {/* Scenarios */}
          <div className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] space-y-2">
            <h4 className="text-xs font-mono font-bold text-gray-300 uppercase mb-2">Expected Scenarios</h4>

            <div className="p-2 rounded bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.2)] text-xs font-mono">
              <span className="text-[#00ff88] font-bold">BULL: </span>
              <span className="text-gray-300">{token.bullScenario || "Upside trajectory."}</span>
            </div>

            <div className="p-2 rounded bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.2)] text-xs font-mono">
              <span className="text-[#00f3ff] font-bold">BASE: </span>
              <span className="text-gray-300">{token.baseScenario || "Consolidation phase."}</span>
            </div>

            <div className="p-2 rounded bg-[rgba(255,0,85,0.05)] border border-[rgba(255,0,85,0.2)] text-xs font-mono">
              <span className="text-[#ff0055] font-bold">BEAR: </span>
              <span className="text-gray-300">{token.bearScenario || "Downside protection."}</span>
            </div>
          </div>
        </div>

        {/* 10-Team AI Council Arguments Breakdown */}
        {councilOpinions && councilOpinions.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xs font-mono font-bold text-gray-300 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-[#d884ff]" />
              10-Team AI Council Verifications
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
              {councilOpinions.map((op: any) => (
                <div
                  key={op.id}
                  className="p-3 rounded-lg bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.06)] text-xs font-mono"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-300 font-bold">{op.teamName}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ${
                        op.verdict === "bullish"
                          ? "bg-[rgba(0,255,136,0.15)] text-[#00ff88]"
                          : "bg-[rgba(255,0,85,0.15)] text-[#ff0055]"
                      }`}
                    >
                      {op.verdict}
                    </span>
                  </div>
                  <p className="text-gray-400 text-[11px] leading-relaxed">{op.argument}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions Footer */}
        <div className="flex items-center justify-between border-t border-[rgba(255,255,255,0.1)] pt-4">
          <div className="text-xs font-mono text-gray-400">
            Liquidity Locked: <span className="text-[#00ff88] font-bold">${token.liquidityUsd}</span> | Market Cap:{" "}
            <span className="text-white font-bold">${token.marketCapUsd}</span>
          </div>

          {!isRejected ? (
            <button
              onClick={() => {
                soundFx.playAlert();
                onOpenPaperTrade(token);
              }}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#00f3ff] via-[#00ff88] to-[#b026ff] text-black font-mono font-black text-xs hover:opacity-90 transition-all shadow-[0_0_20px_rgba(0,243,255,0.4)] flex items-center gap-2"
            >
              <DollarSign className="w-4 h-4" />
              EXECUTE SIMULATED PAPER TRADE
            </button>
          ) : (
            <div className="px-4 py-2 rounded-xl bg-[rgba(255,0,85,0.2)] text-[#ff0055] font-mono text-xs border border-[rgba(255,0,85,0.4)] font-bold">
              TRADE BLOCKED BY RISK GATE
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
