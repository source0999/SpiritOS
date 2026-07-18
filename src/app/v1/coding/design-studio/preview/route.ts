import { createHash, randomUUID } from "node:crypto";

import { persistDesignPreview } from "@/lib/coding/design-approval-authority";

const ACTIONABLE_PROMPTS = [
  "make it modern",
  "make it mobile responsive",
  "make this feel premium and not generic",
  "make it less google ai studio",
];

const CLARIFY_WITHOUT_TARGET_PROMPTS = [
  "make it look premium",
  "make it better",
  "make it clean",
];

type DesignStudioPreviewRequest = {
  critic_probe?: {
    anti_template_status?: "fail" | "pass" | "unknown";
    contrast_status?: "fail" | "pass" | "unknown";
    failed_probe?: string;
    hierarchy_score?: number;
    mobile_status?: "fail" | "pass" | "unknown";
    originality_status?: "fail" | "pass" | "unknown";
    repair_count?: number;
    screenshot_refs?: string[];
    spacing_score?: number;
  };
  originality_probe?: {
    class_names?: string[];
    copied_brand_identity?: boolean;
    generated_description?: string;
    project_motif?: string;
    raw_css_supplied?: boolean;
    reference_similarity?: "direct_clone" | "inspired" | "unknown";
  };
  prompt?: string;
  model_probe?: {
    enabled?: boolean;
    model?: string;
    provider?: "ollama";
    require_source?: boolean;
    timeout_ms?: number;
  };
  reference_upload?: {
    file_name?: string;
    license_state?: string;
    mime_type?: string;
    size_bytes?: number;
    source_type?: string;
  };
  request_id?: string;
  target_surface?: string;
  website_css_reference?: {
    adapter_name?: string;
    css_text?: string;
    source_url?: string;
  };
  writeback_preview?: {
    content?: unknown;
  };
};

async function readPreviewRequest(request?: Request): Promise<DesignStudioPreviewRequest> {
  if (!request) {
    return {};
  }

  try {
    return (await request.json()) as DesignStudioPreviewRequest;
  } catch {
    return {};
  }
}

function normalizeText(value: string | undefined) {
  return value?.trim().toLowerCase() ?? "";
}

function promptHash(value: string | undefined) {
  return createHash("sha256").update(value ?? "", "utf8").digest("hex");
}

function requestIdentity(input: DesignStudioPreviewRequest) {
  const requestId = input.request_id?.trim() || `design-studio-route-${randomUUID()}`;
  const originalUserPromptHash = promptHash(input.prompt);
  return {
    original_user_prompt_hash: originalUserPromptHash,
    request_id: requestId,
    trace_id: `design-studio-trace-${originalUserPromptHash.slice(0, 12)}-${requestId.slice(-8)}`,
  };
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableJson(item)).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256Json(value: unknown) {
  return createHash("sha256").update(stableJson(value), "utf8").digest("hex");
}

function sha256Text(value: string) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function hasModelProbeSource(input: DesignStudioPreviewRequest) {
  return Boolean(
    input.reference_upload?.file_name?.trim() ||
      input.website_css_reference?.source_url?.trim() ||
      input.website_css_reference?.css_text?.trim(),
  );
}

function modelProbeBlockedResponse(input: DesignStudioPreviewRequest, identity: ReturnType<typeof requestIdentity>, reason: string) {
  const model = input.model_probe?.model?.trim() || "phi4-mini:latest";
  return Response.json(
    {
      advisory_only: true,
      apply_authority: false,
      approval_authority: false,
      commit_authority: false,
      design_studio_route: "/coding/design-studio",
      endpoint: "/v1/coding/design-studio/preview",
      fake_go_guard: {
        design_packet_exists_is_go: false,
        fallback_success_for_model_failure: false,
        preview_opens_is_go: false,
        required_downstream_consumption: "accepted_design_packet_to_named_coder_packet_consumer",
        unconsumed_packet_blocks_go: true,
      },
      hidden_execution_started: false,
      memory_write_authority: false,
      model_call_made: false,
      model_invocation_result: {
        blocked_env: true,
        event_id: `ollama-${model.replace(/[^a-z0-9._-]+/gi, "-")}-blocked-env`,
        failure_mode: reason,
        model,
        ok: false,
        output_excerpt: "",
        output_hash: "",
        provider: "ollama",
        trace_id: identity.trace_id,
      },
      message: "MODEL_PROBE_BLOCKED_ENV",
      outcome: "MODEL_PROBE_BLOCKED_ENV",
      original_user_prompt_hash: identity.original_user_prompt_hash,
      provider_call_made: false,
      reason_code: reason,
      push_authority: false,
      request_id: identity.request_id,
      sandbox_apply_authority: false,
      trace_id: identity.trace_id,
    },
    { status: 424 },
  );
}

function promptIncludes(prompt: string, words: string[]) {
  return words.some((word) => prompt.includes(word));
}

function deriveList(prompt: string, rules: [string, string[]][], fallback: string[]) {
  const values = rules
    .filter(([, words]) => promptIncludes(prompt, words))
    .map(([value]) => value);
  return values.length > 0 ? values : fallback;
}

function deriveDesignPacket(input: DesignStudioPreviewRequest, identity: ReturnType<typeof requestIdentity>) {
  const prompt = normalizeText(input.prompt);
  const targetSurface = input.target_surface?.trim() || "target_surface_required";
  const intent = deriveList(
    prompt,
    [
      ["increase perceived product quality", ["premium", "polished", "high-end"]],
      ["improve mobile usability", ["mobile", "responsive", "small screen"]],
      ["tighten operator workflow clarity", ["workbench", "dashboard", "operator", "tool"]],
      ["create editorial scanning rhythm", ["editorial", "spacious", "story"]],
      ["make interaction keyboard-first", ["keyboard", "command", "shortcut"]],
    ],
    [prompt ? "translate messy visual request into bounded design packet" : "preview shell only"],
  );
  const audience = deriveList(
    prompt,
    [
      ["operators reviewing Source Proxy evidence", ["operator", "evidence", "proof", "source proxy"]],
      ["mobile reviewers", ["mobile", "phone", "small screen"]],
      ["keyboard-heavy power users", ["keyboard", "shortcut", "command"]],
      ["design reviewers", ["design", "visual", "premium", "editorial"]],
    ],
    ["SpiritOS coding reviewers"],
  );
  const constraints = [
    "preview_only_no_apply",
    "no_execute_approved",
    "no_raw_css_ingest",
    ...deriveList(
      prompt,
      [
        ["preserve dense workbench utility", ["dense", "workbench", "dashboard"]],
        ["avoid generic AI Studio layout", ["generic", "ai studio", "not generic"]],
        ["support mobile responsive proof", ["mobile", "responsive"]],
        ["support keyboard and focus proof", ["keyboard", "focus", "shortcut"]],
      ],
      ["preserve preview/apply boundary"],
    ),
  ];
  const referenceInputs = [
    input.reference_upload?.file_name ? `upload:${input.reference_upload.file_name}` : null,
    input.website_css_reference?.source_url ? "website_css_reference_url_recorded_only" : null,
    input.website_css_reference?.css_text ? "raw_css_quarantined_not_ingested" : null,
  ].filter(Boolean);
  const visualDirection = deriveList(
    prompt,
    [
      ["premium restrained product surface", ["premium", "polished", "high-end"]],
      ["editorial spacious hierarchy", ["editorial", "spacious"]],
      ["dense console workbench", ["dense", "workbench", "dashboard"]],
      ["mobile-first stacked controls", ["mobile", "responsive"]],
      ["precise technical evidence surface", ["precise", "evidence", "proof"]],
    ],
    ["SpiritOS glass console workbench"],
  );
  const accessibilityNotes = [
    "visible focus states",
    "semantic headings",
    "no text overlap",
    ...deriveList(
      prompt,
      [
        ["keyboard navigation must be first-class", ["keyboard", "shortcut", "command"]],
        ["mobile controls must remain tappable", ["mobile", "phone", "responsive"]],
        ["contrast must survive dark UI surfaces", ["contrast", "readable", "legible"]],
      ],
      ["contrast and responsive checks required before acceptance"],
    ),
  ];
  const riskFlags = [
    !input.target_surface?.trim() ? "missing_target_surface" : null,
    prompt.length < 24 ? "weak_prompt_detail" : null,
    promptIncludes(prompt, ["copy", "clone", "same as"]) ? "copy_similarity_pressure" : null,
    promptIncludes(prompt, ["css", "stylesheet"]) ? "raw_css_pressure" : null,
    referenceInputs.length > 0 ? "reference_policy_required" : null,
  ].filter(Boolean);
  const packetCore = {
    accessibility_notes: accessibilityNotes,
    audience,
    constraints,
    intent,
    page_app_target: targetSurface,
    reference_inputs: referenceInputs.length > 0 ? referenceInputs : ["none_supplied"],
    risk_flags: riskFlags.length > 0 ? riskFlags : ["low_preview_only"],
    visual_direction: visualDirection,
  };
  const designPacketHash = sha256Json({
    original_user_prompt_hash: identity.original_user_prompt_hash,
    packet: packetCore,
  });

  return {
    ...packetCore,
    anti_template_checks: ["reject_generic_ai_studio_layout", "require_project_specific_motif"],
    coder_packet: {
      allowed_files: ["src/components/coding/DesignStudioShell.tsx"],
      css_rules: ["derive tokens from project surface", "do not copy raw CSS selectors"],
      forbidden_files: ["docs/evidence/**", ".env*", ".spirit-backups/**"],
      responsive_rules: ["desktop and mobile proof required before GO"],
      target_files: ["src/components/coding/DesignStudioShell.tsx"],
      verification_commands: [
        "npx vitest run src/app/v1/coding/design-studio/preview/__tests__/route.test.ts --reporter=dot",
      ],
    },
    derivation_source: "heuristic_prompt_structuring_no_model",
    design_packet_hash: designPacketHash,
    design_packet_id: `design-packet-${designPacketHash.slice(0, 12)}`,
    obsidian_context_refs: [],
    project_specific_motif: packetCore.visual_direction[0],
    style_family_blend: packetCore.visual_direction,
    target_surface: targetSurface,
    trace_id: identity.trace_id,
    visual_pass_criteria: [
      "clear preview/apply boundary",
      "mobile and desktop layout remain scannable",
      "no Google AI Studio generic shell",
    ],
  };
}

type DerivedDesignPacket = ReturnType<typeof deriveDesignPacket>;

async function invokeOllamaDesignGuidance(
  input: DesignStudioPreviewRequest,
  designPacket: DerivedDesignPacket,
  identity: ReturnType<typeof requestIdentity>,
) {
  const model = input.model_probe?.model?.trim() || "phi4-mini:latest";
  const baseUrl = (process.env.SOURCE_PROXY_OLLAMA_BASE_URL || process.env.OLLAMA_HOST || "http://127.0.0.1:11434").replace(/\/$/, "");
  const modelPrompt = [
    "You are enriching a preview-only Design Studio packet.",
    "Return one concise design guidance sentence, no markdown.",
    `User prompt: ${input.prompt ?? ""}`,
    `Current intent: ${(designPacket.intent ?? []).join("; ")}`,
    `Current visual direction: ${(designPacket.visual_direction ?? []).join("; ")}`,
  ].join("\n");
  const inputHash = sha256Text(modelPrompt);
  const timeoutMs = Math.min(Math.max(input.model_probe?.timeout_ms ?? 60_000, 1), 60_000);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${baseUrl}/api/generate`, {
      body: JSON.stringify({
        model,
        options: {
          num_predict: 48,
          temperature: 0,
        },
        prompt: modelPrompt,
        stream: false,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
      signal: controller.signal,
    });
    const payload = await response.json();
    const output = typeof payload?.response === "string" ? payload.response.trim() : "";
    const outputHash = sha256Text(output);
    return {
      byte_count: Buffer.byteLength(output, "utf8"),
      event_id: `ollama-${model.replace(/[^a-z0-9._-]+/gi, "-")}-${outputHash.slice(0, 12)}`,
      failure_mode: response.ok && Boolean(output) ? null : "UNAVAILABLE_MODEL_BLOCKED_ENV",
      input_hash: inputHash,
      model,
      ok: response.ok && Boolean(output),
      output_excerpt: output.slice(0, 220),
      output_hash: outputHash,
      provider: "ollama",
      response_status: response.status,
      trace_id: identity.trace_id,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Ollama invocation failed.";
    const failureMode = error instanceof Error && error.name === "AbortError"
      ? "TIMEOUT_RETRY_LIMITED_BLOCKED_ENV"
      : "PROVIDER_UNREACHABLE_BLOCKED_ENV";
    return {
      blocked_env: true,
      error: errorMessage,
      event_id: `ollama-${model.replace(/[^a-z0-9._-]+/gi, "-")}-failed`,
      failure_mode: failureMode,
      input_hash: inputHash,
      model,
      ok: false,
      output_excerpt: "",
      output_hash: "",
      provider: "ollama",
      trace_id: identity.trace_id,
    };
  } finally {
    clearTimeout(timeout);
  }
}

function applyModelGuidanceToDesignPacket(designPacket: DerivedDesignPacket, modelInvocation: Record<string, any>) {
  if (!modelInvocation.ok) {
    return designPacket;
  }
  const enrichedPacket = {
    ...designPacket,
    model_guidance: {
      event_id: modelInvocation.event_id,
      output_hash: modelInvocation.output_hash,
      provider_model_name: modelInvocation.model,
      text: modelInvocation.output_excerpt,
    },
  };
  const designPacketHash = sha256Json({
    model_guidance: enrichedPacket.model_guidance,
    original_design_packet_hash: designPacket.design_packet_hash,
    packet: {
      accessibility_notes: enrichedPacket.accessibility_notes,
      audience: enrichedPacket.audience,
      constraints: enrichedPacket.constraints,
      intent: enrichedPacket.intent,
      model_guidance: enrichedPacket.model_guidance,
      page_app_target: enrichedPacket.page_app_target,
      reference_inputs: enrichedPacket.reference_inputs,
      risk_flags: enrichedPacket.risk_flags,
      visual_direction: enrichedPacket.visual_direction,
    },
  });
  return {
    ...enrichedPacket,
    design_packet_hash: designPacketHash,
    design_packet_id: `design-packet-${designPacketHash.slice(0, 12)}`,
  };
}

function buildPromptOutcome(input: DesignStudioPreviewRequest, identity: ReturnType<typeof requestIdentity>) {
  const prompt = normalizeText(input.prompt);
  const targetSurface = input.target_surface?.trim();
  const hasTarget = Boolean(targetSurface);
  const isActionable = ACTIONABLE_PROMPTS.some((example) => prompt.includes(example));
  const requiresClarification =
    !hasTarget && CLARIFY_WITHOUT_TARGET_PROMPTS.some((example) => prompt.includes(example));

  if (requiresClarification || (prompt && !hasTarget && !isActionable)) {
    return {
      design_packet: null,
      outcome: "ASK_CLARIFY_TARGET",
      reason: "target_surface_required",
    };
  }

  if (prompt && hasTarget) {
    const designPacket = deriveDesignPacket(input, identity);
    return {
      design_packet: designPacket,
      outcome: "DESIGN_PACKET_PREVIEW",
      reason: isActionable ? "actionable_messy_prompt_with_target" : "targeted_prompt_preview",
    };
  }

  return {
    design_packet: null,
    outcome: "PREVIEW_SHELL_ONLY",
    reason: "no_prompt_supplied",
  };
}

function buildReferenceUploadOutcome(input: DesignStudioPreviewRequest) {
  const upload = input.reference_upload;
  if (!upload) {
    return {
      outcome: "NO_REFERENCE_UPLOAD",
      reference_metadata: null,
      staged_for_generation: false,
    };
  }

  const fileName = upload.file_name?.trim() ?? "";
  const mimeType = upload.mime_type?.trim().toLowerCase() ?? "";
  const sourceType = upload.source_type?.trim().toLowerCase() ?? "uploaded_file";
  const licenseState = upload.license_state?.trim().toLowerCase() ?? "unknown";
  const sizeBytes = upload.size_bytes ?? 0;
  const safeMimeTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
  const blockers: string[] = [];

  if (!fileName) {
    blockers.push("missing_file_name");
  }
  if (!safeMimeTypes.has(mimeType)) {
    blockers.push("unsupported_mime_type");
  }
  if (sizeBytes <= 0 || sizeBytes > 8_000_000) {
    blockers.push("size_outside_preview_limit");
  }
  if (licenseState !== "owned" && licenseState !== "approved_reference") {
    blockers.push("license_or_source_uncertain");
  }
  if (sourceType === "raw_css" || sourceType === "external_url") {
    blockers.push("authority_hard_stop_required");
  }

  if (blockers.length > 0) {
    return {
      blockers,
      outcome: "REFERENCE_UPLOAD_BLOCKED",
      reference_metadata: null,
      staged_for_generation: false,
    };
  }

  return {
    blockers: [],
    outcome: "REFERENCE_METADATA_STAGED",
    reference_metadata: {
      file_name: fileName,
      license_state: licenseState,
      mime_type: mimeType,
      reference_id: "reference-upload-preview-local",
      source_type: sourceType,
      source_use_policy: "inspiration_only_no_1_to_1_copy",
    },
    staged_for_generation: false,
    visual_index_adapter: {
      adapter_status: "preview_contract_only",
      memory_promotion_authority: false,
      requires_downstream_consumption: true,
    },
  };
}

function stablePreviewHash(value: string) {
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `preview_${(hash >>> 0).toString(16).padStart(8, "0")}`;
}

function buildWebsiteCssReferenceOutcome(input: DesignStudioPreviewRequest) {
  const reference = input.website_css_reference;
  if (!reference) {
    return {
      outcome: "NO_WEBSITE_CSS_REFERENCE",
      raw_css_quarantine: null,
    };
  }

  const sourceUrl = reference.source_url?.trim() ?? "";
  const cssText = reference.css_text ?? "";
  const adapterName = reference.adapter_name?.trim() ?? "local_quarantine_adapter";
  const blockers: string[] = [];

  if (sourceUrl) {
    blockers.push("external_url_scrape_requires_human_approval");
  }
  if (cssText.trim()) {
    blockers.push("raw_css_ingestion_requires_human_approval");
  }
  if (adapterName !== "local_quarantine_adapter") {
    blockers.push("external_tool_install_or_adapter_requires_human_approval");
  }

  return {
    blockers,
    external_tool_adapter: {
      adapter_name: adapterName,
      install_authority: false,
      local_only: adapterName === "local_quarantine_adapter",
      output_contract: "DesignDNA_or_referenceDNA_only",
    },
    no_copy_policy: {
      class_names_discarded: true,
      direct_css_clone_forbidden: true,
      exact_brand_color_copy_forbidden: true,
      layout_identity_copy_forbidden: true,
      selectors_discarded: true,
    },
    outcome: blockers.length > 0 ? "WEBSITE_CSS_REFERENCE_BLOCKED" : "WEBSITE_CSS_REFERENCE_READY",
    raw_css_quarantine: {
      raw_css_stored: false,
      raw_css_used_for_generation: false,
      source_hash: stablePreviewHash(`${sourceUrl}\n${cssText}`),
      source_url_recorded_only: Boolean(sourceUrl),
    },
  };
}

function buildDesignDnaOutcome(promptOutcome: any, referenceUploadOutcome: any, websiteCssReferenceOutcome: any) {
  const designPacket = promptOutcome.design_packet ?? null;
  const hasDerivedPacket = Boolean(designPacket?.design_packet_hash);
  const designDnaCore = hasDerivedPacket
    ? {
        interaction_model: designPacket.accessibility_notes?.includes("keyboard navigation must be first-class")
          ? "keyboard_first_preview_controls"
          : designPacket.accessibility_notes?.includes("mobile controls must remain tappable")
            ? "touch_first_preview_controls"
            : "click_and_review_preview_controls",
        product_domain_motif: designPacket.project_specific_motif,
        rhythm: designPacket.visual_direction?.includes("dense console workbench")
          ? "dense_evidence_panel_rhythm"
          : designPacket.visual_direction?.includes("editorial spacious hierarchy")
            ? "spacious_editorial_review_rhythm"
            : "balanced_preview_workbench_rhythm",
        spatial_system: designPacket.constraints?.includes("preserve dense workbench utility")
          ? "three_column_dense_workbench"
          : designPacket.constraints?.includes("support mobile responsive proof")
            ? "responsive_single_to_multi_column_review"
            : "bounded_preview_shell_grid",
        typography: designPacket.visual_direction?.includes("editorial spacious hierarchy")
          ? "editorial_readable_hierarchy"
          : "technical_workbench_hierarchy",
        visual_hierarchy: designPacket.intent?.includes("increase perceived product quality")
          ? "premium_primary_action_with_evidence_support"
          : designPacket.intent?.includes("improve mobile usability")
            ? "mobile_first_section_hierarchy"
            : "prompt_derived_review_hierarchy",
      }
    : {
        interaction_model: "generic_preview_only_static_review",
        product_domain_motif: "generic_preview_shell",
        rhythm: "generic_balanced_spacing",
        spatial_system: "generic_three_panel_shell",
        typography: "generic_system_type",
        visual_hierarchy: "generic_heading_cards",
      };
  const sourceRefs = [
    promptOutcome.outcome === "DESIGN_PACKET_PREVIEW" ? "messy_prompt" : null,
    referenceUploadOutcome.outcome === "REFERENCE_METADATA_STAGED" ? "reference_upload" : null,
    websiteCssReferenceOutcome.outcome === "WEBSITE_CSS_REFERENCE_READY"
      ? "website_css_reference_policy"
      : null,
  ].filter(Boolean);
  const domainMotifAnchors = hasDerivedPacket
    ? ["Source Proxy", "Design Studio", "design sandbox", "visual review"]
    : [];
  const designDnaHash = sha256Json({
    design_dna: designDnaCore,
    design_packet_hash: designPacket?.design_packet_hash ?? "none",
    domain_motif_anchors: domainMotifAnchors,
  });

  return {
    consumption_state: {
      consumer_event_id: "blocked_until_coder_packet_or_design_library_consumer",
      consumed_by_downstream: false,
      unconsumed_designdna_blocks_go: true,
    },
    conflict_resolution: [
      "user_explicit_request",
      "project_obsidian_brief",
      "spiritos_dna",
      "reference_dna",
      "generic_defaults",
    ],
    design_dna: {
      anti_copy_constraints: [
        "no raw CSS selectors",
        "no direct class name copy",
        "no exact brand color copy",
        "no 1:1 layout identity copy",
      ],
      color_tokens: ["spirit_accent", "chalk", "surface_glass"],
      component_density: "workbench_dense",
      design_packet_hash: designPacket?.design_packet_hash ?? null,
      domain_motif_anchors: domainMotifAnchors,
      designdna_hash: designDnaHash,
      dna_id: `designdna-${designDnaHash.slice(0, 12)}`,
      generic_fallback_passes: false,
      interaction_model: designDnaCore.interaction_model,
      layout_rhythm: "three_panel_preview_workbench",
      motion_policy: "quiet_state_transitions_only",
      normalization_strength: hasDerivedPacket ? "prompt_derived" : "weak_generic_fallback",
      product_domain_motif: designDnaCore.product_domain_motif,
      radius_scale: ["sm", "md", "lg"],
      responsive_behavior: "desktop_mobile_required_before_go",
      rhythm: designDnaCore.rhythm,
      shadow_policy: "subtle_depth_only",
      source_refs: sourceRefs,
      spacing_scale: ["2", "3", "4", "6"],
      spatial_system: designDnaCore.spatial_system,
      surface_policy: "glass_panel_on_spirit_background",
      type_scale: ["xs", "sm", "base", "lg", "2xl"],
      typography: designDnaCore.typography,
      visual_hierarchy: designDnaCore.visual_hierarchy,
    },
    memory_bridge: {
      obsidian_read_refs_consumed: promptOutcome.outcome === "DESIGN_PACKET_PREVIEW",
      obsidian_writeback_authority: false,
      visual_refs_consumed: referenceUploadOutcome.outcome === "REFERENCE_METADATA_STAGED",
      visual_index_write_authority: false,
    },
    outcome: "DESIGN_DNA_NORMALIZED_PREVIEW",
  };
}

function buildDesignLibraryOutcome(designDnaOutcome: any) {
  const sourceHash = stablePreviewHash(JSON.stringify(designDnaOutcome.design_dna.source_refs));

  return {
    dedupe: {
      duplicate_strategy: "same_source_hash_creates_new_version_preview",
      source_hash: sourceHash,
      version: 1,
    },
    library_record: {
      design_dna_id: designDnaOutcome.design_dna.dna_id,
      library_record_id: "design-library-preview-local",
      source_hash: sourceHash,
      source_refs: designDnaOutcome.design_dna.source_refs,
      status: "preview_only_not_persisted",
    },
    outcome: "DESIGN_LIBRARY_PREVIEW_RECORD",
    read_contract: {
      queryable_by: ["source_hash", "design_dna_id", "target_surface"],
      read_authority: true,
      returns_preview_records_only: true,
    },
    write_guard: {
      durable_store_write_authority: false,
      memory_promotion_authority: false,
      obsidian_writeback_authority: false,
      requires_human_approval_for_persistence: true,
    },
  };
}

function buildCoderPacketOutcome(promptOutcome: any, designDnaOutcome: any) {
  const targetFiles = ["src/app/coding/design-demo/page.tsx"];
  const allowedFiles = ["src/app/coding/design-demo/page.tsx"];
  const designPacketHash = promptOutcome.design_packet?.design_packet_hash ?? "preview-shell-local";
  const coderPacketHash = stablePreviewHash(
    JSON.stringify({
      design_packet_hash: designPacketHash,
      design_packet_id: promptOutcome.design_packet?.design_packet_id ?? "preview-shell-local",
      target_files: targetFiles,
      dna_id: designDnaOutcome.design_dna.dna_id,
    }),
  );

  return {
    coder_packet: {
      accessibility_rules: ["visible focus states", "semantic headings", "no text overlap"],
      allowed_files: allowedFiles,
      coder_packet_hash: coderPacketHash,
      design_packet_hash: designPacketHash,
      component_rules: ["preserve preview-only guardrails", "show design and coder packet panels"],
      consumer_event_id: "blocked_until_sandbox_apply_approval",
      consumer_subsystem: "design_demo_sandbox_apply",
      css_rules: ["use project tokens", "do not copy raw CSS selectors"],
      forbidden_files: ["docs/evidence/**", ".env*", ".spirit-backups/**"],
      production_apply_authority: false,
      responsive_rules: ["desktop and mobile verification required before GO"],
      sandbox_apply_target: "/coding/design-demo",
      target_files: targetFiles,
      verification_commands: [
        "timeout 120s npx vitest run src/components/design-demo/SpiritDesignDemo.test.tsx --reporter=dot --pool=threads --environment=node",
      ],
      visual_pass_criteria: [
        "sandbox page visible at /coding/design-demo",
        "applied design packet is visible",
        "production routes remain untouched",
      ],
    },
    fake_go_guard: {
      coder_packet_exists_is_go: false,
      design_packet_exists_is_go: false,
      requires_named_consumer: true,
    },
    outcome: "CODER_PACKET_PREVIEW_READY",
  };
}

function buildAntiTemplateOriginalityOutcome(input: DesignStudioPreviewRequest) {
  const probe = input.originality_probe;
  const prompt = normalizeText(input.prompt);
  const description = normalizeText(probe?.generated_description);
  const combinedText = `${prompt} ${description}`;
  const projectMotif = probe?.project_motif?.trim() ?? "";
  const classNames = probe?.class_names?.map((className) => className.trim()).filter(Boolean) ?? [];
  const lowerClassNames = classNames.map((className) => className.toLowerCase());
  const blockers: string[] = [];

  const genericRules = [
    ["generic_purple_blue_gradient", combinedText.includes("purple") && combinedText.includes("blue gradient")],
    ["same_three_cards_pattern", combinedText.includes("three cards") || combinedText.includes("3 cards")],
    ["hero_left_cards_right_pattern", combinedText.includes("hero left") || combinedText.includes("cards right")],
    ["decorative_blob_without_reason", combinedText.includes("decorative blob") || combinedText.includes("gradient blob")],
    ["missing_project_motif", Boolean(probe) && !projectMotif],
  ] as const;

  for (const [rule, matched] of genericRules) {
    if (matched) {
      blockers.push(rule);
    }
  }

  if (probe?.raw_css_supplied) {
    blockers.push("raw_css_clone_or_ingest_blocked");
  }
  if (probe?.copied_brand_identity) {
    blockers.push("copied_brand_identity_blocked");
  }
  if (probe?.reference_similarity === "direct_clone") {
    blockers.push("direct_reference_clone_blocked");
  }
  if (
    lowerClassNames.some((className) =>
      ["brandhero", "herogradient", "glasscard", "aistudiocard", "googlegemini"].includes(className),
    )
  ) {
    blockers.push("copied_or_template_classname_blocked");
  }

  return {
    blockers,
    checks: {
      class_names_checked_as_metadata_only: true,
      copied_brand_identity_rejected: true,
      direct_clone_rejected: true,
      generic_slop_patterns_rejected: true,
      inspired_not_copied_allowed: true,
      raw_css_ingestion_performed: false,
    },
    consumer_event_id: "blocked_until_design_critic_or_sandbox_verifier_consumes_originality_result",
    outcome:
      blockers.length > 0
        ? "ANTI_TEMPLATE_ORIGINALITY_BLOCKED"
        : "ANTI_TEMPLATE_ORIGINALITY_APPROVED_PREVIEW",
    trace_id: "anti-template-originality-preview-trace",
  };
}

function buildDesignCriticOutcome(input: DesignStudioPreviewRequest, antiTemplateOutcome: any) {
  const probe = input.critic_probe;
  const screenshotRefs = probe?.screenshot_refs?.map((ref) => ref.trim()).filter(Boolean) ?? [];
  const repairCount = probe?.repair_count ?? 0;
  const hierarchyScore = probe?.hierarchy_score ?? 0;
  const spacingScore = probe?.spacing_score ?? 0;
  const contrastStatus = probe?.contrast_status ?? "unknown";
  const mobileStatus = probe?.mobile_status ?? "unknown";
  const originalityStatus =
    probe?.originality_status ??
    (antiTemplateOutcome.outcome === "ANTI_TEMPLATE_ORIGINALITY_BLOCKED" ? "fail" : "unknown");
  const antiTemplateStatus =
    probe?.anti_template_status ??
    (antiTemplateOutcome.outcome === "ANTI_TEMPLATE_ORIGINALITY_BLOCKED" ? "fail" : "unknown");
  const blockers: string[] = [];
  const repairInstructions: string[] = [];

  if (screenshotRefs.length === 0) {
    blockers.push("missing_screenshot_refs");
  }
  if (repairCount > 2) {
    blockers.push("max_two_repairs_exceeded");
  }
  if (hierarchyScore < 80) {
    repairInstructions.push("tighten visual hierarchy before approval");
  }
  if (spacingScore < 80) {
    repairInstructions.push("repair spacing rhythm and mobile stack density");
  }
  if (contrastStatus !== "pass") {
    repairInstructions.push("verify text/background contrast before approval");
  }
  if (mobileStatus !== "pass") {
    repairInstructions.push("rerun mobile screenshot proof before approval");
  }
  if (originalityStatus !== "pass" || antiTemplateStatus !== "pass") {
    repairInstructions.push("resolve originality and anti-template blockers before approval");
  }

  const needsRepair = repairInstructions.length > 0 || blockers.length > 0;

  return {
    blockers,
    critic_packet: {
      anti_template_status: antiTemplateStatus,
      contrast_status: contrastStatus,
      critic_packet_id: "design-critic-preview-local",
      design_packet_id: "messy-prompt-preview-local",
      failed_probe: probe?.failed_probe ?? (blockers[0] || null),
      hierarchy_score: hierarchyScore,
      mobile_status: mobileStatus,
      originality_status: originalityStatus,
      repair_count: repairCount,
      repair_instructions: repairInstructions,
      screenshot_refs: screenshotRefs,
      spacing_score: spacingScore,
    },
    fake_go_guard: {
      critic_packet_exists_is_go: false,
      missing_screenshot_proof_blocks_approval: true,
      model_says_fixed_is_go: false,
      repair_requires_reverification: true,
    },
    outcome:
      blockers.length > 0
        ? "DESIGN_CRITIC_BLOCKED"
        : needsRepair
          ? "DESIGN_CRITIC_REPAIR_REQUIRED"
          : "DESIGN_CRITIC_APPROVED_PREVIEW",
    repair_loop: {
      max_repairs: 2,
      repair_count: repairCount,
      repair_write_authority: false,
      requires_reverification_after_repair: needsRepair,
    },
    trace_id: "design-critic-preview-trace",
  };
}

export async function POST(request?: Request) {
  const input = await readPreviewRequest(request);
  const identity = requestIdentity(input);
  if (input.model_probe?.enabled && input.model_probe.require_source && !hasModelProbeSource(input)) {
    return modelProbeBlockedResponse(input, identity, "MISSING_SOURCE_BLOCKED_ENV");
  }
  const promptOutcome = buildPromptOutcome(input, identity);
  const noModelDesignPacketHash = promptOutcome.design_packet?.design_packet_hash ?? null;
  const modelInvocation =
    input.model_probe?.enabled && promptOutcome.design_packet
      ? await invokeOllamaDesignGuidance(input, promptOutcome.design_packet, identity)
      : null;
  if (input.model_probe?.enabled && modelInvocation && !modelInvocation.ok) {
    return modelProbeBlockedResponse(
      input,
      identity,
      String(modelInvocation.failure_mode || "MODEL_INVOCATION_BLOCKED_ENV"),
    );
  }
  if (modelInvocation?.ok && promptOutcome.design_packet) {
    promptOutcome.design_packet = applyModelGuidanceToDesignPacket(
      promptOutcome.design_packet,
      modelInvocation,
    );
  }
  const referenceUploadOutcome = buildReferenceUploadOutcome(input);
  const websiteCssReferenceOutcome = buildWebsiteCssReferenceOutcome(input);
  const designDnaOutcome = buildDesignDnaOutcome(
    promptOutcome,
    referenceUploadOutcome,
    websiteCssReferenceOutcome,
  );
  const designLibraryOutcome = buildDesignLibraryOutcome(designDnaOutcome);
  const coderPacketOutcome = buildCoderPacketOutcome(promptOutcome, designDnaOutcome);
  const antiTemplateOriginalityOutcome = buildAntiTemplateOriginalityOutcome(input);
  const designCriticOutcome = buildDesignCriticOutcome(input, antiTemplateOriginalityOutcome);
  const writebackPreview =
    input.writeback_preview?.content === undefined
      ? { state: "not_requested" as const }
      : await persistDesignPreview({
          content: input.writeback_preview.content,
        });

  return Response.json({
    advisory_only: true,
    apply_authority: false,
    approval_authority: false,
    commit_authority: false,
    design_studio_route: "/coding/design-studio",
    endpoint: "/v1/coding/design-studio/preview",
    fake_go_guard: {
      design_packet_exists_is_go: false,
      preview_opens_is_go: false,
      required_downstream_consumption: "accepted_design_packet_to_named_coder_packet_consumer",
      unconsumed_packet_blocks_go: true,
    },
    hidden_execution_started: false,
    memory_write_authority: false,
    model_call_made: Boolean(modelInvocation?.ok),
    model_invocation_result: modelInvocation,
    no_model_design_packet_hash: noModelDesignPacketHash,
    original_user_prompt_hash: identity.original_user_prompt_hash,
    provider_call_made: Boolean(modelInvocation?.ok),
    push_authority: false,
    request_id: identity.request_id,
    raw_css_ingest_authority: false,
    sandbox_apply_authority: false,
    shell: {
      component: "src/components/coding/DesignStudioShell.tsx",
      page: "src/app/coding/design-studio/page.tsx",
      status: "preview_shell_ready",
    },
    trace_id: identity.trace_id,
    messy_prompt_result: promptOutcome,
    reference_upload_result: referenceUploadOutcome,
    website_css_reference_result: websiteCssReferenceOutcome,
    design_dna_result: designDnaOutcome,
    design_library_result: designLibraryOutcome,
    coder_packet_result: coderPacketOutcome,
    anti_template_originality_result: antiTemplateOriginalityOutcome,
    design_critic_result: designCriticOutcome,
    approved_design_memory_writeback: {
      approved_destination: "data/design-vault/design-memory/<YYYY-MM-DD>/<design_run_id>.md",
      preview_only_no_write: true,
      required_gate:
        "verified_run_with_explicit_approval_desktop_mobile_originality_critic_and_no_fake_go",
      write_authority: false,
    },
    approval_preview: writebackPreview,
    preview_packet: {
      consumer_event_id: "blocked_until_packet_acceptance",
      design_packet_id: "preview-shell-local",
      obsidian_context_refs: [],
      original_user_prompt_hash: identity.original_user_prompt_hash,
      request_id: identity.request_id,
      schema_version: "design_studio_preview_shell_v1",
      target_surface: "/coding/design-studio",
      trace_id: identity.trace_id,
    },
    bounded_coder_packet: {
      ...coderPacketOutcome.coder_packet,
      blocked_until_human_accepts_design_packet: true,
    },
  });
}
