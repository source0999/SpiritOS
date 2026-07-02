/// <reference types="vitest/globals" />

import { POST } from "../route";

describe("coding design studio preview route", () => {
  it("returns a preview-only shell packet with all write paths disabled", async () => {
    const response = await POST();

    await expect(response.json()).resolves.toMatchObject({
      advisory_only: true,
      apply_authority: false,
      approval_authority: false,
      commit_authority: false,
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
    });
    expect(response.status).toBe(200);
  });

  it("rejects preview-open and packet-exists fake GO states", async () => {
    const response = await POST();
    const payload = await response.json();

    expect(payload.fake_go_guard).toMatchObject({
      design_packet_exists_is_go: false,
      preview_opens_is_go: false,
      unconsumed_packet_blocks_go: true,
    });
    expect(payload.preview_packet).toMatchObject({
      consumer_event_id: "blocked_until_packet_acceptance",
      schema_version: "design_studio_preview_shell_v1",
      target_surface: "/coding/design-studio",
    });
    expect(payload.bounded_coder_packet).toMatchObject({
      blocked_until_human_accepts_design_packet: true,
      target_files: ["src/components/coding/DesignStudioShell.tsx"],
    });
  });

  it("turns an actionable messy prompt with a target into a typed design packet preview", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        prompt: "make it less Google AI Studio",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.messy_prompt_result).toMatchObject({
      outcome: "DESIGN_PACKET_PREVIEW",
      reason: "actionable_messy_prompt_with_target",
      design_packet: {
        design_packet_id: "messy-prompt-preview-local",
        target_surface: "/coding/design-studio",
        trace_id: "messy-prompt-preview-trace",
        coder_packet: {
          allowed_files: ["src/components/coding/DesignStudioShell.tsx"],
          target_files: ["src/components/coding/DesignStudioShell.tsx"],
        },
      },
    });
    expect(payload.messy_prompt_result.design_packet.style_family_blend).toContain(
      "SpiritOS glass console",
    );
  });

  it("asks for a target instead of guessing for vague prompts", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({ prompt: "make it clean" }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.messy_prompt_result).toEqual({
      design_packet: null,
      outcome: "ASK_CLARIFY_TARGET",
      reason: "target_surface_required",
    });
    expect(payload.provider_call_made).toBe(false);
    expect(payload.model_call_made).toBe(false);
  });

  it("stages safe reference metadata without generation or memory promotion", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        reference_upload: {
          file_name: "owned-dashboard-reference.png",
          license_state: "owned",
          mime_type: "image/png",
          size_bytes: 420000,
          source_type: "uploaded_file",
        },
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.reference_upload_result).toMatchObject({
      blockers: [],
      outcome: "REFERENCE_METADATA_STAGED",
      reference_metadata: {
        file_name: "owned-dashboard-reference.png",
        license_state: "owned",
        mime_type: "image/png",
        reference_id: "reference-upload-preview-local",
        source_use_policy: "inspiration_only_no_1_to_1_copy",
      },
      staged_for_generation: false,
      visual_index_adapter: {
        adapter_status: "preview_contract_only",
        memory_promotion_authority: false,
        requires_downstream_consumption: true,
      },
    });
  });

  it("blocks unsafe reference metadata and authority hard stops", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        reference_upload: {
          file_name: "borrowed.css",
          license_state: "unknown",
          mime_type: "text/css",
          size_bytes: 1200,
          source_type: "raw_css",
        },
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.reference_upload_result).toMatchObject({
      outcome: "REFERENCE_UPLOAD_BLOCKED",
      reference_metadata: null,
      staged_for_generation: false,
    });
    expect(payload.reference_upload_result.blockers).toEqual(
      expect.arrayContaining([
        "unsupported_mime_type",
        "license_or_source_uncertain",
        "authority_hard_stop_required",
      ]),
    );
    expect(payload.raw_css_ingest_authority).toBe(false);
  });

  it("blocks website URL and raw CSS reference intake behind authority hard stops", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        website_css_reference: {
          adapter_name: "wallace-cli",
          css_text: ".brandHero { color: #123456; }",
          source_url: "https://example.invalid/reference",
        },
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.website_css_reference_result).toMatchObject({
      external_tool_adapter: {
        adapter_name: "wallace-cli",
        install_authority: false,
        local_only: false,
        output_contract: "DesignDNA_or_referenceDNA_only",
      },
      no_copy_policy: {
        class_names_discarded: true,
        direct_css_clone_forbidden: true,
        exact_brand_color_copy_forbidden: true,
        layout_identity_copy_forbidden: true,
        selectors_discarded: true,
      },
      outcome: "WEBSITE_CSS_REFERENCE_BLOCKED",
      raw_css_quarantine: {
        raw_css_stored: false,
        raw_css_used_for_generation: false,
        source_url_recorded_only: true,
      },
    });
    expect(payload.website_css_reference_result.blockers).toEqual(
      expect.arrayContaining([
        "external_url_scrape_requires_human_approval",
        "raw_css_ingestion_requires_human_approval",
        "external_tool_install_or_adapter_requires_human_approval",
      ]),
    );
    expect(payload.raw_css_ingest_authority).toBe(false);
  });

  it("allows an empty local quarantine adapter contract without ingesting CSS", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        website_css_reference: {
          adapter_name: "local_quarantine_adapter",
        },
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.website_css_reference_result).toMatchObject({
      blockers: [],
      external_tool_adapter: {
        adapter_name: "local_quarantine_adapter",
        install_authority: false,
        local_only: true,
      },
      outcome: "WEBSITE_CSS_REFERENCE_READY",
      raw_css_quarantine: {
        raw_css_stored: false,
        raw_css_used_for_generation: false,
        source_url_recorded_only: false,
      },
    });
  });

  it("normalizes prompt and reference inputs into preview DesignDNA without writeback", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        prompt: "make it modern",
        reference_upload: {
          file_name: "owned-dashboard-reference.webp",
          license_state: "approved_reference",
          mime_type: "image/webp",
          size_bytes: 220000,
          source_type: "uploaded_file",
        },
        target_surface: "/coding/design-studio",
        website_css_reference: {
          adapter_name: "local_quarantine_adapter",
        },
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.design_dna_result).toMatchObject({
      conflict_resolution: [
        "user_explicit_request",
        "project_obsidian_brief",
        "spiritos_dna",
        "reference_dna",
        "generic_defaults",
      ],
      consumption_state: {
        consumed_by_downstream: false,
        consumer_event_id: "blocked_until_coder_packet_or_design_library_consumer",
        unconsumed_designdna_blocks_go: true,
      },
      design_dna: {
        component_density: "workbench_dense",
        dna_id: "designdna-preview-local",
        layout_rhythm: "three_panel_preview_workbench",
        responsive_behavior: "desktop_mobile_required_before_go",
      },
      memory_bridge: {
        obsidian_read_refs_consumed: true,
        obsidian_writeback_authority: false,
        visual_refs_consumed: true,
        visual_index_write_authority: false,
      },
      outcome: "DESIGN_DNA_NORMALIZED_PREVIEW",
    });
    expect(payload.design_dna_result.design_dna.source_refs).toEqual([
      "messy_prompt",
      "reference_upload",
      "website_css_reference_policy",
    ]);
    expect(payload.design_dna_result.design_dna.anti_copy_constraints).toEqual(
      expect.arrayContaining([
        "no raw CSS selectors",
        "no direct class name copy",
        "no exact brand color copy",
        "no 1:1 layout identity copy",
      ]),
    );
  });

  it("creates a preview-only design library record without durable writes", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        prompt: "make it modern",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.design_library_result).toMatchObject({
      dedupe: {
        duplicate_strategy: "same_source_hash_creates_new_version_preview",
        version: 1,
      },
      library_record: {
        design_dna_id: "designdna-preview-local",
        library_record_id: "design-library-preview-local",
        source_refs: ["messy_prompt"],
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
    });
    expect(payload.design_library_result.library_record.source_hash).toMatch(/^preview_[0-9a-f]{8}$/);
  });

  it("converts preview design context into a bounded coder packet without apply authority", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        prompt: "make it modern",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.coder_packet_result).toMatchObject({
      coder_packet: {
        accessibility_rules: ["visible focus states", "semantic headings", "no text overlap"],
        allowed_files: [
          "src/app/coding/design-studio/page.tsx",
          "src/components/coding/DesignStudioShell.tsx",
          "src/app/v1/coding/design-studio/preview/route.ts",
        ],
        component_rules: [
          "preserve preview-only guardrails",
          "show design and coder packet panels",
        ],
        consumer_event_id: "blocked_until_sandbox_apply_approval",
        consumer_subsystem: "design_studio_preview_ui",
        css_rules: ["use project tokens", "do not copy raw CSS selectors"],
        forbidden_files: ["docs/evidence/**", ".env*", ".spirit-backups/**"],
        responsive_rules: ["desktop and mobile verification required before GO"],
        target_files: ["src/components/coding/DesignStudioShell.tsx"],
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
    });
    expect(payload.coder_packet_result.coder_packet.coder_packet_hash).toMatch(/^preview_[0-9a-f]{8}$/);
    expect(payload.sandbox_apply_authority).toBe(false);
    expect(payload.apply_authority).toBe(false);
  });

  it("blocks generic template and clone signals before design approval", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        originality_probe: {
          class_names: ["brandHero", "glassCard"],
          copied_brand_identity: true,
          generated_description:
            "Purple and blue gradient hero left with three cards right and decorative blobs.",
          raw_css_supplied: true,
          reference_similarity: "direct_clone",
        },
        prompt: "make a generic purple blue gradient with three cards",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.anti_template_originality_result).toMatchObject({
      checks: {
        class_names_checked_as_metadata_only: true,
        copied_brand_identity_rejected: true,
        direct_clone_rejected: true,
        generic_slop_patterns_rejected: true,
        raw_css_ingestion_performed: false,
      },
      outcome: "ANTI_TEMPLATE_ORIGINALITY_BLOCKED",
      trace_id: "anti-template-originality-preview-trace",
    });
    expect(payload.anti_template_originality_result.blockers).toEqual(
      expect.arrayContaining([
        "generic_purple_blue_gradient",
        "same_three_cards_pattern",
        "hero_left_cards_right_pattern",
        "decorative_blob_without_reason",
        "missing_project_motif",
        "raw_css_clone_or_ingest_blocked",
        "copied_brand_identity_blocked",
        "direct_reference_clone_blocked",
        "copied_or_template_classname_blocked",
      ]),
    );
    expect(payload.raw_css_ingest_authority).toBe(false);
  });

  it("allows inspired-not-copied originality metadata when project motif is present", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        originality_probe: {
          class_names: ["spiritWorkbench", "designTraceRail"],
          generated_description:
            "A dense SpiritOS preview workbench with trace rails and bounded apply proof.",
          project_motif: "SpiritOS preview workbench",
          reference_similarity: "inspired",
        },
        prompt: "make it feel premium and not generic",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.anti_template_originality_result).toMatchObject({
      blockers: [],
      checks: {
        inspired_not_copied_allowed: true,
        raw_css_ingestion_performed: false,
      },
      consumer_event_id:
        "blocked_until_design_critic_or_sandbox_verifier_consumes_originality_result",
      outcome: "ANTI_TEMPLATE_ORIGINALITY_APPROVED_PREVIEW",
    });
  });

  it("blocks design critic approval when screenshot proof is missing", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        critic_probe: {
          anti_template_status: "pass",
          contrast_status: "pass",
          hierarchy_score: 92,
          mobile_status: "pass",
          originality_status: "pass",
          repair_count: 0,
          spacing_score: 90,
        },
        prompt: "make it modern",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.design_critic_result).toMatchObject({
      critic_packet: {
        anti_template_status: "pass",
        contrast_status: "pass",
        failed_probe: "missing_screenshot_refs",
        hierarchy_score: 92,
        mobile_status: "pass",
        originality_status: "pass",
        repair_count: 0,
        screenshot_refs: [],
        spacing_score: 90,
      },
      fake_go_guard: {
        critic_packet_exists_is_go: false,
        missing_screenshot_proof_blocks_approval: true,
        model_says_fixed_is_go: false,
      },
      outcome: "DESIGN_CRITIC_BLOCKED",
    });
    expect(payload.design_critic_result.blockers).toContain("missing_screenshot_refs");
  });

  it("blocks bounded repair after two repair attempts", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        critic_probe: {
          contrast_status: "fail",
          failed_probe: "mobile_contrast_regression",
          hierarchy_score: 74,
          mobile_status: "fail",
          repair_count: 3,
          screenshot_refs: ["plan10-desktop-1440x900-design-demo", "plan10-mobile-390x844-design-demo"],
          spacing_score: 78,
        },
        prompt: "make it modern",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.design_critic_result).toMatchObject({
      outcome: "DESIGN_CRITIC_BLOCKED",
      repair_loop: {
        max_repairs: 2,
        repair_count: 3,
        repair_write_authority: false,
        requires_reverification_after_repair: true,
      },
    });
    expect(payload.design_critic_result.blockers).toContain("max_two_repairs_exceeded");
    expect(payload.design_critic_result.critic_packet.repair_instructions).toEqual(
      expect.arrayContaining([
        "tighten visual hierarchy before approval",
        "repair spacing rhythm and mobile stack density",
        "verify text/background contrast before approval",
        "rerun mobile screenshot proof before approval",
      ]),
    );
  });

  it("approves critic preview only when screenshots and quality checks pass", async () => {
    const request = new Request("http://localhost/v1/coding/design-studio/preview", {
      body: JSON.stringify({
        critic_probe: {
          anti_template_status: "pass",
          contrast_status: "pass",
          hierarchy_score: 94,
          mobile_status: "pass",
          originality_status: "pass",
          repair_count: 1,
          screenshot_refs: ["plan10-desktop-1440x900-design-demo", "plan10-mobile-390x844-design-demo"],
          spacing_score: 91,
        },
        originality_probe: {
          generated_description: "SpiritOS preview workbench with trace rails.",
          project_motif: "SpiritOS preview workbench",
          reference_similarity: "inspired",
        },
        prompt: "make it modern",
        target_surface: "/coding/design-studio",
      }),
      method: "POST",
    });
    const response = await POST(request);
    const payload = await response.json();

    expect(payload.design_critic_result).toMatchObject({
      blockers: [],
      critic_packet: {
        anti_template_status: "pass",
        contrast_status: "pass",
        critic_packet_id: "design-critic-preview-local",
        design_packet_id: "messy-prompt-preview-local",
        hierarchy_score: 94,
        mobile_status: "pass",
        originality_status: "pass",
        repair_count: 1,
        repair_instructions: [],
        screenshot_refs: ["plan10-desktop-1440x900-design-demo", "plan10-mobile-390x844-design-demo"],
        spacing_score: 91,
      },
      outcome: "DESIGN_CRITIC_APPROVED_PREVIEW",
      repair_loop: {
        max_repairs: 2,
        repair_count: 1,
        repair_write_authority: false,
        requires_reverification_after_repair: false,
      },
    });
  });

  it("does not write approved design memory during preview-only requests", async () => {
    const response = await POST(
      new Request("http://localhost/v1/coding/design-studio/preview", {
        body: JSON.stringify({
          prompt: "make it modern",
          target_surface: "/coding/design-studio",
        }),
        method: "POST",
      }),
    );
    const payload = await response.json();

    expect(payload.memory_write_authority).toBe(false);
    expect(payload.approved_design_memory_writeback).toEqual({
      approved_destination: "data/design-vault/design-memory/<YYYY-MM-DD>/<design_run_id>.md",
      preview_only_no_write: true,
      required_gate:
        "verified_run_with_explicit_approval_desktop_mobile_originality_critic_and_no_fake_go",
      write_authority: false,
    });
  });
});
