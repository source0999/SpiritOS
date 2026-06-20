#!/usr/bin/env node
// ── SpiritOS Repomix shim ───────────────────────────────────────────
// Replaces bare `repomix` in node_modules/.bin so the familiar CLI shape
// produces an LLM-ready Tree-sitter + Headroom bundle, not a 300MB dump.
import { buildRepositoryContextBundle } from "./source-context-compress.mjs";

const args = process.argv.slice(2);

if (args.includes("--help") || args.includes("-h")) {
  console.log(`SpiritOS repository context packer (Repomix Tree-sitter + Headroom)

Usage:
  npm run context:source-proxy-min
  npx repomix --profile source-proxy-min .
  npx repomix --config repomix.source-proxy-min.config.json .

Profiles:
  source-proxy-min (default)  Source Proxy + coding lane — upload this
  repo-map                    High-level layout + pivot docs only
  default                     Legacy full-tree pack (debug only)

Outputs (per profile):
  repomix-output.<profile>.xml          LLM handoff
  repomix-output.<profile>.ast.xml      mirror
  repomix-output.<profile>.headroom.xml Headroom review copy

Flags:
  --profile <name>      source-proxy-min | repo-map | default
  --full                Raw Repomix only → repomix-output.<profile>.full.xml
  --headroom-only       Re-run Headroom against existing AST bundle
  --config <path>       Override profile config file

Headroom proxy (port 8797 — not Source Proxy on 8787):
  npm run headroom:proxy
  npm run context:headroom:check

Env:
  HEADROOM_BASE_URL=http://127.0.0.1:8797
  HEADROOM_CONTEXT_TOKEN_BUDGET=80000
  HEADROOM_API_KEY=...           Headroom Cloud instead of local proxy
`);
  process.exit(0);
}

const profile = readFlagValue("--profile") || "source-proxy-min";

await buildRepositoryContextBundle({
  profile,
  configPath: readFlagValue("--config"),
  targetPath: readPositionalPath(),
  headroomOnly: args.includes("--headroom-only"),
  fullOnly: args.includes("--full"),
});

function readFlagValue(flag) {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
}

function readPositionalPath() {
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--config" || arg === "--output" || arg === "--profile") {
      index += 1;
      continue;
    }
    if (!arg.startsWith("--")) {
      return arg;
    }
  }
  return ".";
}
