import type { NextConfig } from "next";
import { realpathSync } from "node:fs";

import { buildAllowedDevOrigins } from "./allowed-dev-origins";

/* ── Homelab dev - HMR allowlist + webpack watch ignore (big artifacts) ────────────
 * Next parses `Origin` to hostname only - no `http://` entries.
 * Tailscale / LAN: set `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated hostnames), restart dev.
 */
const nextConfig: NextConfig = {
  experimental: {
    cpus: 1,
    workerThreads: false,
  },

  turbopack: {
    root: realpathSync(process.cwd()),
  },

  allowedDevOrigins: buildAllowedDevOrigins(),

  // SSHFS-hosted pytest cache artefacts are never application inputs. Exclude
  // only their exact generated names from production output tracing.
  outputFileTracingExcludes: {
    "/*": ["./pytest-cache-files-6lyc1rny/**", "./pytest-cache-files-7racnkyv/**"],
  },

  async headers() {
    return [
      {
        source: "/coding",
        headers: [
          {
            key: "Cache-Control",
            value: "no-cache, must-revalidate",
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
          "**/tmp/**",
          "**/docs/evidence/**",
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
