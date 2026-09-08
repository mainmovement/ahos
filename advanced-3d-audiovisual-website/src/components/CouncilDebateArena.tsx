"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import {
  Bot,
  Play,
  CheckCircle2,
  AlertOctagon,
  Award,
  Zap,
  RefreshCw,
  Sliders,
  ShieldAlert,
  Flame,
} from "lucide-react";

interface CouncilDebateArenaProps {
  tokensList: any[];
}

export function CouncilDebateArena({ tokensList }: CouncilDebateArenaProps) {
  const [selectedTokenId, setSelectedTokenId] = useState<string>(tokensList[0]?.id || "");
  const [isDebating, setIsDebating] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  const selectedToken = tokensList.find((t) => t.id === selectedTokenId) || tokensList[0];

  const councilTeams = [
    {
      code: "TEAM-01",
      name: "Mathematical Intelligence",
      role: "Statistics, Probability & Bayesian Reasoning",
      verdict: "BULLISH",
      confidence: 92,
      quote: "Hurst exponent = 0.74 confirms strong trend persistence. Decay function shows institutional accumulation curves.",
      color: "text-[#00f3ff]",
    },
    {
      code: "TEAM-02",
      name: "Crypto Market Intelligence",
      role: "Tokenomics, DEX Liquidity & Orderbook",
      verdict: "BULLISH",
      confidence: 89,
      quote: "DEX liquidity pool depth to market cap ratio is at optimal 21.7% with low slippage on $10k swaps.",
      color: "text-[#00ff88]",
    },
    {
      code: "TEAM-03",
      name: "Blockchain & On-Chain Intelligence",
      role: "Whale Tracking & Smart Money Graph",
      verdict: "BULLISH",
      confidence: 94,
      quote: "14 Smart Money wallets accumulated $420k without CEX deposit transfers over 24 hours.",
      color: "text-[#b026ff]",
    },
    {
      code: "TEAM-04",
      name: "Cybersecurity & Hacker Intelligence",
      role: "Red Team Contract Audit & Honeypot Detector",
      verdict: selectedToken?.securityScore < 50 ? "REJECT" : "APPROVED",
      confidence: 96,
      quote:
        selectedToken?.securityScore < 50
          ? "CRITICAL REJECT: Unrenounced proxy contract allows instant fee manipulation."
          : "Contract verified. Mint & Freeze authorities revoked. LP locked for 730 days.",
      color: selectedToken?.securityScore < 50 ? "text-[#ff0055]" : "text-[#00ff88]",
    },
    {
      code: "TEAM-05",
      name: "Investigative Intelligence",
      role: "OSINT Detective & Deployer History",
      verdict: "BULLISH",
      confidence: 88,
      quote: "Deployer keypair linked to verified GitHub profile with 8 years of Rust developer contributions.",
      color: "text-[#ffaa00]",
    },
    {
      code: "TEAM-06",
      name: "News & Journalism Intelligence",
      role: "Source Verification & Media Monitoring",
      verdict: "BULLISH",
      confidence: 85,
      quote: "Verified organic press coverage on Blockworks without PR distribution flags.",
      color: "text-[#00f3ff]",
    },
    {
      code: "TEAM-07",
      name: "Social & Narrative Intelligence",
      role: "X/Telegram Sentiment & Bot Filter",
      verdict: "BULLISH",
      confidence: 91,
      quote: "Social velocity is in the 90th percentile with a bot interaction ratio under 4.2%.",
      color: "text-[#d884ff]",
    },
    {
      code: "TEAM-08",
      name: "Technology & Software Engineering",
      role: "GitHub Velocity & Code Quality",
      verdict: "BULLISH",
      confidence: 93,
      quote: "48 commits in last 7 days across 12 active repositories. Rust test pass rate = 100%.",
      color: "text-[#00ff88]",
    },
    {
      code: "TEAM-09",
      name: "AI Research & Self-Evolution",
      role: "RAG Memory & Model Comparison",
      verdict: "BULLISH",
      confidence: 90,
      quote: "Pattern matches historical high-conviction momentum cluster #204.",
      color: "text-[#00f3ff]",
    },
    {
      code: "TEAM-10",
      name: "Strategic Decision & Red-Team Council",
      role: "Contrarian Challenge & Confirmation Bias Neutralizer",
      verdict: selectedToken?.securityScore < 50 ? "REJECT" : "BULLISH",
      confidence: 87,
      quote:
        selectedToken?.securityScore < 50
          ? "FINAL RED-TEAM REJECT: Safety gate takes absolute precedence over potential reward."
          : "Worst-case scenario analyzed (-20% market drop = max $0.028 drawdown). R:R = 1:5.2. Approved.",
      color: selectedToken?.securityScore < 50 ? "text-[#ff0055]" : "text-[#ffaa00]",
    },
  ];

  const handleRunDebate = () => {
    soundFx.playScan();
    setIsDebating(true);
    setActiveStep(0);

    let step = 0;
    const interval = setInterval(() => {
      step++;
      soundFx.playAgentBlip(step * 30);
      setActiveStep(step);
      if (step >= councilTeams.length) {
        clearInterval(interval);
        setIsDebating(false);
        if (selectedToken?.securityScore >= 50) {
          soundFx.playAlert();
        } else {
          soundFx.playReject();
        }
      }
    }, 600);
  };

  return (
    <div className="p-6 rounded-2xl bg-[#0a0e17] border border-[rgba(0,243,255,0.2)] shadow-[0_0_50px_rgba(0,243,255,0.08)]">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-5 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded bg-[rgba(176,38,255,0.15)] text-[#d884ff] border border-[rgba(176,38,255,0.3)]">
              MULTI-AGENT CONCLAVE
            </span>
            <span className="text-xs font-mono text-gray-400">Section 11-13 AHOS Master Specification</span>
          </div>
          <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
            <Bot className="w-6 h-6 text-[#00f3ff]" />
            10-Team AI Council Debate Arena
          </h2>
          <p className="text-xs font-mono text-gray-400 mt-1">
            Independent specialized agent teams conduct cross-examinations before final consensus scoring.
          </p>
        </div>

        {/* Token Selector & Trigger */}
        <div className="flex items-center gap-3">
          <select
            value={selectedTokenId}
            onChange={(e) => {
              soundFx.playClick();
              setSelectedTokenId(e.target.value);
            }}
            className="px-3 py-2 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(0,243,255,0.3)] font-mono text-xs text-white focus:outline-none focus:border-[#00f3ff]"
          >
            {tokensList.map((t) => (
              <option key={t.id} value={t.id} className="bg-[#0a0e17] text-white">
                {t.name} ({t.symbol}) - Opp: {t.opportunityScore}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunDebate}
            disabled={isDebating}
            className={`px-5 py-2.5 rounded-xl font-mono text-xs font-bold flex items-center gap-2 transition-all ${
              isDebating
                ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                : "bg-gradient-to-r from-[#00f3ff] via-[#b026ff] to-[#00ff88] text-black shadow-[0_0_25px_rgba(0,243,255,0.4)] hover:opacity-95"
            }`}
          >
            {isDebating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                DEBATING...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                RUN LIVE DEBATE
              </>
            )}
          </button>
        </div>
      </div>

      {/* Grid of 10 AI Council Teams */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
        {councilTeams.map((team, idx) => {
          const isRevealed = idx < activeStep || (!isDebating && activeStep === 0);
          const isCurrentActive = isDebating && idx === activeStep - 1;

          return (
            <div
              key={team.code}
              className={`p-3.5 rounded-xl border transition-all ${
                isCurrentActive
                  ? "bg-[rgba(0,243,255,0.15)] border-[#00f3ff] shadow-[0_0_20px_rgba(0,243,255,0.3)] scale-[1.02]"
                  : isRevealed
                  ? "bg-[rgba(255,255,255,0.03)] border-[rgba(255,255,255,0.08)] hover:border-[rgba(0,243,255,0.2)]"
                  : "bg-[rgba(255,255,255,0.01)] border-transparent opacity-40"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-[10px] font-mono font-bold ${team.color}`}>{team.code}</span>
                <span
                  className={`text-[9px] font-mono font-black px-1.5 py-0.2 rounded uppercase ${
                    team.verdict === "REJECT"
                      ? "bg-[rgba(255,0,85,0.2)] text-[#ff0055]"
                      : "bg-[rgba(0,255,136,0.2)] text-[#00ff88]"
                  }`}
                >
                  {team.verdict}
                </span>
              </div>

              <h4 className="text-xs font-mono font-bold text-white leading-tight mb-0.5">{team.name}</h4>
              <span className="text-[9px] font-mono text-gray-500 block mb-2">{team.role}</span>

              {isRevealed ? (
                <div className="space-y-1.5 border-t border-[rgba(255,255,255,0.06)] pt-1.5">
                  <p className="text-[10px] font-mono text-gray-300 leading-snug line-clamp-3">"{team.quote}"</p>
                  <div className="flex justify-between items-center text-[9px] font-mono text-gray-400">
                    <span>Confidence</span>
                    <span className="text-[#00f3ff] font-bold">{team.confidence}%</span>
                  </div>
                </div>
              ) : (
                <div className="py-3 text-center text-[10px] font-mono text-gray-600 animate-pulse">
                  Awaiting Debate Turn...
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Consensus Bar */}
      <div className="p-4 rounded-xl bg-[rgba(0,243,255,0.04)] border border-[rgba(0,243,255,0.2)] flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Award className="w-8 h-8 text-[#00ff88]" />
          <div>
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-widest block">
              COUNCIL CONSENSUS GAUGING
            </span>
            <div className="flex items-center gap-2">
              <span className="text-lg font-mono font-black text-white">
                {selectedToken?.securityScore < 50 ? "REJECTED BY RED TEAM" : "91.4% AGENT CONSENSUS (HIGH CONVICTION)"}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right font-mono text-xs text-gray-400">
          Target Token: <span className="text-[#00f3ff] font-bold">{selectedToken?.symbol}</span> | Score:{" "}
          <span className="text-[#00ff88] font-bold">{selectedToken?.opportunityScore}/100</span>
        </div>
      </div>
    </div>
  );
}
