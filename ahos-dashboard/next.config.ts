import path from "node:path";
import type { NextConfig } from "next";

/**
 * AHOS dashboard — standalone Next.js app living inside the AHOS monorepo.
 * `turbopack.root` / `outputFileTracingRoot` pin the workspace root to this
 * folder so the parent repository's lockfile is never picked up.
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  turbopack: {
    root: path.resolve(__dirname),
  },
  outputFileTracingRoot: path.resolve(__dirname),
  // three-globe ships ESM that references `three/examples/jsm/*`.
  transpilePackages: ["three-globe"],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
