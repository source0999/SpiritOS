import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    exclude: ["**/node_modules/**", "**/.git/**", "**/.spirit-backups/**", "**/docs/handoff/**"],
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    maxWorkers: 4,
    include: ["**/*.{test,spec}.{ts,tsx}"],
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "server-only": path.resolve(__dirname, "./src/test/shims/server-only.ts"),
    },
  },
});
