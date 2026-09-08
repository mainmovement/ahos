"use client";

import React, { useState, useEffect } from "react";
import { soundFx } from "@/utils/audio";
import { HeaderNav } from "@/components/HeaderNav";
import { Cyber3DCanvas } from "@/components/Cyber3DCanvas";
import { TokenDiscoveryGrid } from "@/components/TokenDiscoveryGrid";
import { TokenDossierModal } from "@/components/TokenDossierModal";
import { CouncilDebateArena } from "@/components/CouncilDebateArena";
import { PaperTradingSection } from "@/components/PaperTradingSection";
import { TreeOfWisdomSection } from "@/components/TreeOfWisdomSection";
import { GitHubOrchestratorSection } from "@/components/GitHubOrchestratorSection";
import { AIChatTelegramDrawer } from "@/components/AIChatTelegramDrawer";
import { MasterVisionModal } from "@/components/MasterVisionModal";
import { QuickScannerModal } from "@/components/QuickScannerModal";
import { SystemHealthSection } from "@/components/SystemHealthSection";
import {
  Zap,
  Search,
  Bot,
  Activity,
  Award,
  ShieldCheck,
  Terminal,
  DollarSign,
  Sparkles,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

export default function Home() {
  const [activeSection, setActiveSection] = useState("overview");
  const [tokens, setTokens] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [tradeStats, setTradeStats] = useState({
    totalPnlUsd: "0.00",
    winRate: "100%",
    activeTradesCount: 0,
    closedTradesCount: 0,
  });

  // Modal & Drawer states
  const [selectedTokenDossier, setSelectedTokenDossier] = useState<any | null>(null);
  const [dossierCouncilOpinions, setDossierCouncilOpinions] = useState<any[]>([]);
  const [showVisionModal, setShowVisionModal] = useState(false);
  const [showChatDrawer, setShowChatDrawer] = useState(false);
  const [showScannerModal, setShowScannerModal] = useState(false);
  const [active3DLayer, setActive3DLayer] = useState("ALL");

  // Fetch Tokens
  const loadTokens = () => {
    fetch("/api/tokens")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setTokens(data.tokens);
        }
      })
      .catch(console.error);
  };

  // Fetch Paper Trades
  const loadPaperTrades = () => {
    fetch("/api/paper-trades")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setTrades(data.trades);
          setTradeStats(data.stats);
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    loadTokens();
    loadPaperTrades();
  }, []);

  // Open Dossier with opinions
  const handleOpenDossier = async (token: any) => {
    soundFx.playClick();
    setSelectedTokenDossier(token);
    try {
      const res = await fetch(`/api/tokens/${token.id}`);
      const data = await res.json();
      if (data.success) {
        setDossierCouncilOpinions(data.councilOpinions);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenPaperTradeFromDossier = (token: any) => {
    setSelectedTokenDossier(null);
    setActiveSection("paper-trading");
  };

  return (
    <div className="min-[#05070c] bg-[#05070c] text-white min-h-screen font-sans selection:bg-[#00f3ff] selection:text-black">
      {/* Background Cyber Ambient Lights */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-[radial-gradient(circle,rgba(0,243,255,0.06)_0%,transparent_70%)] blur-3xl" />
        <div className="absolute top-1/3 right-10 w-[500px] h-[500px] bg-[radial-gradient(circle,rgba(176,38,255,0.05)_0%,transparent_70%)] blur-3xl" />
        <div className="absolute bottom-10 left-1/3 w-[600px] h-[600px] bg-[radial-gradient(circle,rgba(0,255,136,0.04)_0%,transparent_70%)] blur-3xl" />
      </div>

      {/* Navigation Bar */}
      <HeaderNav
        onOpenVision={() => setShowVisionModal(true)}
        onOpenChat={() => setShowChatDrawer(true)}
        onOpenScanner={() => setShowScannerModal(true)}
        activeSection={activeSection}
        setActiveSection={setActiveSection}
      />

      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8 space-y-10">
        {/* Hero Section */}
        <section className="text-center space-y-4 max-w-4xl mx-auto pt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(0,243,255,0.1)] border border-[rgba(0,243,255,0.3)] text-[#00f3ff] font-mono text-xs shadow-[0_0_20px_rgba(0,243,255,0.2)] animate-pulse">
            <Sparkles className="w-3.5 h-3.5" />
            Artificial Hybrid Opportunity Scoring System • Master Vision 1.0
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black font-mono tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-[#00f3ff] to-[#00ff88]">
            EVIDENCE BEFORE DECISION
          </h1>

          <p className="text-sm sm:text-base font-mono text-gray-400 max-w-2xl mx-auto leading-relaxed">
            AHOS is an autonomous intelligence orchestrator. Scans DEXs, On-chain Smart Money, OSINT feeds, and executes 10-team AI Council debates before proposing high-conviction paper trades.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => {
                soundFx.playScan();
                setShowScannerModal(true);
              }}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#00f3ff] via-[#00ff88] to-[#b026ff] text-black font-mono font-black text-xs sm:text-sm flex items-center gap-2 shadow-[0_0_30px_rgba(0,243,255,0.4)] hover:scale-105 transition-transform"
            >
              <Search className="w-4 h-4" />
              SCAN ANY TOKEN CONTRACT
            </button>

            <button
              onClick={() => {
                soundFx.playClick();
                setActiveSection("council");
              }}
              className="px-6 py-3 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white font-mono font-bold text-xs sm:text-sm hover:border-[#00f3ff] hover:text-[#00f3ff] transition-all flex items-center gap-2"
            >
              <Bot className="w-4 h-4" />
              10-TEAM AI COUNCIL DEBATE
            </button>
          </div>
        </section>

        {/* 3D WebGL Canvas Neural Network */}
        <section className="space-y-3">
          <div className="flex items-center justify-between font-mono text-xs">
            <span className="text-gray-400 uppercase tracking-widest flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#00f3ff]" />
              3D Interactive Tree of Wisdom & Intelligence Nodes
            </span>
            <span className="text-[#00ff88] font-bold">Interactive WebGL Shader active</span>
          </div>
          <Cyber3DCanvas activeLayer={active3DLayer} />
        </section>

        {/* Main Section Content Router */}
        {activeSection === "overview" && (
          <div className="space-y-10">
            {/* Top Tokens Preview */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold font-mono text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-[#00f3ff]" />
                  High-Conviction Token Discoveries
                </h2>
                <button
                  onClick={() => setActiveSection("discovery")}
                  className="text-xs font-mono text-[#00f3ff] hover:underline flex items-center gap-1"
                >
                  View All Candidates →
                </button>
              </div>

              <TokenDiscoveryGrid
                tokens={tokens.slice(0, 6)}
                onSelectToken={handleOpenDossier}
                onOpenScanner={() => setShowScannerModal(true)}
              />
            </div>

            {/* Quick 10-Team Debate Preview */}
            <CouncilDebateArena tokensList={tokens} />

            {/* Paper Trading Summary */}
            <PaperTradingSection
              trades={trades}
              stats={tradeStats}
              tokensList={tokens}
              onTradeUpdated={loadPaperTrades}
            />

            {/* System Health */}
            <SystemHealthSection />
          </div>
        )}

        {activeSection === "discovery" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
              <Search className="w-6 h-6 text-[#00f3ff]" />
              AHOS Token Discovery Engine
            </h2>
            <TokenDiscoveryGrid
              tokens={tokens}
              onSelectToken={handleOpenDossier}
              onOpenScanner={() => setShowScannerModal(true)}
            />
          </div>
        )}

        {activeSection === "council" && <CouncilDebateArena tokensList={tokens} />}

        {activeSection === "paper-trading" && (
          <PaperTradingSection
            trades={trades}
            stats={tradeStats}
            tokensList={tokens}
            onTradeUpdated={loadPaperTrades}
          />
        )}

        {activeSection === "tree-of-wisdom" && (
          <TreeOfWisdomSection
            onSelectLayer={(layer) => {
              setActive3DLayer(layer);
            }}
          />
        )}

        {activeSection === "orchestrator" && <GitHubOrchestratorSection />}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t border-[rgba(0,243,255,0.15)] bg-[rgba(5,7,12,0.9)] py-8 font-mono text-xs text-gray-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">AHOS MASTER v1.0</span>
            <span>• Artificial Hybrid Opportunity Scoring System</span>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-[#00ff88]">Evidence Before Decision</span>
            <span>•</span>
            <span className="text-[#00f3ff]">10 AI Council Teams</span>
            <span>•</span>
            <span className="text-[#d884ff]">$0 Initial Budget Specification</span>
          </div>
        </div>
      </footer>

      {/* Modals & Drawers */}
      {selectedTokenDossier && (
        <TokenDossierModal
          token={selectedTokenDossier}
          councilOpinions={dossierCouncilOpinions}
          onClose={() => setSelectedTokenDossier(null)}
          onOpenPaperTrade={handleOpenPaperTradeFromDossier}
        />
      )}

      {showVisionModal && <MasterVisionModal onClose={() => setShowVisionModal(false)} />}

      {showScannerModal && (
        <QuickScannerModal
          onClose={() => setShowScannerModal(false)}
          onTokenDiscovered={loadTokens}
        />
      )}

      <AIChatTelegramDrawer isOpen={showChatDrawer} onClose={() => setShowChatDrawer(false)} />
    </div>
  );
}
