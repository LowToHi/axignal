import type { NextConfig } from "next";

import { securityHeaders } from "./lib/security-boundaries";

const production = process.env.NODE_ENV === "production";
const buildId = process.env.AXIGNAL_BUILD_SHA ?? "axignal-local-build";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  generateBuildId: async () => buildId,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders(production),
      },
    ];
  },
};

export default nextConfig;
