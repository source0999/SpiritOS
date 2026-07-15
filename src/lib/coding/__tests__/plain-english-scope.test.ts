import { describe, expect, it } from "vitest";
import { derivePlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";

describe("derivePlainEnglishScopeDraft", () => {
  it("turns a natural single-file Britton-style prompt into a bounded TaskSpec draft", () => {
    const draft = derivePlainEnglishScopeDraft(
      [
        "PIVOT. Please just inspect tests/ui-agent-trials/fixtures/dummy-coding-targets/readme-trial.md and propose the safe wording change.",
        "Do not apply, commit, push, call providers, or make permanent changes.",
        "Manual checks: git diff --check; npx --no-install tsc --noEmit --pretty false",
      ].join("\n"),
    );

    expect(draft.status).toBe("ready");
    expect(draft.targetFiles).toEqual([
      "tests/ui-agent-trials/fixtures/dummy-coding-targets/readme-trial.md",
    ]);
    expect(draft.allowedFiles).toEqual([
      "tests/ui-agent-trials/fixtures/dummy-coding-targets/readme-trial.md",
    ]);
    expect(draft.expectedChecks).toEqual(
      expect.arrayContaining(["git diff --check", "npx --no-install tsc --noEmit --pretty false"]),
    );
    expect(draft.restrictions).toMatchObject({
      apply: true,
      commit: true,
      permanentChanges: true,
      providerCalls: true,
      push: true,
    });
  });

  it("does not treat forbidden protected paths as target attempts", () => {
    const draft = derivePlainEnglishScopeDraft(
      [
        "Work on tests/ui-agent-trials/fixtures/dummy-coding-targets/no-diff-trial.json only.",
        "Forbidden: .env, .env.local, certificates/*, package-lock.json",
        "Do not inspect secrets.",
      ].join("\n"),
    );

    expect(draft.status).toBe("ready");
    expect(draft.reasonCodes).not.toContain("protected_path");
    expect(draft.forbiddenFiles).toEqual(
      expect.arrayContaining([".env", ".env.local", "certificates/*", "package-lock.json"]),
    );
  });

  it("fails closed with candidate scope guidance instead of requiring perfect schema", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Work in PIVOT but do not make permanent changes. I want the coding agent to inspect the current /coding command center UX and tell me what is blocked.",
    );

    expect(draft.status).toBe("blocked");
    expect(draft.reasonCodes).toContain("target_unresolved");
    expect(draft.clarificationPrompt).toContain("I need one target file or allowed-file scope before preview.");
    expect(draft.candidateFiles).toEqual(
      expect.arrayContaining([
        "labs/coding/CodingCommandCenterShell.tsx",
        "src/lib/coding/plain-english-scope.ts",
      ]),
    );
  });
});
