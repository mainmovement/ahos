"use client";

import React, { useState, useEffect } from "react";
import { soundFx } from "@/utils/audio";
import {
  GitBranch,
  Terminal,
  Play,
  CheckCircle2,
  Folder,
  FileCode,
  Layers,
  Cpu,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

export function GitHubOrchestratorSection() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [executingId, setExecutingId] = useState<string | null>(null);

  const fetchWorkflows = () => {
    fetch("/api/workflows")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setWorkflows(data.workflows);
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleRunWorkflow = async (id: string) => {
    soundFx.playScan();
    setExecutingId(id);

    try {
      const res = await fetch("/api/workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflowId: id }),
      });
      const data = await res.json();
      if (data.success) {
        soundFx.playAlert();
        fetchWorkflows();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setExecutingId(null);
    }
  };

  const repoTree = [
    { name: "src/db/schema.ts", desc: "Drizzle ORM Tokens, Council, Paper Trades & Logs" },
    { name: "src/db/index.ts", desc: "PostgreSQL Connection & Pool Abstraction" },
    { name: "src/utils/audio.ts", desc: "Web Audio Procedural Sound Synthesizer" },
    { name: "src/components/Cyber3DCanvas.tsx", desc: "WebGL / Canvas 3D Neural Network" },
    { name: "src/components/CouncilDebateArena.tsx", desc: "10-Team AI Council Conclave Visualizer" },
    { name: "src/app/api/tokens/route.ts", desc: "Token Discovery & Automated Scan API" },
    { name: "src/app/api/chat/route.ts", desc: "Persian/English AI Assistant & Telegram Bot" },
    { name: "python/ahos_scraper.py", desc: "Solana RPC & Base Contract OSINT Scraper" },
    { name: "workflows/n8n_council.json", desc: "n8n 10-Agent Multi-Model Orchestration Pipeline" },
  ];

  return (
    <div className="p-6 rounded-2xl bg-[#0a0e17] border border-[rgba(0,243,255,0.2)] shadow-[0_0_50px_rgba(0,243,255,0.08)]">
      {/* Header */}
      <div className="border-b border-[rgba(255,255,255,0.08)] pb-5 mb-6">
        <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold rounded bg-[rgba(176,38,255,0.15)] text-[#d884ff] border border-[rgba(176,38,255,0.3)] mb-1 inline-block">
          GITHUB & N8N ORCHESTRATOR
        </span>
        <h2 className="text-2xl font-bold font-mono text-white flex items-center gap-2">
          <GitBranch className="w-6 h-6 text-[#d884ff]" />
          Automation Pipelines & Python OSINT Runners
        </h2>
        <p className="text-xs font-mono text-gray-400 mt-1">
          Section 22, 36 & 47 Master Spec: GitHub as engineering hub + n8n multi-agent orchestration pipelines.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Repository Structure */}
        <div className="lg:col-span-1 p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] font-mono text-xs">
          <h3 className="font-bold text-gray-300 uppercase tracking-widest text-[11px] mb-3 flex items-center gap-2">
            <Folder className="w-4 h-4 text-[#00f3ff]" />
            AHOS Master Repository Tree
          </h3>
          <div className="space-y-2">
            {repoTree.map((item, idx) => (
              <div
                key={idx}
                className="p-2 rounded bg-[rgba(0,243,255,0.03)] border border-[rgba(0,243,255,0.1)] hover:border-[rgba(0,243,255,0.3)] transition-colors"
              >
                <div className="flex items-center gap-1.5 text-white font-bold mb-0.5">
                  <FileCode className="w-3.5 h-3.5 text-[#00ff88]" />
                  {item.name}
                </div>
                <div className="text-[10px] text-gray-400 pl-5">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Workflows & n8n Pipelines */}
        <div className="lg:col-span-2 space-y-4 font-mono text-xs">
          <h3 className="font-bold text-gray-300 uppercase tracking-widest text-[11px] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#00ff88]" />
            Active Automation Workflows
          </h3>

          {workflows.map((wf) => {
            const isRunning = executingId === wf.id;

            return (
              <div
                key={wf.id}
                className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] hover:border-[rgba(0,255,136,0.3)] transition-all"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#00ff88] animate-ping" />
                    <h4 className="font-bold text-white text-sm">{wf.name}</h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[rgba(176,38,255,0.15)] text-[#d884ff] border border-[rgba(176,38,255,0.3)] uppercase">
                      {wf.type}
                    </span>
                  </div>

                  <button
                    onClick={() => handleRunWorkflow(wf.id)}
                    disabled={isRunning}
                    className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#00f3ff] to-[#00ff88] text-black font-bold text-[11px] flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,243,255,0.3)] hover:opacity-90 transition-all"
                  >
                    {isRunning ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        RUNNING...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" />
                        EXECUTE PIPELINE
                      </>
                    )}
                  </button>
                </div>

                <div className="text-gray-400 text-[11px] mb-2">
                  Executions Count: <span className="text-white font-bold">{wf.executionCount}</span> | Last Run:{" "}
                  <span className="text-[#00f3ff]">{new Date(wf.lastRun).toLocaleTimeString()}</span>
                </div>

                <div className="p-2.5 rounded bg-[rgba(5,7,12,0.6)] border border-[rgba(255,255,255,0.06)] text-[11px] text-gray-300 font-mono">
                  <span className="text-[#00ff88] font-bold">LOG SUMMARY: </span>
                  {wf.logSummary || "Pipeline idle and ready."}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
