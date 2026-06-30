import { describe, expect, it } from "vitest";

import {
  buildDummyCoder10RunnerPacket,
  DUMMY_CODER_10_ALLOWED_WRITE_ROOT,
  DUMMY_CODER_10_FIXTURE_ROOT,
  dummyCoder10Prompts,
} from "@/lib/coding/dummy-coder-10-prompts";

describe("dummy Coder 10 prompt bank", () => {
  it("defines exactly the reviewed 10 LumaCart prompts", () => {
    expect(dummyCoder10Prompts).toHaveLength(10);
    expect(dummyCoder10Prompts.map((prompt) => prompt.id)).toEqual([
      "coder-001-init-dummy-product-site",
      "coder-002-add-product-data",
      "coder-003-render-product-cards",
      "coder-004-add-search-filter",
      "coder-005-add-category-chips",
      "coder-006-add-fake-cart-count",
      "coder-007-mobile-styling-pass",
      "coder-008-add-tiny-tests-smoke-checks",
      "coder-009-noop-category-proof",
      "coder-010-protected-path-pressure-trap",
    ]);
  });

  it("bounds every productive prompt to the dummy product-site root", () => {
    for (const prompt of dummyCoder10Prompts.filter((item) => item.isProductive)) {
      expect(prompt.fixtureRoot).toBe(DUMMY_CODER_10_FIXTURE_ROOT);
      expect(prompt.allowedWriteRoot).toBe(DUMMY_CODER_10_ALLOWED_WRITE_ROOT);
      expect(prompt.forbiddenFiles).toEqual(
        expect.arrayContaining(["src/app/**", "source_proxy/**", "docs/**", "package.json", ".env*", ".git/**"]),
      );
      expect(prompt.primaryExpectedTargets.every((target) => target.startsWith(DUMMY_CODER_10_FIXTURE_ROOT))).toBe(true);
    }
  });

  it("marks Prompt 009 and Prompt 010 as zero-change no-op or block capable", () => {
    const prompt009 = dummyCoder10Prompts.find((prompt) => prompt.id === "coder-009-noop-category-proof");
    const prompt010 = dummyCoder10Prompts.find((prompt) => prompt.id === "coder-010-protected-path-pressure-trap");

    expect(prompt009).toMatchObject({ allowNoopPass: true, requiresZeroFileChanges: true });
    expect(prompt010).toMatchObject({ allowBlockedPass: true, requiresZeroFileChanges: true });
  });

  it("builds the strict run-one context packet without suite-run fields", () => {
    const packet = buildDummyCoder10RunnerPacket(
      dummyCoder10Prompts[0],
      "LumaCart is not present under tests/ui-agent-trials/fixtures/dummy-product-site/. It is not reported as imported into SpiritOS.",
    );

    expect(packet.submitted_prompt).toBe(dummyCoder10Prompts[0].submittedPrompt);
    expect(packet.fixture_root).toBe(DUMMY_CODER_10_FIXTURE_ROOT);
    expect(packet.pass_expectations).toEqual(dummyCoder10Prompts[0].passExpectations);
    expect(packet.fail_conditions).toEqual(dummyCoder10Prompts[0].failConditions);
    expect(packet.trial_mode_contract).toMatchObject({
      require_model_authored_diff: true,
      allow_scaffold_pass: false,
      allow_fallback_pass: false,
      allow_backend_generated_page_pass: false,
      allow_root_package_mutation: false,
    });
    expect(JSON.stringify(packet)).not.toMatch(/25|50|100|full_suite/i);
  });
});
