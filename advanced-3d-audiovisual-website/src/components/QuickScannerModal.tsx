"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import { Search, X, ShieldAlert, Sparkles, Terminal, Activity } from "lucide-react";

interface QuickScannerModalProps {
  onClose: () => void;
  onTokenDiscovered: () => void;
}

export function QuickScannerModal({ onClose, onTokenDiscovered }: QuickScannerModalProps) {
  const [contractAddress, setContractAddress] = useState("");
  const [chain, setChain] = useState("Solana");
  const [symbol, setSymbol] = useState("");
  const [isScanning, setIsScanning] = useState(false);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contractAddress.trim()) return;

    soundFx.playScan();
    setIsScanning(true);

    try {
      const res = await fetch("/api/tokens", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contractAddress: contractAddress.trim(),
          chain,
          symbol: symbol.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        soundFx.playAlert();
        setIsScanning(false);
        onTokenDiscovered();
        onClose();
      }
    } catch (err) {
      console.error(err);
      setIsScanning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(5,7,12,0.85)] backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-[#0a0e17] border border-[rgba(0,243,255,0.3)] rounded-2xl p-6 shadow-[0_0_80px_rgba(0,243,255,0.2)]">
        <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.1)] pb-4 mb-4">
          <div className="flex items-center gap-2.5">
            <Search className="w-5 h-5 text-[#00f3ff]" />
            <h3 className="text-lg font-bold font-mono text-white">AHOS Deep Contract Scanner</h3>
          </div>
          <button
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="p-2 rounded-lg hover:bg-[rgba(255,0,85,0.2)] text-gray-400 hover:text-[#ff0055] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleScan} className="space-y-4 font-mono text-xs">
          <div>
            <label className="text-gray-400 block mb-1">Contract Address / Token Mint</label>
            <input
              type="text"
              required
              placeholder="e.g. 7xKX3N8sP1zQ9mR4vL2wY8uT6jH1bF3aN5mP"
              value={contractAddress}
              onChange={(e) => setContractAddress(e.target.value)}
              className="w-full p-3 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(0,243,255,0.3)] text-white focus:outline-none focus:border-[#00f3ff]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-gray-400 block mb-1">Blockchain Ecosystem</label>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
              >
                <option value="Solana" className="bg-[#0a0e17]">Solana</option>
                <option value="Base" className="bg-[#0a0e17]">Base</option>
                <option value="Ethereum" className="bg-[#0a0e17]">Ethereum</option>
                <option value="BNB Chain" className="bg-[#0a0e17]">BNB Chain</option>
              </select>
            </div>

            <div>
              <label className="text-gray-400 block mb-1">Symbol (Optional)</label>
              <input
                type="text"
                placeholder="e.g. AHOS"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isScanning}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[#00f3ff] via-[#00ff88] to-[#b026ff] text-black font-black flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,243,255,0.4)] hover:opacity-90 transition-all text-sm"
          >
            {isScanning ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin text-black" />
                SCANNING BYTECODE & DEPLOYING 10 AI TEAMS...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                START DEEP SCAN & DOSSIER GENERATION
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
