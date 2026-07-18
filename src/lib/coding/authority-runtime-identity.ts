import "server-only";

import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { realpath } from "node:fs/promises";
import { basename, dirname, isAbsolute, resolve } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export class AuthorityRuntimeIdentityError extends Error {
  constructor(public readonly reasonCode: string) {
    super(reasonCode);
    this.name = "AuthorityRuntimeIdentityError";
  }
}

export type AuthorityRuntimeIdentity = {
  repository: string;
  root: string;
  worktree: string;
  branch: string;
  sourceHead: string;
  commonGitDir: string;
  stateNamespace: string;
};

export async function resolveAuthorityRuntimeIdentity(
  configuredRoot = process.env.SPIRITOS_APPROVAL_ROOT?.trim() || process.cwd(),
): Promise<AuthorityRuntimeIdentity> {
  if (!isAbsolute(configuredRoot)) {
    throw new AuthorityRuntimeIdentityError("approval_root_not_absolute");
  }
  const absolute = resolve(configuredRoot);
  let canonicalRoot: string;
  try {
    canonicalRoot = await realpath(absolute);
  } catch {
    throw new AuthorityRuntimeIdentityError("approval_root_unavailable");
  }
  if (canonicalRoot !== absolute) {
    throw new AuthorityRuntimeIdentityError("approval_root_symlink_forbidden");
  }

  const topLevel = await git(canonicalRoot, "rev-parse", "--show-toplevel");
  let canonicalTop: string;
  try {
    canonicalTop = await realpath(topLevel);
  } catch {
    throw new AuthorityRuntimeIdentityError("approval_git_identity_unavailable");
  }
  if (canonicalTop !== canonicalRoot) {
    throw new AuthorityRuntimeIdentityError("approval_root_not_worktree_top_level");
  }

  const worktreeList = await git(canonicalRoot, "worktree", "list", "--porcelain");
  const registered = new Set(
    await Promise.all(
      worktreeList
        .split("\n")
        .filter((line) => line.startsWith("worktree "))
        .map(async (line) => realpath(line.slice("worktree ".length).trim())),
    ),
  );
  if (!registered.has(canonicalRoot)) {
    throw new AuthorityRuntimeIdentityError("approval_root_unregistered");
  }

  const sourceHead = await git(canonicalRoot, "rev-parse", "--verify", "HEAD");
  if (!/^[0-9a-f]{40}$/i.test(sourceHead)) {
    throw new AuthorityRuntimeIdentityError("approval_source_head_invalid");
  }
  const branch = await git(canonicalRoot, "symbolic-ref", "--quiet", "--short", "HEAD");
  if (!branch) {
    throw new AuthorityRuntimeIdentityError("approval_detached_worktree_forbidden");
  }

  const commonRaw = await git(canonicalRoot, "rev-parse", "--git-common-dir");
  const commonGitDir = await realpath(isAbsolute(commonRaw) ? commonRaw : resolve(canonicalRoot, commonRaw));
  const repository = process.env.SPIRITOS_APPROVAL_REPOSITORY?.trim() || basename(dirname(commonGitDir));
  if (!repository) {
    throw new AuthorityRuntimeIdentityError("approval_repository_identity_missing");
  }
  const stateNamespace = createHash("sha256")
    .update(`${commonGitDir}\0${canonicalRoot}`, "utf8")
    .digest("hex")
    .slice(0, 24);
  return {
    repository,
    root: canonicalRoot,
    worktree: canonicalRoot,
    branch,
    sourceHead,
    commonGitDir,
    stateNamespace,
  };
}

async function git(root: string, ...args: string[]): Promise<string> {
  try {
    const { stdout } = await execFileAsync("git", ["-C", root, ...args], {
      encoding: "utf8",
      windowsHide: true,
    });
    return stdout.trim();
  } catch {
    throw new AuthorityRuntimeIdentityError("approval_git_identity_unavailable");
  }
}
