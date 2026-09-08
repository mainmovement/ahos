"use client";

import React, { useState } from "react";
import { soundFx } from "@/utils/audio";
import {
  Volume2,
  VolumeX,
  Shield,
  Bot,
  Zap,
  BookOpen,
  GitBranch,
  Terminal,
  Search,
  Activity,
} from "lucide-react";

interface HeaderNavProps {
  onOpenVision: () => void;
  onOpenChat: () => void;
  onOpenScanner: () => void;
  activeSection: string;
  setActiveSection: (sec: string) => void;
}

export function HeaderNav({
  onOpenVision,
  onOpenChat,
  onOpenScanner,
  activeSection,
  setActiveSection,
}: HeaderNavProps) {
  const [isMuted, setIsMuted] = useState(soundFx.isMuted);

  const handleAudioToggle = () => {
    const muted = soundFx.toggleMute();
    setIsMuted(muted);
  };

  const navItems = [
    { id: "overview", label: "Overview 3D", icon: Zap },
    { id: "discovery", label: "Token Discovery", icon: Search },
    { id: "council", label: "10-AI Council", icon: Bot },
    { id: "paper-trading", label: "Paper Trading", icon: Activity },
    { id: "tree-of-wisdom", label: "Tree of Wisdom", icon: Terminal },
    { id: "orchestrator", label: "GitHub & n8n", icon: GitBranch },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[rgba(0,243,255,0.18)] bg-[rgba(5,7,12,0.85)] backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Brand Identity & Master Badge */}
        <div className="flex items-center gap-3">
          <div
            onClick={() => {
              soundFx.playClick();
              setActiveSection("overview");
            }}
            className="cursor-pointer flex items-center gap-2.5 group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00f3ff] via-[#b026ff] to-[#ff0055] p-[1.5px] shadow-[0_0_20px_rgba(0,243,255,0.4)] transition-transform group-hover:scale-105">
              <div className="w-full h-full bg-[#05070c] rounded-[10px] flex items-center justify-center">
                <span className="font-mono font-black text-transparent bg-clip-text bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-base tracking-tighter">
                  AHOS
                </span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold tracking-wider text-white group-hover:text-[#00f3ff] transition-colors">
                  AHOS
                </span>
                <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-[rgba(0,255,136,0.15)] text-[#00ff88] border border-[rgba(0,255,136,0.3)]">
                  MASTER v1.0
                </span>
              </div>
              <p className="text-[10px] font-mono text-gray-400 hidden sm:block">
                Artificial Hybrid Opportunity Scoring System
              </p>
            </div>
          </div>
        </div>

        {/* Center Nav Links */}
        <nav className="hidden lg:flex items-center gap-1 bg-[rgba(255,255,255,0.03)] p-1 rounded-xl border border-[rgba(255,255,255,0.06)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  soundFx.playClick();
                  setActiveSection(item.id);
                }}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-[rgba(0,243,255,0.2)] to-[rgba(176,38,255,0.2)] text-[#00f3ff] border border-[rgba(0,243,255,0.4)] shadow-[0_0_15px_rgba(0,243,255,0.2)]"
                    : "text-gray-400 hover:text-white hover:bg-[rgba(255,255,255,0.05)]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Action Controls: Audio, Quick Scan, Master Specification, Telegram Bot */}
        <div className="flex items-center gap-2">
          {/* Quick Scan Button */}
          <button
            onClick={() => {
              soundFx.playScan();
              onOpenScanner();
            }}
            className="px-3 py-1.5 rounded-lg bg-[rgba(0,243,255,0.1)] border border-[rgba(0,243,255,0.3)] text-[#00f3ff] hover:bg-[rgba(0,243,255,0.2)] transition-all font-mono text-xs flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,243,255,0.2)]"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Quick Scan</span>
          </button>

          {/* Master Vision Doc Reader */}
          <button
            onClick={() => {
              soundFx.playClick();
              onOpenVision();
            }}
            className="px-3 py-1.5 rounded-lg bg-[rgba(176,38,255,0.15)] border border-[rgba(176,38,255,0.3)] text-[#d884ff] hover:bg-[rgba(176,38,255,0.25)] transition-all font-mono text-xs flex items-center gap-1.5"
            title="Read Master Vision Specification Document"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Master Vision</span>
          </button>

          {/* Telegram / AI Chat Simulator */}
          <button
            onClick={() => {
              soundFx.playClick();
              onOpenChat();
            }}
            className="p-2 rounded-lg bg-[rgba(0,255,136,0.1)] border border-[rgba(0,255,136,0.3)] text-[#00ff88] hover:bg-[rgba(0,255,136,0.2)] transition-all flex items-center gap-1.5 font-mono text-xs"
            title="AI Chat & Telegram Bot Simulator"
          >
            <Bot className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
          </button>

          {/* Audio Synthesizer Toggle */}
          <button
            onClick={handleAudioToggle}
            className={`p-2 rounded-lg border transition-all ${
              isMuted
                ? "bg-[rgba(255,0,85,0.1)] border-[rgba(255,0,85,0.3)] text-[#ff0055]"
                : "bg-[rgba(0,243,255,0.1)] border-[rgba(0,243,255,0.3)] text-[#00f3ff]"
            }`}
            title={isMuted ? "Unmute Procedural Audio" : "Mute Sound Effects"}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}
