import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../../src/features/trade-venue/styles/venue.css";
import "../../../src/features/missions-b2/styles.css";

export const metadata: Metadata = { title: "AHOS - weekly-exam (paper)", robots: { index: false, follow: false } };

export default function WeeklyExamPageLayout({ children }: { children: ReactNode }) {
  return children;
}
