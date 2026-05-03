import type { NextConfig } from "next";

/* ── Homelab dev — hostname allowlist + webpack watch ignore (big artifacts) ───
 * Next parses `Origin` to hostname only — no `http://` entries.
 */
const nextConfig: NextConfig = {
  turbopack: {},

  allowedDevOrigins: [
    "10.0.0.186",
    "localhost",
    "127.0.0.1",
    "*.ts.net",
  ],

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
