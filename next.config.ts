import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Prefer explicit unstable_cache TTLs in API routes over cacheComponents
  // (cacheComponents conflicts with route segment configs we need for market data).
};

export default nextConfig;
