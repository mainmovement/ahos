import type { Metadata } from "next";
import type { ReactNode } from "react";
import "../../src/styles/shell.css";
import "../../src/styles/dashboard.css";
import "../../src/styles/globe.css";

export const metadata: Metadata = {
  title: "AHOS - Arena workspace",
  icons: {
    icon: [
      { url: "/brand/logo/favicon/ahos-favicon-32.svg", type: "image/svg+xml", sizes: "32x32" },
      { url: "/brand/logo/favicon/ahos-favicon-16.svg", type: "image/svg+xml", sizes: "16x16" },
    ],
    apple: "/brand/logo/ahos-app-icon.svg",
  },
  description: "AHOS intelligence workspace (Arena AI build). Evidence-first. Paper-only.",
};

export default function ArenaLayout({ children }: { children: ReactNode }) {
  return children;
}