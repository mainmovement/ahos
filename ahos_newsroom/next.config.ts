import { fileURLToPath } from 'node:url';

import type { NextConfig } from 'next';

/**
 * AHOS Newsroom — stand-alone Next.js app.
 *
 * Everything is static & client-rendered: no server secrets, no outbound calls,
 * no API routes. The page reads typed fixtures from `src/mock/newsroom`.
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Dev-server previews are proxied under https://{port}-{sandbox}.e2b.app.
  allowedDevOrigins: ['*'],
  // Keep the bundle honest: no server-side image optimisation needed here.
  images: { unoptimized: true },
  // Keep the build deterministic even when this folder is nested inside a
  // larger repository that happens to have its own lockfile.
  turbopack: { root: fileURLToPath(new URL('.', import.meta.url)) },
};

export default nextConfig;
