import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../../src/features/white-hats/styles/wh.css";

export const metadata: Metadata = { title: "AHOS - White hats (paper)", robots: { index: false, follow: false } };

export default function WhiteHatsLayout({ children }: { children: ReactNode }) {
  return children;
}
