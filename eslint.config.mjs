import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Extracted Vite design reference — not part of Next build / lint surface.
    "_reference/**",
    // Local agent/runtime artifacts and generated context bundles are outside
    // the frontend lint surface and can make repo-root linting crawl.
    ".claude/**",
    ".codex-smoke/**",
    ".cursor/**",
    ".spirit-backups/**",
    ".venv-source-proxy/**",
    ".venv-source-proxy-windows/**",
    "backend/**",
    "data/**",
    "models/**",
    "source_proxy/**",
    "repomix-output*.xml",
    "oldSpiritOS.xml",
    "*.log",
  ]),
]);

export default eslintConfig;
