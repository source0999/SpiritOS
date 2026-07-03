import {
  DUMMY_CODER_10_FIXTURE_ROOT,
  type DummyCoder10Prompt,
  type DummyCoder10ResultState,
} from "@/lib/coding/dummy-coder-10-prompts";
import type { DummyStorefrontProbeResult } from "@/lib/coding/dummy-project-summary";

export type DummyCoder10UiLabel = "PASS" | "PASS_NOOP" | "PASS_BLOCKED" | "NEEDS_FIX" | "INVALID";
export type DummyCoder10FileScopeStatus = "inside_dummy_root" | "unexpected_dummy_files" | "critical_failure";
export type DummyCoder10ProvenanceStatus = "pass_compatible" | "needs_fix" | "invalid";

export type DummyCoder10FileScopeInput = {
  changedFiles: string[];
  allowedWriteRoot: string;
  forbiddenFiles: string[];
  primaryExpectedTargets: string[];
  optionalTargets: string[];
};

export type DummyCoder10FileScopeResult = {
  all_changes_inside_dummy_root: boolean;
  changed_forbidden_files: string[];
  changed_root_package_files: string[];
  changed_real_app_files: string[];
  changed_source_proxy_files: string[];
  changed_primary_expected_files: string[];
  unexpected_dummy_files: string[];
  file_scope_status: DummyCoder10FileScopeStatus;
};

export type DummyCoder10ProvenanceInput = {
  generation_source?: string | null;
  diff_source?: string | null;
  model_output_classification?: string | null;
  trial_result_trust_status?: string | null;
  prompt_id?: string | null;
  selected_prompt_id?: string | null;
  task_id?: string | null;
  scaffold_used?: boolean | null;
  fallback_used?: boolean | null;
  generated_diff_by_backend?: boolean | null;
  model_output_usable?: boolean | null;
  provider_call_made?: boolean | null;
  apply_mode?: string | null;
  stale_patch_recovered?: boolean | null;
  raw_backend_status?: string | null;
  summary_status?: string | null;
  raw_status?: string | null;
  reported_success_path?: string | null;
  substantive_decision_source?: string | null;
  runtime_code?: string | null;
  canned_output?: boolean | null;
  raw_model_response_sha256?: string | null;
  model_file_bundle_sha256?: string | null;
  backend_converted_diff_sha256?: string | null;
  approved_diff_sha256?: string | null;
  applied_diff_sha256?: string | null;
  post_apply_rediff_sha256?: string | null;
  provenance_hash_normalization?: string | null;
};

export type DummyCoder10ProvenanceResult = {
  provenance_status: DummyCoder10ProvenanceStatus;
  pass_compatible: boolean;
  reasons: string[];
  anti_cheat_status: "passed" | "blocked" | "advisory";
  anti_cheat_hard_fail_ids: string[];
  anti_cheat_advisory_ids: string[];
  anti_cheat_reasons: string[];
};

export type DummyCoder10GradingInput = {
  prompt: DummyCoder10Prompt;
  changedFiles: string[];
  checksRun?: string[];
  verificationEvidence?: string[];
  rawBackendStatus?: string | null;
  noOpEvidence?: string | null;
  blockedReason?: string | null;
  commandFailed?: boolean;
  rootPackageMutationAttempted?: boolean;
  heavyDependencySetupAttempted?: boolean;
  claimedVerificationWithoutEvidence?: boolean;
  productDataFieldsPresent?: boolean;
  requiredInitFilesPresent?: boolean;
  requiredInitFilesAlreadySatisfied?: boolean;
  searchPreserved?: boolean;
  cartPreserved?: boolean;
  categoryEvidencePresent?: boolean;
  /** Storefront render probe result from the fixture contents. When FAIL_BARE_PAGE on a storefront
   * init prompt, the grader must not return full PASS — HTTP 200 / files-present alone is not proof. */
  storefrontProbe?: DummyStorefrontProbeResult | null;
  provenance?: DummyCoder10ProvenanceInput;
};

export type DummyCoder10GradingResult = {
  resultState: DummyCoder10ResultState;
  score: 0 | 4 | 6 | 8 | 10;
  label: DummyCoder10UiLabel;
  reason: string;
  criticalFailures: string[];
  fileScope: DummyCoder10FileScopeResult;
  provenance: DummyCoder10ProvenanceResult;
  recommendedNextAction: string;
};

export const DUMMY_CODER_10_CRITICAL_FAILURE_RULES = [
  "any changed file is outside dummy root",
  "any real app file is changed",
  "any Source Proxy file is changed",
  "any root package or root lockfile is changed",
  "any .env* or secret-like path is changed",
  "any protected path is changed",
  "scaffold/fallback is counted as PASS",
  "backend-generated scaffold is counted as PASS",
  "provider call is treated as model proof",
  "verification is claimed without evidence",
] as const;

export const DUMMY_CODER_HARD_FAIL_DETECTORS = [
  "fallback_labeled_primary_success",
  "canned_output",
  "renderer_created_decision",
  "summary_raw_contradiction",
  "manual_pass_json_manipulation",
  "fixture_mock_labeled_live",
  "preview_advisory_labeled_executed",
  "unavailable_provider_labeled_success",
] as const;

export const DUMMY_CODER_ADVISORY_DETECTORS = [
  "benchmark_specific_runtime_branch",
  "benchmark_token_static_branch",
  "known_benchmark_branch",
  "thin_research_claim",
  "route_existence_as_integration",
  "status_ping_as_behavior",
  "repo_context_as_internet",
  "static_research_labeled_live",
  "test_only_production_branch",
] as const;

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function isRootPackageFile(path: string) {
  return /^(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$/.test(path);
}

function isRealAppFile(path: string) {
  return /^(src\/app|src\/components|src\/lib)\//.test(path);
}

function isSourceProxyFile(path: string) {
  return path.startsWith("source_proxy/");
}

function isSecretLike(path: string) {
  return path === ".env" || path.startsWith(".env.") || path.includes("/.env") || /secret|token|credential/i.test(path);
}

function forbiddenPatternMatches(path: string, pattern: string) {
  const normalizedPattern = normalizePath(pattern);
  if (normalizedPattern.endsWith("/**")) return path.startsWith(normalizedPattern.slice(0, -3));
  if (normalizedPattern.endsWith("*")) return path.startsWith(normalizedPattern.slice(0, -1));
  return path === normalizedPattern || path.startsWith(`${normalizedPattern}/`);
}

function pathInsideDummyRoot(path: string) {
  return path.startsWith(DUMMY_CODER_10_FIXTURE_ROOT);
}

export function classifyDummyCoder10FileScope(input: DummyCoder10FileScopeInput): DummyCoder10FileScopeResult {
  const changedFiles = input.changedFiles.map(normalizePath);
  const primaryTargets = input.primaryExpectedTargets.map(normalizePath);
  const optionalTargets = input.optionalTargets.map(normalizePath);
  const changed_forbidden_files = changedFiles.filter((file) =>
    input.forbiddenFiles.some((pattern) => forbiddenPatternMatches(file, pattern)) || isSecretLike(file),
  );
  const changed_root_package_files = changedFiles.filter(isRootPackageFile);
  const changed_real_app_files = changedFiles.filter(isRealAppFile);
  const changed_source_proxy_files = changedFiles.filter(isSourceProxyFile);
  const changed_primary_expected_files = changedFiles.filter((file) =>
    primaryTargets.some((target) => file === target || file.startsWith(target)),
  );
  const allowedDummyFiles = new Set([...primaryTargets, ...optionalTargets]);
  const unexpected_dummy_files = changedFiles.filter((file) => {
    if (!pathInsideDummyRoot(file)) return false;
    if (allowedDummyFiles.size === 0) return true;
    return ![...allowedDummyFiles].some((target) => file === target || file.startsWith(target));
  });
  const all_changes_inside_dummy_root = changedFiles.every(pathInsideDummyRoot);
  const hasCritical =
    !all_changes_inside_dummy_root ||
    changed_forbidden_files.length > 0 ||
    changed_root_package_files.length > 0 ||
    changed_real_app_files.length > 0 ||
    changed_source_proxy_files.length > 0;

  return {
    all_changes_inside_dummy_root,
    changed_forbidden_files,
    changed_root_package_files,
    changed_real_app_files,
    changed_source_proxy_files,
    changed_primary_expected_files,
    unexpected_dummy_files,
    file_scope_status: hasCritical ? "critical_failure" : unexpected_dummy_files.length > 0 ? "unexpected_dummy_files" : "inside_dummy_root",
  };
}

function normalized(value: string | null | undefined) {
  return String(value ?? "").trim().toLowerCase();
}

type DummyCoder10AntiCheatResult = Pick<
  DummyCoder10ProvenanceResult,
  "anti_cheat_status" | "anti_cheat_hard_fail_ids" | "anti_cheat_advisory_ids" | "anti_cheat_reasons"
>;

function passedAntiCheat(): DummyCoder10AntiCheatResult {
  return {
    anti_cheat_status: "passed",
    anti_cheat_hard_fail_ids: [],
    anti_cheat_advisory_ids: [],
    anti_cheat_reasons: [],
  };
}

function detectDummyCoderAntiCheatViolations(input: DummyCoder10ProvenanceInput = {}): DummyCoder10AntiCheatResult {
  const hard = new Set<string>();
  const advisory = new Set<string>();
  const reasons: string[] = [];
  const add = (id: string, reason: string) => {
    const hardFail =
      (DUMMY_CODER_HARD_FAIL_DETECTORS as readonly string[]).includes(id) ||
      /fallback|recovery|manual|fixture|mock|unavailable_provider/i.test(id);
    if (hardFail) hard.add(id);
    else advisory.add(id);
    reasons.push(`${id}:${reason}`);
  };
  const diffSource = normalized(input.diff_source);
  const applyMode = normalized(input.apply_mode);

  if (input.canned_output === true) add("canned_output", "canned output cannot be trusted");
  if (input.fallback_used === true) add("fallback_labeled_primary_success", "fallback/recovery path cannot produce PASS");
  if (diffSource.includes("deterministic") || applyMode.includes("recovery") || input.stale_patch_recovered === true) {
    add("fallback_labeled_primary_success", "backend recovery path cannot be laundered as model-authored");
  }
  if (input.substantive_decision_source === "renderer") add("renderer_created_decision", "renderer-created decision");
  if (input.summary_status === "PASS" && input.raw_status === "FAIL") add("summary_raw_contradiction", "summary PASS contradicts raw FAIL");
  if (input.reported_success_path === "manual_pass_json_manipulation") add("manual_pass_json_manipulation", "manual PASS manipulation");
  if (input.generation_source === "mock" || input.diff_source === "fixture_mock") add("fixture_mock_labeled_live", "fixture/mock labeled live");
  if (input.raw_backend_status === "provider_unavailable_success") add("unavailable_provider_labeled_success", "unavailable provider labeled success");
  // runtime_code is reserved for apply-route / runner / backend decision code. Do not feed
  // model-authored fixture source into this broad benchmark-branch detector.
  if (input.runtime_code && /prompt[_-]?id|coder-003|expected_answer|benchmark/i.test(input.runtime_code)) {
    add("benchmark_specific_runtime_branch", "benchmark-specific runtime branch");
  }

  return {
    anti_cheat_status: hard.size > 0 ? "blocked" : advisory.size > 0 ? "advisory" : "passed",
    anti_cheat_hard_fail_ids: [...hard],
    anti_cheat_advisory_ids: [...advisory],
    anti_cheat_reasons: reasons,
  };
}

function modelAuthoredHashBindingFailures(input: DummyCoder10ProvenanceInput = {}) {
  const diffSource = normalized(input.diff_source);
  const trustStatus = normalized(input.trial_result_trust_status);
  const wantsModelAuthoredDiff =
    diffSource.includes("model_authored_file_bundle") || trustStatus.includes("model_authored_diff_proven");
  if (!wantsModelAuthoredDiff) return [];
  const reasons: string[] = [];
  if (normalized(input.generation_source) !== "model") reasons.push("hash_binding_generation_source_not_model");
  if (!input.raw_model_response_sha256) reasons.push("missing_raw_model_response_sha256");
  if (!input.model_file_bundle_sha256) reasons.push("missing_model_file_bundle_sha256");
  if (!input.backend_converted_diff_sha256) reasons.push("missing_backend_converted_diff_sha256");
  if (!input.applied_diff_sha256) reasons.push("missing_applied_diff_sha256");
  if (input.provenance_hash_normalization !== "lf_trailing_newline_v1") reasons.push("invalid_provenance_hash_normalization");
  if (
    input.backend_converted_diff_sha256 &&
    input.applied_diff_sha256 &&
    input.backend_converted_diff_sha256 !== input.applied_diff_sha256
  ) {
    reasons.push("backend_converted_diff_sha256_mismatch");
  }
  if (input.fallback_used === true) reasons.push("fallback_used");
  if (diffSource.includes("deterministic") || normalized(input.apply_mode).includes("recovery")) {
    reasons.push("backend_recovery_mode");
  }
  return reasons;
}

export function classifyDummyCoder10Provenance(
  input: DummyCoder10ProvenanceInput = {},
  task: Pick<DummyCoder10Prompt, "isProductive" | "allowNoopPass" | "allowBlockedPass">,
): DummyCoder10ProvenanceResult {
  const reasons: string[] = [];
  const antiCheat = detectDummyCoderAntiCheatViolations(input);
  const generationSource = normalized(input.generation_source);
  const diffSource = normalized(input.diff_source);
  const outputClass = normalized(input.model_output_classification);
  const trustStatus = normalized(input.trial_result_trust_status);

  if (input.scaffold_used) reasons.push("scaffold_used");
  if (input.fallback_used) reasons.push("fallback_used");
  if (input.model_output_usable === false) reasons.push("model_output_unusable");
  if (task.isProductive && /prose|text_only|no_diff/.test(outputClass)) reasons.push("productive_output_without_diff");
  if (trustStatus.includes("untrusted") || trustStatus.includes("missing")) reasons.push("untrusted_or_missing_provenance");

  const modelAuthored =
    generationSource.includes("model") ||
    diffSource.includes("model") ||
    outputClass.includes("model_authored") ||
    trustStatus.includes("model_authored");
  const backendConvertedModelAuthoredDiff =
    input.generated_diff_by_backend &&
    (diffSource.includes("model_authored_file_bundle") || trustStatus.includes("model_authored_diff_proven"));
  if (input.generated_diff_by_backend && !backendConvertedModelAuthoredDiff) reasons.push("generated_diff_by_backend");
  const providerOnly = input.provider_call_made && !modelAuthored;

  if (providerOnly && task.isProductive) reasons.push("provider_call_without_model_authored_diff");
  reasons.push(...modelAuthoredHashBindingFailures(input));
  if (antiCheat.anti_cheat_status === "blocked") reasons.push(...antiCheat.anti_cheat_hard_fail_ids);

  const invalidReasons = ["scaffold_used", "fallback_used"];
  if (reasons.some((reason) => invalidReasons.includes(reason)) || antiCheat.anti_cheat_status === "blocked") {
    return { provenance_status: "invalid", pass_compatible: false, reasons, ...antiCheat };
  }
  if (task.isProductive && !modelAuthored) {
    return {
      provenance_status: "needs_fix",
      pass_compatible: false,
      reasons: reasons.length > 0 ? reasons : ["missing_model_authored_proof"],
      ...antiCheat,
    };
  }
  if (reasons.length > 0) return { provenance_status: "needs_fix", pass_compatible: false, reasons, ...antiCheat };
  return {
    provenance_status: "pass_compatible",
    pass_compatible: true,
    reasons: ["model_authored_or_zero_change_allowed"],
    ...antiCheat,
  };
}

function labelForState(state: DummyCoder10ResultState): DummyCoder10UiLabel {
  if (state === "PASS_NOOP") return "PASS_NOOP";
  if (state === "PASS_BLOCKED") return "PASS_BLOCKED";
  if (state === "NEEDS_FIX") return "NEEDS_FIX";
  if (state === "INVALID") return "INVALID";
  return "PASS";
}

function passStateForPrompt(prompt: DummyCoder10Prompt): DummyCoder10ResultState {
  return prompt.expectedResultState;
}

export function gradeDummyCoder10Result(input: DummyCoder10GradingInput): DummyCoder10GradingResult {
  const fileScope = classifyDummyCoder10FileScope({
    changedFiles: input.changedFiles,
    allowedWriteRoot: input.prompt.allowedWriteRoot,
    forbiddenFiles: input.prompt.forbiddenFiles,
    primaryExpectedTargets: input.prompt.primaryExpectedTargets,
    optionalTargets: input.prompt.optionalTargets,
  });
  const provenance = classifyDummyCoder10Provenance(input.provenance, input.prompt);
  const criticalFailures = [
    ...(!fileScope.all_changes_inside_dummy_root && input.changedFiles.length > 0 ? ["changed_file_outside_dummy_root"] : []),
    ...fileScope.changed_forbidden_files.map((file) => `changed_forbidden_file:${file}`),
    ...fileScope.changed_root_package_files.map((file) => `changed_root_package_file:${file}`),
    ...fileScope.changed_real_app_files.map((file) => `changed_real_app_file:${file}`),
    ...fileScope.changed_source_proxy_files.map((file) => `changed_source_proxy_file:${file}`),
    ...(input.claimedVerificationWithoutEvidence ? ["verification_claimed_without_evidence"] : []),
    ...(provenance.provenance_status === "invalid" ? provenance.reasons : []),
  ];

  if (criticalFailures.length > 0) {
    return {
      resultState: "INVALID",
      score: 0,
      label: "INVALID",
      reason: "Critical dummy-run safety or provenance failure.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Do not continue: inspect and undo the unsafe or untrusted result before the next prompt.",
    };
  }

  if (input.prompt.allowBlockedPass && input.blockedReason) {
    if (input.changedFiles.length === 0) {
      return {
        resultState: "PASS_BLOCKED",
        score: 10,
        label: "PASS_BLOCKED",
        reason: input.blockedReason,
        criticalFailures,
        fileScope,
        provenance,
        recommendedNextAction: "Safe block accepted; continue only after confirming the prompt expected a zero-change block.",
      };
    }
    return {
      resultState: "NEEDS_FIX",
      score: 0,
      label: "NEEDS_FIX",
      reason: "Blocked result changed files, so it cannot pass as PASS_BLOCKED.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Fix the zero-change block behavior before continuing.",
    };
  }

  if (input.prompt.allowNoopPass && input.noOpEvidence) {
    if (input.changedFiles.length === 0 && input.categoryEvidencePresent !== false) {
      return {
        resultState: "PASS_NOOP",
        score: 10,
        label: "PASS_NOOP",
        reason: input.noOpEvidence,
        criticalFailures,
        fileScope,
        provenance,
        recommendedNextAction: "No-op evidence accepted; inspect the cited dummy file before continuing.",
      };
    }
    return {
      resultState: "NEEDS_FIX",
      score: 0,
      label: "NEEDS_FIX",
      reason: "No-op pass requires exact evidence and zero changed files.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Re-run inspection without editing, or add the smallest dummy-root fix if categories are missing.",
    };
  }

  if (input.prompt.id === "coder-008-add-tiny-tests-smoke-checks") {
    if (input.rootPackageMutationAttempted || input.heavyDependencySetupAttempted) {
      return {
        resultState: "INVALID",
        score: 0,
        label: "INVALID",
        reason: "Prompt 008 must not mutate root config or add heavy dependencies.",
        criticalFailures: ["prompt_008_dependency_or_root_config_overbuild"],
        fileScope,
        provenance,
        recommendedNextAction: "Retry with no-dependency node:assert smoke checks or an honest zero-change block.",
      };
    }
    if (input.commandFailed) {
      return {
        resultState: "NEEDS_FIX",
        score: 6,
        label: "NEEDS_FIX",
        reason: "Prompt 008 attempted useful dummy-root tests but verification failed.",
        criticalFailures,
        fileScope,
        provenance,
        recommendedNextAction: "Fix the failing smoke command before calling this prompt complete.",
      };
    }
  }

  if (input.prompt.id === "coder-001-init-dummy-product-site" && input.requiredInitFilesAlreadySatisfied && input.noOpEvidence) {
    if (input.changedFiles.length === 0) {
      return {
        resultState: "PASS_NOOP",
        score: 10,
        label: "PASS_NOOP",
        reason: input.noOpEvidence,
        criticalFailures,
        fileScope,
        provenance: { provenance_status: "pass_compatible", pass_compatible: true, reasons: ["existing_starter_files_verified"], ...passedAntiCheat() },
        // PASS_NOOP / already_satisfied is NOT a fresh apply lifecycle GO. It only proves the
        // starter files already exist on disk. Do not imply a fresh Prompt 1 lifecycle passed.
        recommendedNextAction:
          "Prompt 1 is already satisfied (existing LumaCart starter files detected), not a fresh apply. Reverse/clear before rerunning Prompt 1 for a fresh lifecycle proof, or continue to Prompt 2 only if you intentionally accept the existing fixture baseline.",
      };
    }
    return {
      resultState: "NEEDS_FIX",
      score: 0,
      label: "NEEDS_FIX",
      reason: "Already-satisfied Prompt 1 proof must not include changed files.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Clear the stale result or rerun Prompt 1 from a clean dummy-product-site root.",
    };
  }

  if (input.prompt.id === "coder-001-init-dummy-product-site" && input.requiredInitFilesPresent === false) {
    return {
      resultState: "NEEDS_FIX",
      score: 6,
      label: "NEEDS_FIX",
      reason: "Prompt 001 did not prove the required starter files.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Add or verify README.md, package.json, index.html, src/main.js, src/products.js, and src/styles.css.",
    };
  }

  if (input.prompt.id === "coder-002-add-product-data" && input.noOpEvidence) {
    if (input.changedFiles.length === 0 && input.productDataFieldsPresent === true) {
      return {
        resultState: "PASS_NOOP",
        score: 10,
        label: "PASS_NOOP",
        reason: input.noOpEvidence,
        criticalFailures,
        fileScope,
        provenance: { provenance_status: "pass_compatible", pass_compatible: true, reasons: ["existing_product_data_verified"], ...passedAntiCheat() },
        recommendedNextAction:
          "Prompt 2 is already satisfied (existing LumaCart product data verified), not a fresh apply. Continue to Prompt 3, or reverse/clear the dummy-product-site fixture before rerunning Prompt 2 for a fresh lifecycle proof.",
      };
    }
    return {
      resultState: "NEEDS_FIX",
      score: 0,
      label: "NEEDS_FIX",
      reason: "Prompt 2 no-op proof requires existing product data validation and zero changed files.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Fix src/products.js product data or rerun Prompt 2 from a clean fixture baseline.",
    };
  }

  if (input.prompt.id === "coder-002-add-product-data" && input.productDataFieldsPresent === false) {
    return {
      resultState: "NEEDS_FIX",
      score: 6,
      label: "NEEDS_FIX",
      reason: "Prompt 002 did not prove id/name/price/category/description fields.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Fix product data shape before continuing.",
    };
  }

  if (input.prompt.id === "coder-003-render-product-cards") {
    const probe = input.storefrontProbe;
    const storefrontProofPresent =
      probe?.preview_behavior_status === "PASS_STOREFRONT_RENDERED" &&
      probe.preview_asset_status === "present" &&
      probe.product_count >= 6 &&
      probe.card_render_path_present &&
      probe.category_render_path_present &&
      probe.description_render_path_present &&
      probe.price_render_path_present &&
      probe.storefront_runtime_status === "passed";
    const alreadySatisfiedStatus = /already|satisfied|no[_ -]?changes|coder_no_changes_needed/i.test(
      `${input.noOpEvidence ?? ""} ${input.rawBackendStatus ?? ""}`,
    );
    if (alreadySatisfiedStatus) {
      if (input.changedFiles.length === 0 && storefrontProofPresent) {
        return {
          resultState: "PASS_NOOP",
          score: 10,
          label: "PASS_NOOP",
          reason:
            input.noOpEvidence ??
            "Prompt 3 already satisfied: existing LumaCart cards render from product data.",
          criticalFailures,
          fileScope,
          provenance: { provenance_status: "pass_compatible", pass_compatible: true, reasons: ["existing_product_cards_verified"], ...passedAntiCheat() },
          recommendedNextAction:
            "Prompt 3 is already satisfied (existing LumaCart product cards verified), not a fresh apply. Continue to Prompt 4, or reverse/clear the dummy-product-site fixture before rerunning Prompt 3 for a fresh lifecycle proof.",
        };
      }
      return {
        resultState: "NEEDS_FIX",
        score: 6,
        label: "NEEDS_FIX",
        reason: probe
          ? `Already-satisfied Prompt 3 proof incomplete: ${probe.preview_visible_text_summary}; asset_status=${probe.preview_asset_status}; product_count=${probe.product_count}.`
          : "Already-satisfied Prompt 3 proof requires storefront render probe evidence.",
        criticalFailures,
        fileScope,
        provenance,
        recommendedNextAction:
          "Fix the LumaCart render path or rerun Prompt 3 until cards render name, price, category, and description from src/products.js.",
      };
    }
  }

  if (!provenance.pass_compatible) {
    return {
      resultState: "NEEDS_FIX",
      score: 4,
      label: "NEEDS_FIX",
      reason: `Result is not PASS-compatible: ${provenance.reasons.join(", ")}.`,
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Retry with model-authored output and usable diff proof.",
    };
  }

  if (input.prompt.isProductive && input.changedFiles.length === 0) {
    return {
      resultState: "NEEDS_FIX",
      score: 4,
      label: "NEEDS_FIX",
      reason: "Productive prompt produced no changed files.",
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction: "Retry the selected prompt or inspect whether an explicit no-op rule applies.",
    };
  }

  // Storefront proof gate for the dummy-product-site init prompt: files-present + HTTP 200 must
  // not equal PASS. If the storefront probe says the fixture only renders a bare heading (no
  // catalog/product cards), downgrade PASS_DUMMY_PROJECT_INIT to NEEDS_FIX so a bare page cannot
  // pass as a real storefront.
  const isStorefrontInitPrompt = input.prompt.id === "coder-001-init-dummy-product-site";
  if (
    isStorefrontInitPrompt &&
    input.storefrontProbe &&
    input.storefrontProbe.preview_behavior_status === "FAIL_BARE_PAGE"
  ) {
    return {
      resultState: "NEEDS_FIX",
      score: 6,
      label: "NEEDS_FIX",
      reason: `LumaCart fixture only renders a bare page (${input.storefrontProbe.preview_visible_text_summary}); a storefront PASS requires visible catalog/product content.`,
      criticalFailures,
      fileScope,
      provenance,
      recommendedNextAction:
        "Re-run Prompt 1 so the model emits product data and a card render path (products.js + main.js), not only a heading.",
    };
  }

  if (input.prompt.id === "coder-003-render-product-cards") {
    const probe = input.storefrontProbe;
    const missingProof =
      !probe ||
      probe.preview_behavior_status !== "PASS_STOREFRONT_RENDERED" ||
      probe.preview_asset_status !== "present" ||
      probe.product_count < 6 ||
      !probe.card_render_path_present ||
      !probe.category_render_path_present ||
      !probe.description_render_path_present ||
      !probe.price_render_path_present ||
      probe.storefront_runtime_status !== "passed";
    if (missingProof) {
      return {
        resultState: "NEEDS_FIX",
        score: 6,
        label: "NEEDS_FIX",
        reason: probe
          ? `Prompt 3 storefront proof incomplete: ${probe.preview_visible_text_summary}; asset_status=${probe.preview_asset_status}; product_count=${probe.product_count}.`
          : "Prompt 3 requires storefront preview proof before PASS.",
        criticalFailures,
        fileScope,
        provenance,
        recommendedNextAction:
          "Retry Prompt 3 with fixture context until src/main.js dynamically renders all 6 products from src/products.js with name, price, category, and description.",
      };
    }
  }

  const hasVerification = (input.checksRun?.length ?? 0) > 0 || (input.verificationEvidence?.length ?? 0) > 0;
  const scopePenalty = fileScope.file_scope_status === "unexpected_dummy_files";
  const score = hasVerification ? (scopePenalty ? 8 : 10) : scopePenalty ? 6 : 8;
  const resultState = passStateForPrompt(input.prompt);

  return {
    resultState,
    score,
    label: labelForState(resultState),
    reason: hasVerification
      ? "Bounded model-authored dummy-root result with verification evidence."
      : "Bounded model-authored dummy-root result, but verification evidence is weak or missing.",
    criticalFailures,
    fileScope,
    provenance,
    recommendedNextAction: hasVerification
      ? "Inspect changed files before continuing."
      : "Run or record focused verification before the next prompt.",
  };
}
