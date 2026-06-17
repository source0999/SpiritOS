#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { compress } from "headroom-ai";

const repoRoot = resolve(import.meta.dirname, "..");
const innerOutput = resolve(repoRoot, "repomix-output.ast-inner.xml");
const finalOutput = resolve(repoRoot, "repomix-output.ast.xml");
const headroomOutput = resolve(repoRoot, "repomix-output.headroom.xml");

const repomixCli = resolve(repoRoot, "node_modules", "repomix", "bin", "repomix.cjs");
const headroomOnly = process.argv.includes("--headroom-only");

if (!headroomOnly) {
  execFileSync(
    process.execPath,
    [
      repomixCli,
      "--config",
      "repomix.config.json",
      "--compress",
      "--output",
      innerOutput,
      ".",
    ],
    {
      cwd: repoRoot,
      stdio: "inherit",
    },
  );
}

const repomixSource = headroomOnly ? finalOutput : innerOutput;

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

const headroomResult = await compress(
  [
    {
      role: "user",
      content: repositoryContextXml,
    },
  ],
  {
    model: process.env.HEADROOM_CONTEXT_MODEL || "gpt-4o",
    baseUrl: process.env.HEADROOM_BASE_URL || "http://localhost:8787",
    fallback: true,
    retries: 0,
    stack: "spiritos-repomix-context",
    tokenBudget: Number(process.env.HEADROOM_CONTEXT_TOKEN_BUDGET || 120000),
  },
);

const headroomContent = String(headroomResult.messages?.[0]?.content || repositoryContextXml);
const headroomActuallyCompressed = Boolean(headroomResult.compressed && headroomContent !== repositoryContextXml);

const wrappedXml = wrapContextXml({
  compression: headroomActuallyCompressed ? "tree-sitter+headroom" : "tree-sitter",
  generator: headroomActuallyCompressed ? "repomix,headroom-ai" : "repomix",
  systemDirective,
  contextXml: headroomActuallyCompressed ? headroomContent : repositoryContextXml,
  headroomResult,
});

writeFileSync(finalOutput, wrappedXml, "utf8");
writeFileSync(
  headroomOutput,
  wrapContextXml({
    compression: "tree-sitter+headroom",
    generator: "repomix,headroom-ai",
    systemDirective,
    contextXml: headroomContent,
    headroomResult,
  }),
  "utf8",
);
rmSync(innerOutput, { force: true });

console.log(`Compressed context written to ${finalOutput}`);
console.log(
  headroomActuallyCompressed
    ? `Headroom context written to ${headroomOutput} (${headroomResult.tokensSaved} tokens saved)`
    : `Headroom context written to ${headroomOutput} (proxy unavailable or no savings; fallback content used)`,
);

function wrapContextXml({ compression, generator, systemDirective, contextXml, headroomResult }) {
  const metrics = [
    `compressed="${headroomResult.compressed ? "true" : "false"}"`,
    `tokens_before="${headroomResult.tokensBefore || 0}"`,
    `tokens_after="${headroomResult.tokensAfter || 0}"`,
    `tokens_saved="${headroomResult.tokensSaved || 0}"`,
    `compression_ratio="${headroomResult.compressionRatio || 1}"`,
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

function indentXml(value, spaces) {
  const prefix = " ".repeat(spaces);
  return value
    .split(/\r?\n/u)
    .map((line) => `${prefix}${line}`)
    .join("\n");
}
