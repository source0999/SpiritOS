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
  reference_upload?: {
    file_name?: string;
    license_state?: string;
    mime_type?: string;
    size_bytes?: number;
    source_type?: string;
  };
  target_surface?: string;
  website_css_reference?: {
    adapter_name?: string;
    css_text?: string;
    source_url?: string;
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

function buildPromptOutcome(input: DesignStudioPreviewRequest) {
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
    return {
      design_packet: {
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
        design_packet_id: "messy-prompt-preview-local",
        obsidian_context_refs: [],
        project_specific_motif: "SpiritOS preview workbench",
        style_family_blend: ["SpiritOS glass console", "dense product workbench"],
        target_surface: targetSurface,
        trace_id: "messy-prompt-preview-trace",
        visual_pass_criteria: [
          "clear preview/apply boundary",
          "mobile and desktop layout remain scannable",
          "no Google AI Studio generic shell",
        ],
      },
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
  const sourceRefs = [
    promptOutcome.outcome === "DESIGN_PACKET_PREVIEW" ? "messy_prompt" : null,
    referenceUploadOutcome.outcome === "REFERENCE_METADATA_STAGED" ? "reference_upload" : null,
    websiteCssReferenceOutcome.outcome === "WEBSITE_CSS_REFERENCE_READY"
      ? "website_css_reference_policy"
      : null,
  ].filter(Boolean);

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
      dna_id: "designdna-preview-local",
      layout_rhythm: "three_panel_preview_workbench",
      motion_policy: "quiet_state_transitions_only",
      radius_scale: ["sm", "md", "lg"],
      responsive_behavior: "desktop_mobile_required_before_go",
      shadow_policy: "subtle_depth_only",
      source_refs: sourceRefs,
      spacing_scale: ["2", "3", "4", "6"],
      surface_policy: "glass_panel_on_spirit_background",
      type_scale: ["xs", "sm", "base", "lg", "2xl"],
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
  const targetFiles = ["src/components/coding/DesignStudioShell.tsx"];
  const allowedFiles = [
    "src/app/coding/design-studio/page.tsx",
    "src/components/coding/DesignStudioShell.tsx",
    "src/app/v1/coding/design-studio/preview/route.ts",
  ];
  const coderPacketHash = stablePreviewHash(
    JSON.stringify({
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
      component_rules: ["preserve preview-only guardrails", "show design and coder packet panels"],
      consumer_event_id: "blocked_until_sandbox_apply_approval",
      consumer_subsystem: "design_studio_preview_ui",
      css_rules: ["use project tokens", "do not copy raw CSS selectors"],
      forbidden_files: ["docs/evidence/**", ".env*", ".spirit-backups/**"],
      responsive_rules: ["desktop and mobile verification required before GO"],
      target_files: targetFiles,
      verification_commands: [
        "timeout 120s npx vitest run src/app/v1/coding/design-studio/preview/__tests__/route.test.ts --reporter=dot --pool=threads --environment=node",
        "timeout 120s npx vitest run src/components/coding/__tests__/design-studio-shell.test.tsx --reporter=dot --pool=threads --environment=node",
      ],
      visual_pass_criteria: [
        "design packet visible",
        "coder packet visible",
        "apply remains locked",
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
  const promptOutcome = buildPromptOutcome(input);
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
    model_call_made: false,
    provider_call_made: false,
    push_authority: false,
    raw_css_ingest_authority: false,
    sandbox_apply_authority: false,
    shell: {
      component: "src/components/coding/DesignStudioShell.tsx",
      page: "src/app/coding/design-studio/page.tsx",
      status: "preview_shell_ready",
    },
    messy_prompt_result: promptOutcome,
    reference_upload_result: referenceUploadOutcome,
    website_css_reference_result: websiteCssReferenceOutcome,
    design_dna_result: designDnaOutcome,
    design_library_result: designLibraryOutcome,
    coder_packet_result: coderPacketOutcome,
    anti_template_originality_result: antiTemplateOriginalityOutcome,
    design_critic_result: designCriticOutcome,
    preview_packet: {
      consumer_event_id: "blocked_until_packet_acceptance",
      design_packet_id: "preview-shell-local",
      obsidian_context_refs: [],
      schema_version: "design_studio_preview_shell_v1",
      target_surface: "/coding/design-studio",
      trace_id: "preview-shell-trace",
    },
    bounded_coder_packet: {
      allowed_files: [
        "src/app/coding/design-studio/page.tsx",
        "src/components/coding/DesignStudioShell.tsx",
        "src/app/v1/coding/design-studio/preview/route.ts",
      ],
      blocked_until_human_accepts_design_packet: true,
      forbidden_files: ["docs/evidence/**", ".env*", ".spirit-backups/**"],
      target_files: ["src/components/coding/DesignStudioShell.tsx"],
      verification_commands: [
        "npm test -- src/app/v1/coding/design-studio/preview/__tests__/route.test.ts",
      ],
    },
  });
}
