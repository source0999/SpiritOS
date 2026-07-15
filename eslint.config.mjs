import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const productionBoundaryRestrictions = [
  { group: ["source_proxy/**"], message: "Production TypeScript must cross Source Proxy through shared contracts or an HTTP boundary." },
  { group: ["@/labs/**", "**/labs/**"], message: "Production code cannot import labs; move the dependency back to a canonical surface." },
  { group: ["@/tests/**", "@/fixtures/**", "**/fixtures/**"], message: "Production code cannot depend on tests or fixtures." },
];

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
    "**/.venv/**",
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
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: { "no-restricted-imports": ["error", { patterns: productionBoundaryRestrictions }] },
  },
  {
    files: ["src/{app,components,lib}/coding/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [
        ...productionBoundaryRestrictions,
        { group: ["@/app/spiritflix/**", "@/components/spiritflix/**", "@/lib/spiritflix/**"], message: "Coding cannot import SpiritFlix product code; use a shared contract." },
      ] }],
    },
  },
  {
    files: ["src/{app,components,lib}/spiritflix/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [
        ...productionBoundaryRestrictions,
        { group: ["@/app/coding/**", "@/components/coding/**", "@/lib/coding/**"], message: "SpiritFlix cannot import Coding product code; use a shared contract." },
      ] }],
    },
  },
  {
    files: ["packages/contracts/**/*.{ts,tsx,js,mjs}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [
        { group: ["@/**", "src/**", "source_proxy/**", "scout/**"], message: "Contracts cannot import product runtime code." },
      ] }],
    },
  },
]);

export default eslintConfig;
