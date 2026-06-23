#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compress } from "headroom-ai";

const repoRoot = resolve(import.meta.dirname, "..");
const DEFAULT_HEADROOM_PORT = 8797;
const DEFAULT_HEADROOM_BASE_URL = `http://127.0.0.1:${DEFAULT_HEADROOM_PORT}`;
const DEFAULT_TOKEN_BUDGET = 80_000;
const DEFAULT_HEADROOM_TARGET_RATIO = 0.5;
const DEFAULT_HEADROOM_CHUNK_CHARS = 100_000;

const PROFILE_CONFIGS = {
  "source-proxy-min": "repomix.source-proxy-min.config.json",
  "repo-map": "repomix.repo-map.config.json",
  default: "repomix.config.json",
};

export function resolveContextProfile(options = {}) {
  const profile = options.profile || "source-proxy-min";
  const configPath =
    options.configPath || PROFILE_CONFIGS[profile] || PROFILE_CONFIGS.default;
  const slug = profile === "default" ? "" : `.${profile}`;
  return {
    profile,
    configPath,
    slug,
    llmOutput: resolve(repoRoot, `repomix-output${slug}.xml`),
    astOutput: resolve(repoRoot, `repomix-output${slug}.ast.xml`),
    headroomOutput: resolve(repoRoot, `repomix-output${slug}.headroom.xml`),
    innerOutput: resolve(repoRoot, `repomix-output${slug}.ast-inner.xml`),
    fullOutput: resolve(repoRoot, `repomix-output${slug}.full.xml`),
  };
}

export async function buildRepositoryContextBundle(options = {}) {
  const {
    targetPath = ".",
    headroomOnly = false,
    fullOnly = false,
  } = options;

  const profilePaths = resolveContextProfile(options);
  const {
    profile,
    configPath,
    innerOutput,
    llmOutput,
    astOutput,
    headroomOutput,
    fullOutput,
  } = profilePaths;

  const repomixCli = resolve(repoRoot, "node_modules", "repomix", "bin", "repomix.cjs");
  const headroomBaseUrl = (process.env.HEADROOM_BASE_URL || DEFAULT_HEADROOM_BASE_URL).replace(/\/$/, "");
  const headroomCompressionConfig = resolveHeadroomCompressionConfig();

  if (fullOnly) {
    execFileSync(
      process.execPath,
      [repomixCli, "--config", configPath, "--output", fullOutput, targetPath],
      { cwd: repoRoot, stdio: "inherit" },
    );
    console.log(`Full (uncompressed) context written to ${fullOutput}`);
    return {
      profile,
      configPath,
      llmOutput: fullOutput,
      compression: "none",
      headroomActuallyCompressed: false,
      headroomProxyReachable: false,
    };
  }

  if (!headroomOnly) {
    execFileSync(
      process.execPath,
      [
        repomixCli,
        "--config",
        configPath,
        "--compress",
        "--output",
        innerOutput,
        targetPath,
      ],
      { cwd: repoRoot, stdio: "inherit" },
    );
  }

  const repomixSource = headroomOnly ? astOutput : innerOutput;
  const compressedRepomixXml = readFileSync(repomixSource, "utf8")
    .replace(/^\uFEFF/, "")
    .replace(/^<\?xml[^>]*>\s*/u, "")
    .trim();
  const repositoryContextXml = extractRepositoryContextXml(compressedRepomixXml);

  const systemDirective = [
    "This is a compressed repository context generated for Source proxy planning.",
    "The repository_context payload was produced by Repomix Tree-sitter compression and may include an additional Headroom pass.",
    "Use file paths and structural signatures as read-only context.",
    "When implementation detail is absent, request or inspect the original file before editing.",
  ].join(" ");

  const proxyReachable = await probeHeadroomProxy(headroomBaseUrl);
  if (!proxyReachable) {
    console.warn(
      [
        `Headroom proxy not reachable at ${headroomBaseUrl}.`,
        `Tree-sitter Repomix output will be used without further Headroom compression.`,
        `Start the proxy: npm run headroom:proxy`,
        `Or set HEADROOM_API_KEY for Headroom Cloud.`,
      ].join(" "),
    );
  }

  const headroomMessages = chunkText(
    repositoryContextXml,
    Number(process.env.HEADROOM_CONTEXT_CHUNK_CHARS || DEFAULT_HEADROOM_CHUNK_CHARS),
  ).map((content) => ({ role: "user", content }));
  const headroomResult = await compress(
    headroomMessages,
    {
      model: process.env.HEADROOM_CONTEXT_MODEL || "gpt-4o",
      baseUrl: headroomBaseUrl,
      apiKey: process.env.HEADROOM_API_KEY,
      fallback: true,
      retries: proxyReachable ? 1 : 0,
      stack: "spiritos-repomix-context",
      tokenBudget: Number(process.env.HEADROOM_CONTEXT_TOKEN_BUDGET || DEFAULT_TOKEN_BUDGET),
      timeout: Number(process.env.HEADROOM_CONTEXT_TIMEOUT_MS || 180_000),
      config: headroomCompressionConfig,
    },
  );

  const headroomContent = joinHeadroomMessages(headroomResult.messages) || repositoryContextXml;
  const headroomTokensSaved = Number(headroomResult.tokensSaved || 0);
  const headroomActuallyCompressed = Boolean(
    headroomResult.compressed && headroomTokensSaved > 0 && headroomContent !== repositoryContextXml,
  );
  const headroomFallbackReason = resolveHeadroomFallbackReason({
    proxyReachable,
    headroomResult,
    headroomContent,
    repositoryContextXml,
  });

  const wrappedXml = wrapContextXml({
    compression: headroomActuallyCompressed ? "tree-sitter+headroom" : "tree-sitter",
    generator: headroomActuallyCompressed ? "repomix,headroom-ai" : "repomix",
    systemDirective,
    contextXml: headroomActuallyCompressed ? headroomContent : repositoryContextXml,
    headroomResult,
    headroomBaseUrl,
    headroomActuallyCompressed,
    headroomFallbackReason,
  });

  writeFileSync(llmOutput, wrappedXml, "utf8");
  writeFileSync(astOutput, wrappedXml, "utf8");
  writeFileSync(
    headroomOutput,
    wrapContextXml({
      compression: headroomActuallyCompressed ? "tree-sitter+headroom" : "tree-sitter",
      generator: headroomActuallyCompressed ? "repomix,headroom-ai" : "repomix",
      systemDirective,
      contextXml: headroomContent,
      headroomResult,
      headroomBaseUrl,
      headroomActuallyCompressed,
      headroomFallbackReason,
    }),
    "utf8",
  );
  rmSync(innerOutput, { force: true });

  const llmBytes = readFileSync(llmOutput).byteLength;
  console.log(`Profile: ${profile} (config: ${configPath})`);
  console.log(`LLM context written to ${llmOutput} (${formatBytes(llmBytes)})`);
  console.log(`AST mirror written to ${astOutput}`);
  console.log(
    headroomActuallyCompressed
      ? `Headroom pass saved ${headroomResult.tokensSaved} tokens (${headroomResult.compressionRatio}x) via ${headroomBaseUrl}`
      : `Headroom pass skipped or had no savings — Tree-sitter payload only (${headroomBaseUrl})`,
  );

  return {
    profile,
    configPath,
    llmOutput,
    astOutput,
    headroomOutput,
    headroomActuallyCompressed,
    headroomProxyReachable: proxyReachable,
    headroomResult,
  };
}

function parseCliArgs(argv) {
  const args = argv.slice(2);
  let configPath;
  let profile = "source-proxy-min";
  let targetPath = ".";
  const flags = new Set();

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--config" && args[index + 1]) {
      configPath = args[index + 1];
      index += 1;
      continue;
    }
    if (arg === "--profile" && args[index + 1]) {
      profile = args[index + 1];
      index += 1;
      continue;
    }
    if (arg === "--output" && args[index + 1]) {
      index += 1;
      continue;
    }
    if (arg.startsWith("--")) {
      flags.add(arg);
      continue;
    }
    targetPath = arg;
  }

  return {
    profile,
    configPath,
    targetPath,
    headroomOnly: flags.has("--headroom-only"),
    fullOnly: flags.has("--full"),
  };
}

async function main() {
  const cli = parseCliArgs(process.argv);
  await buildRepositoryContextBundle(cli);
}

const isDirectRun =
  process.argv[1] &&
  resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));

if (isDirectRun) {
  await main();
}

async function probeHeadroomProxy(baseUrl) {
  try {
    const response = await fetch(`${baseUrl}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(2500),
    });
    return response.ok;
  } catch {
    return false;
  }
}

function resolveHeadroomCompressionConfig() {
  const config = {
    compressUserMessages: process.env.HEADROOM_CONTEXT_COMPRESS_USER_MESSAGES !== "0",
    protectRecent: Number(process.env.HEADROOM_CONTEXT_PROTECT_RECENT || 0),
    targetRatio: Number(process.env.HEADROOM_CONTEXT_TARGET_RATIO || DEFAULT_HEADROOM_TARGET_RATIO),
    protectAnalysisContext: process.env.HEADROOM_CONTEXT_PROTECT_ANALYSIS_CONTEXT === "1",
  };

  if (process.env.HEADROOM_CONTEXT_FORCE_KOMPRESS === "1") {
    config.forceKompress = true;
  }
  if (process.env.HEADROOM_CONTEXT_MIN_TOKENS) {
    config.minTokensToCompress = Number(process.env.HEADROOM_CONTEXT_MIN_TOKENS);
  }
  return config;
}

function resolveHeadroomFallbackReason({
  proxyReachable,
  headroomResult,
  headroomContent,
  repositoryContextXml,
}) {
  if (!proxyReachable) return "proxy_unreachable";
  if (!headroomResult.compressed) return "headroom_not_compressed";
  if (Number(headroomResult.tokensSaved || 0) <= 0) return "no_positive_token_savings";
  if (headroomContent === repositoryContextXml) return "content_unchanged";
  return "unknown";
}

function wrapContextXml({
  compression,
  generator,
  systemDirective,
  contextXml,
  headroomResult,
  headroomBaseUrl,
  headroomActuallyCompressed,
  headroomFallbackReason,
}) {
  const metrics = [
    `compressed="${headroomActuallyCompressed ? "true" : "false"}"`,
    `tokens_before="${headroomResult.tokensBefore || 0}"`,
    `tokens_after="${headroomResult.tokensAfter || 0}"`,
    `tokens_saved="${headroomResult.tokensSaved || 0}"`,
    `compression_ratio="${headroomResult.compressionRatio || 1}"`,
    `fallback_used="${headroomActuallyCompressed ? "false" : "true"}"`,
    `fallback_reason="${escapeXml(headroomFallbackReason)}"`,
    `proxy="${escapeXml(headroomBaseUrl)}"`,
  ].join(" ");

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<source_context_bundle compression="${escapeXml(compression)}" generator="${escapeXml(generator)}">`,
    `  <system_directive>${escapeXml(systemDirective)}</system_directive>`,
    `  <headroom ${metrics} />`,
    '  <repository_context format="repomix-xml">',
    indentXml(contextXml, 4),
    "  </repository_context>",
    "</source_context_bundle>",
    "",
  ].join("\n");
}

function extractRepositoryContextXml(value) {
  const match = value.match(
    /<repository_context\b[^>]*>\s*([\s\S]*?)\s*<\/repository_context>/u,
  );
  return (match?.[1] || value).trim();
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function chunkText(value, chunkSize) {
  const safeChunkSize = Number.isFinite(chunkSize) && chunkSize > 0
    ? Math.floor(chunkSize)
    : DEFAULT_HEADROOM_CHUNK_CHARS;
  const chunks = [];
  for (let index = 0; index < value.length; index += safeChunkSize) {
    chunks.push(value.slice(index, index + safeChunkSize));
  }
  return chunks.length ? chunks : [""];
}

function joinHeadroomMessages(messages) {
  if (!Array.isArray(messages)) return "";
  return messages
    .map((message) => {
      const content = message?.content;
      if (typeof content === "string") return content;
      if (Array.isArray(content)) {
        return content
          .map((part) => {
            if (typeof part === "string") return part;
            if (typeof part?.text === "string") return part.text;
            if (typeof part?.content === "string") return part.content;
            return "";
          })
          .join("\n");
      }
      return "";
    })
    .join("\n");
}

function indentXml(value, spaces) {
  const prefix = " ".repeat(spaces);
  return value
    .split(/\r?\n/u)
    .map((line) => `${prefix}${line}`)
    .join("\n");
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
