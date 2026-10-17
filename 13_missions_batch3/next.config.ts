import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Standalone app: pin the workspace root so unrelated lockfiles (when this
  // folder is checked out inside a bigger repo) are ignored.
  turbopack: { root: import.meta.dirname },
  // Arena preview proxies run under https://{port}-{sandbox}.e2b.app in dev.
  allowedDevOrigins: ["*.e2b.app"],
};

export default nextConfig;
