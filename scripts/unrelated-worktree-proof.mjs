import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { lstatSync, openSync, closeSync, readSync, readFileSync, readlinkSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const DEFAULT_UNRELATED_PROOF_EXCLUDES = Object.freeze([
  ".codex-worktrees/**",
  ".git/**",
  ".next/**",
  ".spirit-backups/**",
  ".codex-next-3000.log",
  "data/approved_actions.audit.jsonl",
  "data/blocked_actions.audit.jsonl",
  "data/long_running_tasks.sqlite3*",
  "data/source-proxy/**",
  "docs/evidence/e2e-loop/**",
  "docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/**",
  "playwright-report/**",
  "test-results/**",
  "tests/ui-agent-trials/fixtures/dummy-product-site/**",
  "tmp/e2e-loop/**",
]);

const FULL_HASH_LIMIT_BYTES = 1024 * 1024;
const SAMPLE_BYTES = 64 * 1024;

export function captureUnrelatedWorktreeSnapshot(
  repoRoot,
  { excludes = DEFAULT_UNRELATED_PROOF_EXCLUDES } = {},
) {
  const root = path.resolve(repoRoot);
  const pathspec = [".", ...excludes.map((item) => `:(exclude)${item}`)];
  const trackedDiff = runGitBuffer(root, [
    "diff",
    "--binary",
    "--no-ext-diff",
    "HEAD",
    "--",
    ...pathspec,
  ]);
  const untrackedOutput = runGitText(root, [
    "ls-files",
    "--others",
    "--exclude-standard",
    "--",
    ...pathspec,
  ]);
  const untrackedPaths = [...new Set(
    untrackedOutput.split(/\r?\n/u).map((item) => item.trim()).filter(Boolean),
  )].sort();
  const untrackedFiles = untrackedPaths.map((relativePath) =>
    fingerprintUntrackedPath(root, relativePath),
  );
  const payload = {
    schema_version: "unrelated-worktree-proof/v1",
    excluded_paths: [...excludes],
    tracked_diff_bytes: trackedDiff.length,
    tracked_diff_sha256: sha256(trackedDiff),
    untracked_file_count: untrackedFiles.length,
    untracked_files: untrackedFiles,
  };
  return {
    ...payload,
    snapshot_sha256: sha256(Buffer.from(stableJson(payload), "utf8")),
    captured_at_ms: Date.now(),
  };
}

export function compareUnrelatedWorktreeSnapshots(before, after) {
  const beforeFiles = new Map(
    (Array.isArray(before?.untracked_files) ? before.untracked_files : [])
      .map((item) => [item.path, item]),
  );
  const afterFiles = new Map(
    (Array.isArray(after?.untracked_files) ? after.untracked_files : [])
      .map((item) => [item.path, item]),
  );
  const changedPaths = [...new Set([...beforeFiles.keys(), ...afterFiles.keys()])]
    .filter((relativePath) => stableJson(beforeFiles.get(relativePath)) !== stableJson(afterFiles.get(relativePath)))
    .sort();
  const trackedDiffMatches = Boolean(
    before?.tracked_diff_sha256 && before.tracked_diff_sha256 === after?.tracked_diff_sha256,
  );
  const untrackedFilesMatch = changedPaths.length === 0;
  const snapshotMatches = Boolean(
    before?.snapshot_sha256 && before.snapshot_sha256 === after?.snapshot_sha256,
  );
  return {
    status: trackedDiffMatches && untrackedFilesMatch && snapshotMatches ? "GO" : "NO_GO",
    snapshot_matches: snapshotMatches,
    tracked_diff_matches: trackedDiffMatches,
    untracked_files_match: untrackedFilesMatch,
    before_snapshot_sha256: before?.snapshot_sha256 ?? "missing",
    after_snapshot_sha256: after?.snapshot_sha256 ?? "missing",
    before_tracked_diff_sha256: before?.tracked_diff_sha256 ?? "missing",
    after_tracked_diff_sha256: after?.tracked_diff_sha256 ?? "missing",
    before_untracked_file_count: before?.untracked_file_count ?? null,
    after_untracked_file_count: after?.untracked_file_count ?? null,
    changed_paths: changedPaths,
    compared_at_ms: Date.now(),
  };
}

export function unrelatedSnapshotSummary(snapshot) {
  return {
    schema_version: snapshot?.schema_version ?? "missing",
    snapshot_sha256: snapshot?.snapshot_sha256 ?? "missing",
    tracked_diff_bytes: snapshot?.tracked_diff_bytes ?? null,
    tracked_diff_sha256: snapshot?.tracked_diff_sha256 ?? "missing",
    untracked_file_count: snapshot?.untracked_file_count ?? null,
    captured_at_ms: snapshot?.captured_at_ms ?? null,
  };
}

function runGitBuffer(cwd, args) {
  const result = spawnSync("git", args, {
    cwd,
    encoding: null,
    maxBuffer: 256 * 1024 * 1024,
    windowsHide: true,
  });
  if (result.status !== 0) {
    throw new Error(
      `git ${args.join(" ")} failed (${result.status}): ${Buffer.from(result.stderr ?? "").toString("utf8")}`,
    );
  }
  return Buffer.isBuffer(result.stdout) ? result.stdout : Buffer.from(result.stdout ?? "");
}

function runGitText(cwd, args) {
  return runGitBuffer(cwd, args).toString("utf8");
}

function fingerprintUntrackedPath(root, relativePath) {
  const absolutePath = path.resolve(root, relativePath);
  const relativeFromRoot = path.relative(root, absolutePath);
  if (relativeFromRoot.startsWith("..") || path.isAbsolute(relativeFromRoot)) {
    throw new Error(`Untracked path escaped repo root: ${relativePath}`);
  }
  const stat = lstatSync(absolutePath, { bigint: true });
  const base = {
    path: relativePath.replace(/\\/gu, "/"),
    mode: Number(stat.mode),
    size_bytes: Number(stat.size),
    mtime_ns: stat.mtimeNs.toString(),
  };
  if (stat.isSymbolicLink()) {
    return { ...base, kind: "symlink", content_fingerprint: sha256(Buffer.from(readlinkSync(absolutePath))) };
  }
  if (!stat.isFile()) {
    return { ...base, kind: "other", content_fingerprint: "not_file" };
  }
  return {
    ...base,
    kind: "file",
    content_fingerprint: fileFingerprint(absolutePath, Number(stat.size)),
    fingerprint_mode: Number(stat.size) <= FULL_HASH_LIMIT_BYTES ? "full_sha256" : "sampled_sha256",
  };
}

function fileFingerprint(filePath, size) {
  if (size <= FULL_HASH_LIMIT_BYTES) return sha256(readFileSync(filePath));
  const descriptor = openSync(filePath, "r");
  try {
    const firstLength = Math.min(SAMPLE_BYTES, size);
    const lastLength = Math.min(SAMPLE_BYTES, Math.max(0, size - firstLength));
    const first = Buffer.alloc(firstLength);
    const last = Buffer.alloc(lastLength);
    readSync(descriptor, first, 0, firstLength, 0);
    if (lastLength > 0) readSync(descriptor, last, 0, lastLength, size - lastLength);
    return sha256(Buffer.concat([Buffer.from(String(size)), first, last]));
  } finally {
    closeSync(descriptor);
  }
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function stableJson(value) {
  return JSON.stringify(stableValue(value));
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map((item) => stableValue(item));
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, stableValue(value[key])]),
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const snapshot = captureUnrelatedWorktreeSnapshot(process.cwd());
  const output = process.argv.includes("--full") ? snapshot : unrelatedSnapshotSummary(snapshot);
  console.log(JSON.stringify(output, null, 2));
}
