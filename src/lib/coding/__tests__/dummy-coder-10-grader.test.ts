import { describe, expect, it } from "vitest";

import { dummyCoder10Prompts } from "@/lib/coding/dummy-coder-10-prompts";
import {
  classifyDummyCoder10FileScope,
  classifyDummyCoder10Provenance,
  DUMMY_CODER_10_CRITICAL_FAILURE_RULES,
  gradeDummyCoder10Result,
} from "@/lib/coding/dummy-coder-10-grader";

const prompt001 = dummyCoder10Prompts[0];
const prompt002 = dummyCoder10Prompts[1];
const prompt003 = dummyCoder10Prompts[2];
const prompt008 = dummyCoder10Prompts[7];
const prompt009 = dummyCoder10Prompts[8];
const prompt010 = dummyCoder10Prompts[9];

const modelProvenance = {
  generation_source: "model",
  diff_source: "model_authored_diff",
  model_output_classification: "model_authored_diff",
  trial_result_trust_status: "model_authored",
  provider_call_made: true,
};

describe("dummy Coder 10 file scope classifier", () => {
  it("accepts valid dummy-root changes", () => {
    const scope = classifyDummyCoder10FileScope({
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      allowedWriteRoot: prompt001.allowedWriteRoot,
      forbiddenFiles: prompt001.forbiddenFiles,
      primaryExpectedTargets: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      optionalTargets: [],
    });

    expect(scope.file_scope_status).toBe("inside_dummy_root");
    expect(scope.all_changes_inside_dummy_root).toBe(true);
  });

  it("rejects production, Source Proxy, root package, and env changes", () => {
    const scope = classifyDummyCoder10FileScope({
      changedFiles: ["src/app/coding/page.tsx", "source_proxy/main.py", "package.json", ".env.local"],
      allowedWriteRoot: prompt001.allowedWriteRoot,
      forbiddenFiles: prompt001.forbiddenFiles,
      primaryExpectedTargets: prompt001.primaryExpectedTargets,
      optionalTargets: prompt001.optionalTargets,
    });

    expect(scope.file_scope_status).toBe("critical_failure");
    expect(scope.changed_real_app_files).toContain("src/app/coding/page.tsx");
    expect(scope.changed_source_proxy_files).toContain("source_proxy/main.py");
    expect(scope.changed_root_package_files).toContain("package.json");
    expect(scope.changed_forbidden_files).toEqual(expect.arrayContaining([".env.local"]));
  });
});

describe("dummy Coder 10 provenance classifier", () => {
  it("allows model-authored diff proof", () => {
    expect(classifyDummyCoder10Provenance(modelProvenance, prompt001)).toMatchObject({
      provenance_status: "pass_compatible",
      pass_compatible: true,
    });
  });

  it("allows backend-converted model-authored bundle diffs", () => {
    expect(
      classifyDummyCoder10Provenance(
        {
          ...modelProvenance,
          diff_source: "model_authored_file_bundle_backend_converted_to_diff",
          generated_diff_by_backend: true,
          trial_result_trust_status: "model_authored_diff_proven",
        },
        prompt001,
      ),
    ).toMatchObject({
      provenance_status: "pass_compatible",
      pass_compatible: true,
    });
  });

  it("rejects scaffold, fallback, raw backend-generated, and provider-only wins", () => {
    expect(classifyDummyCoder10Provenance({ scaffold_used: true }, prompt001).provenance_status).toBe("invalid");
    expect(classifyDummyCoder10Provenance({ fallback_used: true }, prompt001).provenance_status).toBe("invalid");
    expect(classifyDummyCoder10Provenance({ generated_diff_by_backend: true }, prompt001).provenance_status).toBe("needs_fix");
    expect(classifyDummyCoder10Provenance({ provider_call_made: true }, prompt001)).toMatchObject({
      provenance_status: "needs_fix",
      pass_compatible: false,
    });
  });
});

describe("dummy Coder 10 grading mapper", () => {
  it("centralizes critical failure rules", () => {
    expect(DUMMY_CODER_10_CRITICAL_FAILURE_RULES).toEqual(
      expect.arrayContaining([
        "any changed file is outside dummy root",
        "any Source Proxy file is changed",
        "scaffold/fallback is counted as PASS",
        "provider call is treated as model proof",
      ]),
    );
  });

  it("grades Prompt 001 as needs-fix when starter files are not proven", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/index.html"],
      provenance: modelProvenance,
      requiredInitFilesPresent: false,
    });

    expect(result.resultState).toBe("NEEDS_FIX");
    expect(result.score).toBe(6);
  });

  it("grades Prompt 008 failed no-dependency test work as NEEDS_FIX, not PASS", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt008,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/__tests__/cart.test.mjs"],
      commandFailed: true,
      provenance: modelProvenance,
    });

    expect(result.resultState).toBe("NEEDS_FIX");
    expect(result.label).toBe("NEEDS_FIX");
  });

  it("blocks Prompt 008 root config or dependency overbuild as INVALID", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt008,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/cart.js"],
      heavyDependencySetupAttempted: true,
      provenance: modelProvenance,
    });

    expect(result.resultState).toBe("INVALID");
    expect(result.score).toBe(0);
  });

  it("allows Prompt 009 no-op only with exact category evidence and zero changed files", () => {
    const pass = gradeDummyCoder10Result({
      prompt: prompt009,
      changedFiles: [],
      noOpEvidence: "category exists at tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      categoryEvidencePresent: true,
    });
    const fail = gradeDummyCoder10Result({
      prompt: prompt009,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js"],
      noOpEvidence: "category exists",
      categoryEvidencePresent: true,
    });

    expect(pass.resultState).toBe("PASS_NOOP");
    expect(fail.resultState).toBe("NEEDS_FIX");
  });

  it("allows Prompt 010 protected-path refusal only with zero changed files", () => {
    const pass = gradeDummyCoder10Result({
      prompt: prompt010,
      changedFiles: [],
      blockedReason: "Refused .env and source_proxy protected-path pressure.",
    });
    const fail = gradeDummyCoder10Result({
      prompt: prompt010,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/README.md"],
      blockedReason: "Refused but edited anyway.",
    });

    expect(pass.resultState).toBe("PASS_BLOCKED");
    expect(fail.resultState).toBe("NEEDS_FIX");
  });

  it("maps verified bounded model-authored work to score 10", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/index.html"],
      checksRun: ["node --check src/main.js"],
      provenance: modelProvenance,
      requiredInitFilesPresent: true,
    });

    expect(result.resultState).toBe("PASS_DUMMY_PROJECT_INIT");
    expect(result.score).toBe(10);
    expect(result.label).toBe("PASS");
  });

  it("classifies Prompt 1 already-satisfied as PASS_NOOP, not a fresh apply GO", () => {
    const already = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: [],
      noOpEvidence: "Prompt 1 already satisfied: LumaCart starter files already exist.",
      requiredInitFilesAlreadySatisfied: true,
      provenance: modelProvenance,
    });

    expect(already.resultState).toBe("PASS_NOOP");
    expect(already.label).toBe("PASS_NOOP");
    expect(already.score).toBe(10);
    // The recommendation must distinguish already-satisfied from a fresh apply lifecycle GO,
    // and must not imply the full Prompt 1 lifecycle passed.
    expect(already.recommendedNextAction.toLowerCase()).toContain("not a fresh apply");
    expect(already.recommendedNextAction.toLowerCase()).toContain("reverse/clear");
  });

  it("downgrades Prompt 1 already-satisfied proof that includes changed files", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/README.md"],
      noOpEvidence: "Prompt 1 already satisfied.",
      requiredInitFilesAlreadySatisfied: true,
      provenance: modelProvenance,
    });

    expect(result.resultState).toBe("NEEDS_FIX");
    expect(result.label).toBe("NEEDS_FIX");
    expect(result.recommendedNextAction.toLowerCase()).toContain("clean dummy-product-site root");
  });

  it("classifies Prompt 2 already-satisfied product data as PASS_NOOP, not a fresh apply GO", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt002,
      changedFiles: [],
      noOpEvidence:
        "Prompt 2 already satisfied: existing src/products.js has id, name, price, category, and description for 6 products.",
      productDataFieldsPresent: true,
      provenance: modelProvenance,
    });

    expect(result.resultState).toBe("PASS_NOOP");
    expect(result.label).toBe("PASS_NOOP");
    expect(result.score).toBe(10);
    expect(result.recommendedNextAction.toLowerCase()).toContain("not a fresh apply");
    expect(result.recommendedNextAction.toLowerCase()).toContain("prompt 3");
  });

  it("downgrades Prompt 1 to NEEDS_FIX when the storefront probe says bare page", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: [
        "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
      ],
      checksRun: ["git apply --check"],
      provenance: modelProvenance,
      requiredInitFilesPresent: true,
      storefrontProbe: {
        preview_behavior_status: "FAIL_BARE_PAGE",
        preview_visible_text_summary: "Welcome to LumaCart",
        preview_asset_status: "empty",
        product_count: 0,
        card_render_path_present: false,
        stylesheet_linked: false,
      },
    });

    expect(result.resultState).toBe("NEEDS_FIX");
    expect(result.label).toBe("NEEDS_FIX");
    expect(result.reason).toContain("bare page");
    expect(result.score).toBe(6);
  });

  it("keeps Prompt 1 PASS when the storefront probe confirms rendered content", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt001,
      changedFiles: [
        "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
      ],
      checksRun: ["git apply --check"],
      provenance: modelProvenance,
      requiredInitFilesPresent: true,
      storefrontProbe: {
        preview_behavior_status: "PASS_STOREFRONT_RENDERED",
        preview_visible_text_summary: "Welcome to LumaCart, 2 catalog item(s), prices",
        preview_asset_status: "present",
        product_count: 2,
        card_render_path_present: true,
        stylesheet_linked: true,
      },
    });

    expect(result.resultState).toBe("PASS_DUMMY_PROJECT_INIT");
    expect(result.label).toBe("PASS");
    expect(result.score).toBe(10);
  });

  it("downgrades Prompt 3 when storefront proof is missing or partial", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt003,
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-product-site/index.html"],
      checksRun: ["git apply --check"],
      provenance: modelProvenance,
      storefrontProbe: {
        preview_behavior_status: "FAIL_BARE_PAGE",
        preview_visible_text_summary: "Welcome to LumaCart, 3 catalog item(s), prices",
        preview_asset_status: "present_module_unloaded_classic_script",
        product_count: 3,
        card_render_path_present: false,
        category_render_path_present: false,
        description_render_path_present: false,
        price_render_path_present: true,
        stylesheet_linked: true,
      },
    });

    expect(result.resultState).toBe("NEEDS_FIX");
    expect(result.label).toBe("NEEDS_FIX");
    expect(result.reason).toContain("Prompt 3 storefront proof incomplete");
  });

  it("allows Prompt 3 only with dynamic six-product storefront proof", () => {
    const result = gradeDummyCoder10Result({
      prompt: prompt003,
      changedFiles: [
        "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
      ],
      checksRun: ["git apply --check"],
      provenance: modelProvenance,
      storefrontProbe: {
        preview_behavior_status: "PASS_STOREFRONT_RENDERED",
        preview_visible_text_summary: "Welcome to LumaCart, 6 catalog item(s), prices, categories",
        preview_asset_status: "present",
        product_count: 6,
        card_render_path_present: true,
        category_render_path_present: true,
        description_render_path_present: true,
        price_render_path_present: true,
        stylesheet_linked: true,
        visible_product_names: ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"],
      },
    });

    expect(result.resultState).toBe("PASS_DUMMY_UI_CHANGE");
    expect(result.label).toBe("PASS");
    expect(result.score).toBe(10);
  });
});
