"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
} from "lucide-react";

interface PaperTradingSectionProps {
  trades: any[];
  stats: {
    totalPnlUsd: string;
    winRate: string;
    activeTradesCount: number;
    closedTradesCount: number;
  };
  tokensList: any[];
  onTradeUpdated: () => void;
}

export function PaperTradingSection({
  trades,
  stats,
  tokensList,
  onTradeUpdated,
}: PaperTradingSectionProps) {
  const [showNewTradeModal, setShowNewTradeModal] = useState(false);
  const [selectedTokenId, setSelectedTokenId] = useState(tokensList[0]?.id || "");
  const [virtualCapital, setVirtualCapital] = useState("500");
  const [stopLoss, setStopLoss] = useState("0.012");
  const [targetPrice, setTargetPrice] = useState("0.080");
  const [closingTradeId, setClosingTradeId] = useState<string | null>(null);
  const [exitPrice, setExitPrice] = useState("");
  const [postMortemText, setPostMortemText] = useState("");

  const selectedToken = tokensList.find((t) => t.id === selectedTokenId) || tokensList[0];

  const handleOpenTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    soundFx.playClick();
    if (!selectedToken) return;

    try {
      const res = await fetch("/api/paper-trades", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tokenId: selectedToken.id,
          symbol: selectedToken.symbol,
          entryPrice: selectedToken.price || "0.020",
          stopLoss: stopLoss || "0.015",
          targetPrice: targetPrice || "0.060",
          virtualCapital,
        }),
      });
      const data = await res.json();
      if (data.success) {
        soundFx.playAlert();
        setShowNewTradeModal(false);
        onTradeUpdated();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCloseTrade = async (tradeId: string) => {
    soundFx.playClick();
    try {
      const res = await fetch("/api/paper-trades", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: tradeId,
          exitPrice: exitPrice || "0.045",
          postMortem: postMortemText || "Post-Mortem logged into Tree of Wisdom knowledge graph.",
        }),
      });
      const data = await res.json();
      if (data.success) {
        soundFx.playAlert();
        setClosingTradeId(null);
        setExitPrice("");
        setPostMortemText("");
        onTradeUpdated();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-[#0a0e17] border border-[rgba(0,243,255,0.2)] shadow-[0_0_50px_rgba(0,243,255,0.08)]">
      {/* Header & Stats Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-5 mb-6">
        <div>
          <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded bg-[rgba(0,255,136,0.15)] text-[#00ff88] border border-[rgba(0,255,136,0.3)] mb-1 inline-block">
            PAPER TRADING ENGINE
          </span>
          <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-[#00ff88]" />
            Simulated Portfolio & Post-Mortem Learning
          </h2>
          <p className="text-xs font-mono text-gray-400 mt-1">
            Section 16-20 AHOS Master Spec: Every opportunity executes paper positions to test hypotheses before real capital deployment.
          </p>
        </div>

        <button
          onClick={() => {
            soundFx.playClick();
            setShowNewTradeModal(true);
          }}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-mono font-black text-xs flex items-center gap-2 shadow-[0_0_20px_rgba(0,243,255,0.3)] hover:opacity-90 transition-all"
        >
          <Plus className="w-4 h-4" />
          OPEN PAPER POSITION
        </button>
      </div>

      {/* Analytics Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">TOTAL SIMULATED PNL</span>
          <span className="text-2xl font-mono font-black text-[#00ff88]">${stats.totalPnlUsd}</span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">WIN RATE</span>
          <span className="text-2xl font-mono font-black text-[#00f3ff]">{stats.winRate}</span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(176,38,255,0.05)] border border-[rgba(176,38,255,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">ACTIVE POSITIONS</span>
          <span className="text-2xl font-mono font-black text-[#d884ff]">{stats.activeTradesCount}</span>
        </div>

        <div className="p-4 rounded-xl bg-[rgba(255,170,0,0.05)] border border-[rgba(255,170,0,0.2)]">
          <span className="text-[10px] font-mono text-gray-400 block">EVALUATED & CLOSED</span>
          <span className="text-2xl font-mono font-black text-[#ffaa00]">{stats.closedTradesCount}</span>
        </div>
      </div>

      {/* Active & Historical Trade Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-[rgba(255,255,255,0.1)] text-gray-400 uppercase text-[10px]">
              <th className="py-3 px-3">Symbol</th>
              <th className="py-3 px-3">Type</th>
              <th className="py-3 px-3">Entry / Current Price</th>
              <th className="py-3 px-3">Target / Stop</th>
              <th className="py-3 px-3">Capital</th>
              <th className="py-3 px-3">PnL (%)</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(255,255,255,0.05)]">
            {trades.map((trade) => {
              const isWin = parseFloat(trade.pnlPercent || "0") >= 0;
              const isOpen = trade.status === "OPEN";

              return (
                <tr key={trade.id} className="hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                  <td className="py-3 px-3 font-bold text-white flex items-center gap-1.5">
                    {trade.symbol}
                  </td>
                  <td className="py-3 px-3 text-[#00ff88] font-bold">{trade.type}</td>
                  <td className="py-3 px-3 text-gray-300">
                    ${trade.entryPrice} / <span className="text-white font-bold">${trade.currentPrice}</span>
                  </td>
                  <td className="py-3 px-3 text-gray-400">
                    Target: <span className="text-[#00ff88]">${trade.targetPrice}</span> | Stop:{" "}
                    <span className="text-[#ff0055]">${trade.stopLoss}</span>
                  </td>
                  <td className="py-3 px-3 text-gray-300">${trade.virtualCapital}</td>
                  <td className="py-3 px-3 font-bold">
                    <span
                      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[11px] ${
                        isWin
                          ? "bg-[rgba(0,255,136,0.15)] text-[#00ff88]"
                          : "bg-[rgba(255,0,85,0.15)] text-[#ff0055]"
                      }`}
                    >
                      {isWin ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {trade.pnlPercent}% (${trade.pnlUsd})
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isOpen
                          ? "bg-[rgba(0,243,255,0.15)] text-[#00f3ff]"
                          : isWin
                          ? "bg-[rgba(0,255,136,0.2)] text-[#00ff88]"
                          : "bg-[rgba(255,0,85,0.2)] text-[#ff0055]"
                      }`}
                    >
                      {trade.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    {isOpen ? (
                      <button
                        onClick={() => {
                          soundFx.playClick();
                          setClosingTradeId(trade.id);
                          setExitPrice(trade.currentPrice);
                        }}
                        className="px-3 py-1 rounded-lg bg-[rgba(255,170,0,0.15)] text-[#ffaa00] border border-[rgba(255,170,0,0.3)] hover:bg-[rgba(255,170,0,0.25)] transition-colors text-[11px]"
                      >
                        CLOSE & POST-MORTEM
                      </button>
                    ) : (
                      <span className="text-[10px] text-gray-500 italic">Evaluated</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Modal: Open New Trade */}
      {showNewTradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(5,7,12,0.85)] backdrop-blur-md">
          <div className="w-full max-w-md bg-[#0a0e17] border border-[rgba(0,243,255,0.3)] rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold font-mono text-white mb-4">Open Simulated Paper Trade</h3>
            <form onSubmit={handleOpenTrade} className="space-y-4 font-mono text-xs">
              <div>
                <label className="text-gray-400 block mb-1">Select Token</label>
                <select
                  value={selectedTokenId}
                  onChange={(e) => setSelectedTokenId(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
                >
                  {tokensList.map((t) => (
                    <option key={t.id} value={t.id} className="bg-[#0a0e17]">
                      {t.name} ({t.symbol}) - Price: ${t.price}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-gray-400 block mb-1">Virtual Capital (USDT)</label>
                <input
                  type="number"
                  value={virtualCapital}
                  onChange={(e) => setVirtualCapital(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-gray-400 block mb-1">Stop Loss ($)</label>
                  <input
                    type="text"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[rgba(255,0,85,0.1)] border border-[rgba(255,0,85,0.3)] text-[#ff0055]"
                  />
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">Profit Target ($)</label>
                  <input
                    type="text"
                    value={targetPrice}
                    onChange={(e) => setTargetPrice(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[rgba(0,255,136,0.1)] border border-[rgba(0,255,136,0.3)] text-[#00ff88]"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewTradeModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-bold"
                >
                  Submit Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Close Trade & Post-Mortem */}
      {closingTradeId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(5,7,12,0.85)] backdrop-blur-md">
          <div className="w-full max-w-md bg-[#0a0e17] border border-[rgba(255,170,0,0.3)] rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold font-mono text-white mb-2">Trade Post-Mortem Evaluation</h3>
            <p className="text-xs font-mono text-gray-400 mb-4">
              Enter exit price and specify why this hypothesis succeeded or failed to feed the Tree of Wisdom learning engine.
            </p>

            <div className="space-y-4 font-mono text-xs">
              <div>
                <label className="text-gray-400 block mb-1">Exit Price ($)</label>
                <input
                  type="text"
                  value={exitPrice}
                  onChange={(e) => setExitPrice(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
                />
              </div>

              <div>
                <label className="text-gray-400 block mb-1">Post-Mortem Reason / Pattern</label>
                <textarea
                  rows={3}
                  value={postMortemText}
                  onChange={(e) => setPostMortemText(e.target.value)}
                  placeholder="e.g. Target reached on CEX listing announcement. Smart Money accumulation validated."
                  className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setClosingTradeId(null)}
                  className="flex-1 py-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleCloseTrade(closingTradeId)}
                  className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-[#ffaa00] to-[#00ff88] text-black font-bold"
                >
                  Save Post-Mortem
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
