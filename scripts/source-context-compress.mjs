#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const repoRoot = resolve(import.meta.dirname, "..");
const innerOutput = resolve(repoRoot, "repomix-output.ast-inner.xml");
const finalOutput = resolve(repoRoot, "repomix-output.ast.xml");

const repomixCli = resolve(repoRoot, "node_modules", "repomix", "bin", "repomix.cjs");

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

const compressedRepomixXml = readFileSync(innerOutput, "utf8")
  .replace(/^\uFEFF/, "")
  .replace(/^<\?xml[^>]*>\s*/u, "")
  .trim();

const systemDirective = [
  "This is a compressed repository context generated for Source proxy planning.",
  "The repository_context payload was produced by Repomix Tree-sitter compression.",
  "Use file paths and structural signatures as read-only context.",
  "When implementation detail is absent, request or inspect the original file before editing.",
].join(" ");

const wrappedXml = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  '<source_context_bundle compression="tree-sitter" generator="repomix">',
  `  <system_directive>${escapeXml(systemDirective)}</system_directive>`,
  '  <repository_context format="repomix-xml">',
  indentXml(compressedRepomixXml, 4),
  "  </repository_context>",
  "</source_context_bundle>",
  "",
].join("\n");

writeFileSync(finalOutput, wrappedXml, "utf8");
rmSync(innerOutput, { force: true });

console.log(`Compressed context written to ${finalOutput}`);

function escapeXml(value) {
  return value
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
