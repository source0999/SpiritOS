import { describe, expect, it } from "vitest";

import {
  AuthorityRuntimeIdentityError,
  resolveAuthorityRuntimeIdentity,
} from "@/lib/coding/authority-runtime-identity";

describe("authority runtime identity", () => {
  it("resolves the current registered worktree without campaign-specific paths", async () => {
    const identity = await resolveAuthorityRuntimeIdentity(process.cwd());
    expect(identity.root).toBe(process.cwd());
    expect(identity.worktree).toBe(process.cwd());
    expect(identity.sourceHead).toMatch(/^[0-9a-f]{40}$/);
    expect(identity.branch).toBe("codex/spiritos-foundation-remediation-r1-20260717");
    expect(identity.commonGitDir).toMatch(/\/SpiritOS\/\.git$/);
    expect(identity.stateNamespace).toMatch(/^[0-9a-f]{24}$/);
  });

  it("rejects a subdirectory rather than silently promoting it to repository root", async () => {
    await expect(resolveAuthorityRuntimeIdentity(`${process.cwd()}/src`)).rejects.toMatchObject({
      reasonCode: "approval_root_not_worktree_top_level",
    } satisfies Partial<AuthorityRuntimeIdentityError>);
  });

  it("rejects relative configured roots", async () => {
    await expect(resolveAuthorityRuntimeIdentity(".")).rejects.toMatchObject({
      reasonCode: "approval_root_not_absolute",
    } satisfies Partial<AuthorityRuntimeIdentityError>);
  });
});
