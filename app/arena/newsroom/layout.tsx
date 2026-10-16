import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../../src/features/newsroom/styles/nw.css";

export const metadata: Metadata = { title: "AHOS - Newsroom (paper)", robots: { index: false, follow: false } };

export default function NewsroomLayout({ children }: { children: ReactNode }) {
  return children;
}
