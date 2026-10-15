import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../src/styles/shell.css";
import "../../src/styles/dashboard.css";
import "../../src/styles/globe.css";

export const metadata: Metadata = {
  title: "AHOS - Arena workspace",
  description: "AHOS intelligence workspace (Arena AI build). Evidence-first. Paper-only.",
};

export default function ArenaLayout({ children }: { children: ReactNode }) {
  return children;
}