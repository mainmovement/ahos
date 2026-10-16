import type { NextConfig } from "next";

/**
 * Self-contained config — no external services, no network at runtime.
 * Fonts are bundled locally via @fontsource (see src/app/layout.tsx).
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  // No dev-indicator badge: this is a premium audit terminal surface.
  devIndicators: false,
  // This app is self-contained: its own folder is the tracing root
  // (silences the multiple-lockfile warning when embedded in a monorepo).
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
