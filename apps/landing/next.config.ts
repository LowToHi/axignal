import type { NextConfig } from "next";

import { securityHeaders } from "./lib/security-boundaries";

const production = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders(production)
      }
    ];
  }
};

export default nextConfig;
