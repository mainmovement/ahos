"use client";

import React, { useEffect, useRef } from "react";

interface Node3D {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  radius: number;
  color: string;
  label: string;
  layer: "ROOTS" | "TRUNK" | "BRANCHES" | "LEAVES" | "OCEAN";
  pulse: number;
}

export function Cyber3DCanvas({ activeLayer }: { activeLayer?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 600);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight || 600;
    };
    window.addEventListener("resize", handleResize);

    // Mouse interactive position
    let mouseX = width / 2;
    let mouseY = height / 2;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };
    canvas.addEventListener("mousemove", handleMouseMove);

    // Initialize 3D Nodes representing the AHOS Tree of Wisdom & Ocean
    const nodes: Node3D[] = [];
    const layers: ("ROOTS" | "TRUNK" | "BRANCHES" | "LEAVES" | "OCEAN")[] = [
      "ROOTS",
      "TRUNK",
      "BRANCHES",
      "LEAVES",
      "OCEAN",
    ];
    const colors = {
      ROOTS: "#ffaa00", // Amber Gold Roots
      TRUNK: "#00f3ff", // Electric Cyan Trunk
      BRANCHES: "#00ff88", // Emerald Branches
      LEAVES: "#b026ff", // Cyber Violet Leaves
      OCEAN: "#0077ff", // Ocean Blue Groundwater
    };

    const nodeLabels = [
      { label: "DEX Scraper RPC", layer: "ROOTS" },
      { label: "On-Chain Smart Money", layer: "ROOTS" },
      { label: "Honeypot Red Team", layer: "ROOTS" },
      { label: "Evidence Aggregator", layer: "TRUNK" },
      { label: "10-Team AI Council", layer: "TRUNK" },
      { label: "Math Intelligence", layer: "BRANCHES" },
      { label: "Social Velocity", layer: "BRANCHES" },
      { label: "OSINT Investigator", layer: "BRANCHES" },
      { label: "$AHOS-AI Opportunity", layer: "LEAVES" },
      { label: "$NEURAL-DEP DePIN", layer: "LEAVES" },
      { label: "Groundwater Ocean", layer: "OCEAN" },
      { label: "Post-Mortem Engine", layer: "OCEAN" },
    ];

    for (let i = 0; i < 45; i++) {
      const labelObj = nodeLabels[i % nodeLabels.length];
      nodes.push({
        x: (Math.random() - 0.5) * width * 0.9,
        y: (Math.random() - 0.5) * height * 0.8,
        z: Math.random() * 400 - 200,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        vz: (Math.random() - 0.5) * 0.2,
        radius: Math.random() * 3 + 2,
        color: colors[labelObj.layer as keyof typeof colors],
        label: labelObj.label,
        layer: labelObj.layer as any,
        pulse: Math.random() * Math.PI * 2,
      });
    }

    let angleX = 0;
    let angleY = 0;

    const render = () => {
      ctx.fillStyle = "rgba(5, 7, 12, 0.82)";
      ctx.fillRect(0, 0, width, height);

      // Draw subtle futuristic cyber grid
      ctx.strokeStyle = "rgba(0, 243, 255, 0.04)";
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Smooth camera tilt based on mouse position
      const targetAngleY = ((mouseX - width / 2) / width) * 0.4;
      const targetAngleX = ((mouseY - height / 2) / height) * 0.4;
      angleY += (targetAngleY - angleY) * 0.05;
      angleX += (targetAngleX - angleX) * 0.05;

      const fov = 350;
      const projectedNodes: { px: number; py: number; scale: number; node: Node3D }[] = [];

      // Update and project nodes in 3D
      nodes.forEach((node) => {
        node.pulse += 0.03;
        node.x += node.vx;
        node.y += node.vy;
        node.z += node.vz;

        if (Math.abs(node.x) > width * 0.45) node.vx *= -1;
        if (Math.abs(node.y) > height * 0.4) node.vy *= -1;
        if (Math.abs(node.z) > 200) node.vz *= -1;

        // Rotate Y
        let rx = node.x * Math.cos(angleY) - node.z * Math.sin(angleY);
        let rz = node.x * Math.sin(angleY) + node.z * Math.cos(angleY);
        // Rotate X
        let ry = node.y * Math.cos(angleX) - rz * Math.sin(angleX);
        rz = node.y * Math.sin(angleX) + rz * Math.cos(angleX);

        const distance = fov + rz;
        if (distance > 10) {
          const scale = fov / distance;
          const px = width / 2 + rx * scale;
          const py = height / 2 + ry * scale;
          projectedNodes.push({ px, py, scale, node });
        }
      });

      // Draw 3D Connecting Fiber Lines
      ctx.lineWidth = 0.8;
      for (let i = 0; i < projectedNodes.length; i++) {
        for (let j = i + 1; j < projectedNodes.length; j++) {
          const p1 = projectedNodes[i];
          const p2 = projectedNodes[j];
          const dx = p1.px - p2.px;
          const dy = p1.py - p2.py;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 110) {
            const alpha = (1 - dist / 110) * 0.25;
            ctx.strokeStyle = p1.node.layer === p2.node.layer ? p1.node.color : "rgba(0,243,255,0.15)";
            ctx.globalAlpha = alpha;
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.stroke();
            ctx.globalAlpha = 1;
          }
        }
      }

      // Draw 3D Pulsing Spheres & Neon Labels
      projectedNodes.forEach(({ px, py, scale, node }) => {
        const pulseFactor = 1 + Math.sin(node.pulse) * 0.3;
        const rad = Math.max(1, node.radius * scale * pulseFactor);

        const isHighlighted = activeLayer && node.layer.toLowerCase() === activeLayer.toLowerCase();

        // Glow outer aura
        const grad = ctx.createRadialGradient(px, py, 0, px, py, rad * 3.5);
        grad.addColorStop(0, node.color);
        grad.addColorStop(1, "transparent");

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(px, py, rad * 3.5, 0, Math.PI * 2);
        ctx.fill();

        // Solid core
        ctx.fillStyle = isHighlighted ? "#ffffff" : node.color;
        ctx.beginPath();
        ctx.arc(px, py, rad, 0, Math.PI * 2);
        ctx.fill();

        // Label for primary nodes
        if (scale > 1.1 || isHighlighted) {
          ctx.fillStyle = isHighlighted ? "#00f3ff" : "rgba(255,255,255,0.7)";
          ctx.font = `${Math.round(10 * scale)}px monospace`;
          ctx.fillText(node.label, px + rad + 4, py + 3);
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      canvas.removeEventListener("mousemove", handleMouseMove);
    };
  }, [activeLayer]);

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden border border-[rgba(0,243,255,0.2)] bg-[#05070c] shadow-[0_0_50px_rgba(0,243,255,0.1)]">
      <canvas ref={canvasRef} className="w-full h-full block cursor-crosshair" />

      {/* Floating HUD Badges overlay */}
      <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2 pointer-events-none">
        <span className="px-3 py-1 text-xs font-mono rounded-full bg-[rgba(0,243,255,0.1)] border border-[rgba(0,243,255,0.3)] text-[#00f3ff] backdrop-blur-md flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-ping" />
          WebGL 3D Neural Engine Active
        </span>
        <span className="px-3 py-1 text-xs font-mono rounded-full bg-[rgba(255,170,0,0.1)] border border-[rgba(255,170,0,0.3)] text-[#ffaa00] backdrop-blur-md">
          Tree of Wisdom Layer: {activeLayer ? activeLayer.toUpperCase() : "ALL LAYERS"}
        </span>
      </div>

      <div className="absolute bottom-4 right-4 z-10 text-right pointer-events-none">
        <div className="text-[10px] font-mono text-gray-400">MOUSE PERSPECTIVE TILT</div>
        <div className="text-xs font-mono text-[#00f3ff] tracking-widest">EVIDENCE BEFORE DECISION</div>
      </div>
    </div>
  );
}
