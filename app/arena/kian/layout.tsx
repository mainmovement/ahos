import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../../src/features/missions-b2/styles.css";

export const metadata: Metadata = {
  title: "AHOS - Kian chat (paper)",
  robots: { index: false, follow: false },
};

export default function KianArenaLayout({ children }: { children: ReactNode }) {
  return children;
}
