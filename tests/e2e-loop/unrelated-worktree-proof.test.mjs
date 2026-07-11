import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  captureUnrelatedWorktreeSnapshot,
  compareUnrelatedWorktreeSnapshots,
} from "../../scripts/unrelated-worktree-proof.mjs";

test("fixture-only lifecycle changes preserve the unrelated worktree snapshot", () => {
  withRepo((root) => {
    writeFileSync(path.join(root, "tracked.txt"), "user dirty tracked work\n", "utf8");
    writeFileSync(path.join(root, "untracked.txt"), "user untracked work\n", "utf8");
    const fixture = path.join(root, "tests/ui-agent-trials/fixtures/dummy-product-site/index.html");
    mkdirSync(path.dirname(fixture), { recursive: true });
    writeFileSync(fixture, "before\n", "utf8");
    const before = captureUnrelatedWorktreeSnapshot(root);

    writeFileSync(fixture, "after\n", "utf8");
    const after = captureUnrelatedWorktreeSnapshot(root);
    const comparison = compareUnrelatedWorktreeSnapshots(before, after);

    assert.equal(comparison.status, "GO");
    assert.equal(comparison.snapshot_matches, true);
    assert.deepEqual(comparison.changed_paths, []);
  });
});

test("tracked or untracked unrelated drift fails closed with exact paths", () => {
  withRepo((root) => {
    writeFileSync(path.join(root, "tracked.txt"), "initial dirty state\n", "utf8");
    writeFileSync(path.join(root, "untracked.txt"), "initial untracked state\n", "utf8");
    const before = captureUnrelatedWorktreeSnapshot(root);

    writeFileSync(path.join(root, "tracked.txt"), "changed by lifecycle\n", "utf8");
    writeFileSync(path.join(root, "untracked.txt"), "changed untracked state\n", "utf8");
    const after = captureUnrelatedWorktreeSnapshot(root);
    const comparison = compareUnrelatedWorktreeSnapshots(before, after);

    assert.equal(comparison.status, "NO_GO");
    assert.equal(comparison.tracked_diff_matches, false);
    assert.equal(comparison.untracked_files_match, false);
    assert.deepEqual(comparison.changed_paths, ["untracked.txt"]);
  });
});

function withRepo(callback) {
  const root = mkdtempSync(path.join(tmpdir(), "unrelated-worktree-proof-"));
  try {
    runGit(root, ["init", "-q"]);
    writeFileSync(path.join(root, "tracked.txt"), "committed\n", "utf8");
    runGit(root, ["add", "tracked.txt"]);
    runGit(root, [
      "-c",
      "user.name=Codex Test",
      "-c",
      "user.email=codex-test@example.invalid",
      "commit",
      "-qm",
      "baseline",
    ]);
    callback(root);
  } finally {
    rmSync(root, { force: true, recursive: true });
  }
}

function runGit(cwd, args) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8", windowsHide: true });
  assert.equal(result.status, 0, result.stderr || result.stdout);
}
