import type { NextConfig } from "next";

import { buildAllowedDevOrigins } from "./allowed-dev-origins";

/* ── Homelab dev — HMR allowlist + webpack watch ignore (big artifacts) ────────────
 * Next parses `Origin` to hostname only — no `http://` entries.
 * Tailscale / LAN: set `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated hostnames), restart dev.
 */
const nextConfig: NextConfig = {
  turbopack: {},

  allowedDevOrigins: buildAllowedDevOrigins(),

  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.watchOptions = {
        ...(config.watchOptions ?? {}),
        ignored: [
          "**/node_modules/**",
          "**/.git/**",
          "**/.next/**",
          "**/models/**",
          "**/backend/**",
          "**/.cursor/**",
          "**/repomix-output*.xml",
          "**/oldSpiritOS.xml",
          "**/*.gguf",
        ],
      };
    }
    if (!isServer) {
      config.devServer = {
        ...config.devServer,
        client: {
          webSocketURL: "auto://0.0.0.0:0/ws",
        },
      };
    }
    return config;
  },
};

export default nextConfig;
