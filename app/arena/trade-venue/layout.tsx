import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../../src/features/trade-venue/styles/venue.css";

export const metadata: Metadata = { title: "AHOS - Trade venue (paper)", robots: { index: false, follow: false } };

export default function TradeVenueLayout({ children }: { children: ReactNode }) {
  return children;
}
