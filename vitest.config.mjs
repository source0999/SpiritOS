import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    exclude: [
      "**/node_modules/**",
      "**/.git/**",
      "**/.codex-worktrees/**",
      "**/.spirit-backups/**",
      "**/docs/handoff/**",
    ],
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    maxWorkers: 1,
    include: ["**/*.{test,spec}.{ts,tsx}"],
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@labs": path.resolve(__dirname, "./labs"),
      "server-only": path.resolve(__dirname, "./src/test/shims/server-only.ts"),
    },
  },
});
