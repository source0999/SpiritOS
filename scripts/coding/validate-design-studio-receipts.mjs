#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REQUIRED_FIELDS = [
  "increment_id",
  "plan_id",
  "phase_id",
  "started_at",
  "completed_at",
  "head_before",
  "head_after",
  "branch",
  "final_increment_verdict",
];

const ALLOWED_VERDICTS = new Set([
  "INCREMENT_GO_PROVEN",
  "INCREMENT_BLOCKED_ENV",
  "INCREMENT_BLOCKED_PERMISSION",
  "INCREMENT_BLOCKED_TEST_FAILURE",
  "INCREMENT_BLOCKED_SCOPE_CONFLICT",
  "INCREMENT_NO_GO_FAKE_PROOF",
]);

const BOOTSTRAP_EXEMPT_PATTERN = /increment-00-phase-0-00\.4-receipt-/;

export function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function parseReceiptFile(path) {
  const raw = readFileSync(path, "utf8");
  if (extname(path) === ".json") {
    return JSON.parse(raw);
  }

  const receipt = { __raw: raw };
  for (const line of raw.split(/\r?\n/)) {
    const match = line.match(/^([A-Za-z0-9_]+):\s*(.+?)\s*$/);
    if (!match) continue;
    receipt[match[1]] = match[2].replace(/^`|`$/g, "");
  }
  return receipt;
}

function resolveArtifactPath(baseDir, artifactPath) {
  return isAbsolute(artifactPath) ? artifactPath : resolve(baseDir, artifactPath);
}

export function validateReceiptObject(receipt, options = {}) {
  const baseDir = resolve(options.baseDir ?? process.cwd());
  const errors = [];

  for (const field of REQUIRED_FIELDS) {
    if (typeof receipt[field] !== "string" || receipt[field].trim() === "") {
      errors.push(`missing_required_field:${field}`);
    }
  }

  if (
    typeof receipt.final_increment_verdict === "string" &&
    !ALLOWED_VERDICTS.has(receipt.final_increment_verdict)
  ) {
    errors.push(`invalid_final_increment_verdict:${receipt.final_increment_verdict}`);
  }

  const artifactsByRole = new Map();
  for (const artifact of receipt.artifacts ?? []) {
    if (!artifact.role) errors.push("artifact_missing_role");
    if (!artifact.path) errors.push(`artifact_missing_path:${artifact.role ?? "unknown"}`);
    if (!artifact.sha256) errors.push(`artifact_missing_sha256:${artifact.role ?? "unknown"}`);
    if (!artifact.path || !artifact.sha256) continue;

    const absolutePath = resolveArtifactPath(baseDir, artifact.path);
    if (!existsSync(absolutePath)) {
      errors.push(`artifact_path_missing:${artifact.role}:${artifact.path}`);
      continue;
    }

    const actualHash = sha256File(absolutePath);
    if (actualHash !== artifact.sha256) {
      errors.push(`artifact_hash_mismatch:${artifact.role}:${artifact.path}`);
    }
    artifactsByRole.set(artifact.role, { ...artifact, absolutePath, actualHash });
  }

  for (const link of receipt.chain_links ?? []) {
    const target = artifactsByRole.get(link.to_role);
    if (!target) {
      errors.push(`chain_link_missing_target:${link.to_role}`);
      continue;
    }
    if (target.actualHash !== link.expected_hash) {
      errors.push(`chain_link_hash_mismatch:${link.from_role}->${link.to_role}`);
    }
    if (receipt.trace_id && target.trace_id && receipt.trace_id !== target.trace_id) {
      errors.push(`chain_link_trace_mismatch:${link.to_role}`);
    }
  }

  if (receipt.receipt_type === "screenshot") {
    if (!receipt.sandbox_apply_receipt_id) {
      errors.push("screenshot_missing_sandbox_apply_receipt_id");
    }
    if (!receipt.diff_hash) {
      errors.push("screenshot_missing_diff_hash");
    }
  }

  if (receipt.receipt_type === "critic") {
    const hashes = [receipt.desktop_screenshot_hash, receipt.mobile_screenshot_hash].filter(Boolean);
    if (hashes.length === 0) {
      errors.push("critic_missing_screenshot_hash");
    }
  }

  if (receipt.receipt_type === "writeback") {
    if (!receipt.approval_id_hash) {
      errors.push("writeback_missing_approval_id_hash");
    }
    if (receipt.acceptance_trace_id && receipt.trace_id !== receipt.acceptance_trace_id) {
      errors.push("writeback_trace_mismatch");
    }
  }

  return {
    errors,
    ok: errors.length === 0,
  };
}

export function validateReceiptFile(path, options = {}) {
  return validateReceiptObject(parseReceiptFile(path), {
    ...options,
    baseDir: options.baseDir ?? resolve(path, ".."),
  });
}

function listReceiptFiles(dir) {
  const found = [];
  if (!existsSync(dir)) return found;
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      found.push(...listReceiptFiles(path));
    } else if (/increment-.*-receipt-.*\.(md|json)$/.test(entry)) {
      found.push(path);
    }
  }
  return found.sort();
}

function receiptPlanNumber(path) {
  const match = path.match(/increment-(\d{2})-/);
  return match ? Number(match[1]) : Number.POSITIVE_INFINITY;
}

export function validatePivot({ pivot, throughPlan = "99" }) {
  const pivotRoot = resolve(pivot);
  const maxPlan = Number.parseInt(throughPlan, 10);
  const files = listReceiptFiles(pivotRoot).filter((file) => receiptPlanNumber(file) <= maxPlan);
  const results = [];
  const errors = [];

  for (const file of files) {
    const rel = relative(process.cwd(), file);
    if (BOOTSTRAP_EXEMPT_PATTERN.test(file)) {
      results.push({ file: rel, ok: true, skipped: "bootstrap_exempt_00.4" });
      continue;
    }
    const result = validateReceiptFile(file, { baseDir: process.cwd() });
    results.push({ file: rel, ...result });
    for (const error of result.errors) {
      errors.push(`${rel}:${error}`);
    }
  }

  return { errors, filesChecked: results.length, ok: errors.length === 0, results };
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--pivot") args.pivot = argv[++index];
    else if (arg === "--through-plan") args.throughPlan = argv[++index];
    else if (arg === "--receipt") args.receipt = argv[++index];
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  let result;
  if (args.receipt) {
    result = validateReceiptFile(resolve(args.receipt), { baseDir: process.cwd() });
  } else {
    if (!args.pivot) {
      throw new Error("Missing --pivot <path> or --receipt <path>");
    }
    result = validatePivot({ pivot: args.pivot, throughPlan: args.throughPlan ?? "99" });
  }

  if (!result.ok) {
    console.error(JSON.stringify(result, null, 2));
    process.exitCode = 1;
    return;
  }
  console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}
