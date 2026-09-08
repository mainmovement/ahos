"use client";

import { cn } from "@/lib/utils";
import type { HTMLAttributes, ReactNode } from "react";
import { motion } from "framer-motion";

export function Card({ children, className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("glass noise-border rounded-2xl p-5", className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, right, icon }: { title: ReactNode; subtitle?: ReactNode; right?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div className="flex items-start gap-3">
        {icon && <div className="mt-0.5 rounded-lg border border-white/10 bg-white/5 p-2 text-cyan-300">{icon}</div>}
        <div>
          <h3 className="font-display text-sm font-semibold tracking-wide text-slate-100">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
        </div>
      </div>
      {right}
    </div>
  );
}

export function RevealCard({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
