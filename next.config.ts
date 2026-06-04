import type { NextConfig } from "next";
import { realpathSync } from "node:fs";

import { buildAllowedDevOrigins } from "./allowed-dev-origins";

/* ── Homelab dev - HMR allowlist + webpack watch ignore (big artifacts) ────────────
 * Next parses `Origin` to hostname only - no `http://` entries.
 * Tailscale / LAN: set `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated hostnames), restart dev.
 */
const nextConfig: NextConfig = {
  turbopack: {
    root: realpathSync(process.cwd()),
  },

  allowedDevOrigins: buildAllowedDevOrigins(),

  async headers() {
    return [
      {
        source: "/coding",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store, max-age=0, must-revalidate",
          },
          {
            key: "Clear-Site-Data",
            value: '"cache"',
          },
        ],
      },
    ];
  },

  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.cache = false;
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
    return config;
  },
};

export default nextConfig;
