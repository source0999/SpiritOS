import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  getReadOnlyMapData,
  readOnlyMapEndpointAllowlist,
} from "../read-only-map-data";
import { getCartographerLiveState } from "../cartographer-live-state";
import {
  buildCartographerBranchPushPreview,
  buildCartographerCommitPreview,
  buildCartographerDirtyTreePreview,
  cartographerDefaultProjectCardPreviews,
  cartographerForbiddenPreviewControlActions,
  cartographerMapApprovalTokenFields,
  cartographerMapAuthorityDenials,
  cartographerMapLiveStateFields,
  cartographerMapOperationalSections,
  cartographerMapOperatorDecisionPacketFields,
  cartographerMapOperatorQuestions,
  cartographerMapQueuePanelFields,
  cartographerMapReadOnlySourceFields,
  cartographerMapReceiptEvidenceFields,
  cartographerMapReviewOnlyReadinessFields,
  cartographerMapStopControlFields,
  cartographerMapSubCartographerFields,
  cartographerMapTrustAuditFields,
  cartographerMapWorkflowPanelFields,
  cartographerPreviewControlAuthority,
  cartographerRawMapDiagnosticSections,
} from "../map-information-architecture";

describe("Cartographer map information architecture", () => {
  it("uses simple mobile-first operational sections for the /map controller", () => {
    expect(cartographerMapOperationalSections.map((section) => section.id)).toEqual([
      "status-strip",
      "can-act",
      "blockers",
      "dirty-tree-groups",
      "commit-push-readiness",
      "project-tracker",
      "advisory-fleet",
      "manual-check",
      "raw-diagnostics",
    ]);
  });

  it("keeps raw backend diagnostic sections separate from the simple controller", () => {
    expect(cartographerRawMapDiagnosticSections.map((section) => section.id)).toEqual([
      "read-only-sources",
      "approvals",
      "queue-workflow",
      "stop-controls",
      "review-readiness",
      "trust-audit",
      "receipts",
      "authority-boundary",
    ]);
  });

  it("keeps operator review questions simple and human-readable", () => {
    expect(cartographerMapOperatorQuestions).toContain(
      "What is Cartographer's status?",
    );
    expect(cartographerMapOperatorQuestions).toContain("Can Cartographer act?");
    expect(cartographerMapOperatorQuestions).toContain("What blocks action?");
    expect(cartographerMapOperatorQuestions).toContain("How is the dirty tree grouped?");
    expect(cartographerMapOperatorQuestions).toContain("Are commit and push ready?");
    expect(cartographerMapOperatorQuestions).toContain("Which projects need attention?");
    expect(cartographerMapOperatorQuestions).toContain(
      "Which advisory helpers are watching only?",
    );
    expect(cartographerMapOperatorQuestions).toContain(
      "What manual check should Britton run?",
    );
    expect(cartographerMapOperatorQuestions).toContain("Where are raw diagnostics?");
  });

  it("locks the raw live state panel fields", () => {
    expect(cartographerMapLiveStateFields).toEqual([
      "Branch",
      "HEAD",
      "Dirty state",
      "Protected-lane state",
      "Repo-map source",
      "Recommendation",
    ]);
  });

  it("locks raw visible read-only source fields", () => {
    expect(cartographerMapReadOnlySourceFields).toEqual([
      "Live state",
      "Status",
      "Repo map",
      "Sub-cartographers",
      "Trust score",
      "Audit trail",
    ]);
    expect(cartographerMapSubCartographerFields).toEqual([
      "Roles observed",
      "Routes observed",
      "Outputs observed",
      "Maximum authority",
      "Forbidden actions",
    ]);
    expect(cartographerMapTrustAuditFields).toEqual([
      "Score",
      "Grade",
      "Authority granted",
      "Signals needing review",
      "Audit event count",
      "Audit result summary",
    ]);
  });

  it("locks the raw approval token panel fields", () => {
    expect(cartographerMapApprovalTokenFields).toEqual([
      "Runtime status",
      "Validation status",
      "Consumption preview",
      "Blocked reasons",
      "Safe next action",
    ]);
  });

  it("locks the raw queue panel fields", () => {
    expect(cartographerMapQueuePanelFields).toEqual([
      "Queue status",
      "Run-next status",
      "One-task selection",
      "Execution blocked",
      "Safe next action",
    ]);
  });

  it("locks the raw workflow run panel fields", () => {
    expect(cartographerMapWorkflowPanelFields).toEqual([
      "Active runs",
      "Recent runs",
      "Workflow status",
      "Step status",
      "Blocked reasons",
    ]);
  });

  it("locks the raw kill switch and stop control fields", () => {
    expect(cartographerMapStopControlFields).toEqual([
      "Kill switch state",
      "Pause control",
      "Cancel control",
      "Timeout control",
      "Retry control",
    ]);
  });

  it("locks the raw receipt and evidence browser fields", () => {
    expect(cartographerMapReceiptEvidenceFields).toEqual([
      "Receipt journal",
      "Evidence artifacts",
      "Approved docs paths",
      "Missing evidence",
      "Write blocked",
    ]);
  });

  it("locks the review-only readiness cards", () => {
    expect(cartographerMapReviewOnlyReadinessFields).toEqual([
      "Commit readiness",
      "Push readiness",
      "Merge readiness",
      "Queue readiness",
      "Approval readiness",
      "Preflight readiness",
      "Kill switch status",
    ]);
  });

  it("locks the operator decision packet fields", () => {
    expect(cartographerMapOperatorDecisionPacketFields).toEqual([
      "Decision default",
      "Current HEAD",
      "Dirty tree summary",
      "Protected lane summary",
      "Required proof",
      "Missing proof",
      "Blocked actions",
      "Kill switch state",
      "Manual decision",
    ]);
  });

  it("does not present authority-granting dashboard actions", () => {
    expect(cartographerMapAuthorityDenials).toContain("No approval minting");
    expect(cartographerMapAuthorityDenials).toContain("No self-approval");
    expect(cartographerMapAuthorityDenials).toContain("No source writes");
    expect(cartographerMapAuthorityDenials).toContain("No command execution");
    expect(cartographerMapAuthorityDenials).toContain(
      "No commit, push, branch, checkout, reset, clean, or stash",
    );
  });

  it("defines only preview controls that cannot post, mutate, execute, or grant authority", () => {
    expect(cartographerPreviewControlAuthority.map((control) => control.kind)).toEqual([
      "display-only-card",
      "existing-get-link",
      "copyable-manual-command-text",
      "local-expand-collapse",
      "safe-refresh",
      "already-read-get-summary",
    ]);

    expect(
      cartographerPreviewControlAuthority.every(
        (control) =>
          control.grantsAuthority === false &&
          control.mayPost === false &&
          control.mayMutate === false &&
          control.mayExecute === false,
      ),
    ).toBe(true);

    expect(cartographerForbiddenPreviewControlActions).toContain("POST");
    expect(cartographerForbiddenPreviewControlActions).toContain("run queue");
    expect(cartographerForbiddenPreviewControlActions).toContain("grant autonomy");
  });

  it("groups dirty files for preview without granting cleanup authority", () => {
    const preview = buildCartographerDirtyTreePreview({
      trackedDirtyFiles: [
        "docs/cartographer-map-preview-controls-plan-v0.1.md",
        "src/app/map/page.tsx",
        ".next/cache/fetch-cache",
      ],
      untrackedFiles: ["notes/local.txt", "source_proxy/cartographer/service.py"],
      protectedLaneMatches: [
        { path: "src/app/map/page.tsx", lane: "map" },
        { path: "source_proxy/cartographer/service.py", lane: "source_proxy_runtime" },
      ],
    });

    expect(preview).toMatchObject({
      totalDirtyFiles: 5,
      trackedCount: 3,
      untrackedCount: 2,
      protectedLaneCount: 2,
      authority: "preview-only",
    });
    expect(preview.likelySafeDocsFiles).toEqual([
      "docs/cartographer-map-preview-controls-plan-v0.1.md",
    ]);
    expect(preview.riskySourceFiles).toEqual([
      "src/app/map/page.tsx",
      "source_proxy/cartographer/service.py",
    ]);
    expect(preview.generatedCacheFiles).toEqual([".next/cache/fetch-cache"]);
    expect(preview.unknownFiles).toEqual(["notes/local.txt"]);
    expect(preview.cleanupPlanPreview.join(" ")).toContain("do not clean from /map");
  });

  it("builds commit previews without staging or committing authority", () => {
    const dirtyTree = buildCartographerDirtyTreePreview({
      trackedDirtyFiles: ["docs/plan.md", "src/app/map/page.tsx"],
      untrackedFiles: [".next/cache/trace"],
      protectedLaneMatches: [{ path: "src/app/map/page.tsx", lane: "map" }],
    });
    const preview = buildCartographerCommitPreview(dirtyTree);

    expect(preview.authority).toBe("preview-only");
    expect(preview.canStage).toBe(false);
    expect(preview.canCommit).toBe(false);
    expect(preview.suggestedCommitGroups.map((group) => group.label)).toEqual([
      "Docs review group",
      "Source review group",
    ]);
    expect(preview.filesThatShouldNotBeCommittedYet).toEqual([
      ".next/cache/trace",
      "src/app/map/page.tsx",
    ]);
    expect(preview.missingVerification).toContain("git diff --check");
    expect(preview.suggestedCommitMessageDraft).toBe(
      "chore: review cartographer preview model changes",
    );
  });

  it("builds branch and push previews without git mutation authority", () => {
    const dirtyTree = buildCartographerDirtyTreePreview({
      trackedDirtyFiles: ["src/app/map/page.tsx"],
      untrackedFiles: [],
      protectedLaneMatches: [{ path: "src/app/map/page.tsx", lane: "map" }],
    });
    const preview = buildCartographerBranchPushPreview({
      currentBranch: "feature/map-preview",
      currentHead: "abcdef1234567890",
      ahead: 2,
      behind: 1,
      upstream: "origin/main",
      dirtyTree,
    });

    expect(preview).toMatchObject({
      currentBranch: "feature/map-preview",
      headShortHash: "abcdef123456",
      aheadBehindSummary: "2 ahead, 1 behind origin/main",
      mergeRisk: "blocked",
      pushReadiness: "blocked",
      authority: "preview-only",
      canCheckout: false,
      canCreateBranch: false,
      canMerge: false,
      canPush: false,
    });
    expect(preview.changedAreas).toEqual(["source", "protected lanes"]);
    expect(preview.pushBlockers).toContain("dirty tree needs manual review");
    expect(preview.pushBlockers).toContain("branch is behind upstream");
    expect(preview.proofNeeded).toContain("separate push approval");
  });

  it("defines project cards as preview-only with no mutation or worker start", () => {
    expect(cartographerDefaultProjectCardPreviews.map((card) => card.label)).toEqual([
      "SpiritOS",
      "Source Proxy",
      "Cartographer",
      "Scout",
      "Agent Factory",
      "Media app",
      "Oracle / Chat",
    ]);

    expect(
      cartographerDefaultProjectCardPreviews.every(
        (card) =>
          card.authority === "preview-only" &&
          card.canMutateProject === false &&
          card.canStartWorker === false,
      ),
    ).toBe(true);
    expect(cartographerDefaultProjectCardPreviews.map((card) => card.state)).toContain(
      "blocked",
    );
    expect(
      cartographerDefaultProjectCardPreviews.find((card) => card.projectId === "cartographer")
        ?.visibleRepoSignals,
    ).toContain("src/app/map");
  });
});

describe("Cartographer map Phase 1 read-only adapter", () => {
  it("uses only the Phase 1 approved read-only display sources", () => {
    expect(readOnlyMapEndpointAllowlist.map((source) => source.endpoint)).toEqual([
      "/v1/cartographer/live-state",
      "/v1/cartographer/status",
      "/v1/cartographer/repo-map",
      "/v1/cartographer/sub-cartographers",
      "/v1/cartographer/trust-score",
      "/v1/cartographer/audit-trail",
    ]);
  });

  it("can display a 6/6 live read-only state with conservative source summaries", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      let payload: Record<string, unknown>;

      if (url.endsWith("/v1/cartographer/live-state")) {
        payload = {
          current_branch: "main",
          current_head: "abc123",
          recommended_safety_state: "blocked",
          tracked_dirty_files: ["src/app/map/page.tsx"],
          untracked_files: [],
        };
      } else if (url.endsWith("/v1/cartographer/status")) {
        payload = {
          status: "observing",
          write_actions_enabled: false,
          configured_roots: [{ path: "/home/source/SpiritOS" }],
          pending_proposals: 0,
        };
      } else if (url.endsWith("/v1/cartographer/repo-map")) {
        payload = {
          status: "observing",
          maps: [],
          project_count: 0,
          safety: { write_policy: "read_only" },
        };
      } else if (url.endsWith("/v1/cartographer/sub-cartographers")) {
        payload = {
          status: "observing",
          roles: [
            {
              role_id: "component_mapper",
              label: "Component Mapper",
              max_authority: "read_only",
            },
          ],
          routes: [],
          outputs: [],
          safety: { write_policy: "read_only" },
        };
      } else if (url.endsWith("/v1/cartographer/trust-score")) {
        payload = {
          status: "observing",
          score: 40,
          grade: "low",
          authority_granted: false,
          signals: [{ code: "authority_locked", passed: true }],
          safety: { write_policy: "read_only" },
        };
      } else {
        payload = {
          status: "observing",
          events: [{ event: "commit_pending", result: "pending_approval" }],
          event_count: 1,
          safety: { write_policy: "read_only" },
        };
      }

      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    };

    try {
      const data = await getReadOnlyMapData("https://spirit.test");

      expect(data.mode).toBe("read-only-live");
      expect(data.statusLabel).toBe("Live read-only display");
      expect(data.recommendationPacket.fallback_state).toBe("none");
      expect(data.endpoints.filter((endpoint) => endpoint.state === "live")).toHaveLength(6);
      expect(
        data.endpoints.find(
          (endpoint) => endpoint.endpoint === "/v1/cartographer/sub-cartographers",
        )?.sourceSummary,
      ).toContain("Component Mapper: read_only");
      expect(
        data.endpoints.find(
          (endpoint) => endpoint.endpoint === "/v1/cartographer/trust-score",
        )?.sourceSummary,
      ).toContain("Authority granted: no");
      expect(
        data.endpoints.find(
          (endpoint) => endpoint.endpoint === "/v1/cartographer/audit-trail",
        )?.sourceSummary,
      ).toContain("First result: pending_approval");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("preserves static fallback when live data is unavailable", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new Error("offline");
    };

    try {
      const data = await getReadOnlyMapData("https://spirit.test");

      expect(data.mode).toBe("static-fallback");
      expect(data.statusLabel).toBe("Static fallback");
      expect(data.recommendationPacket.fallback_state).toBe("active");
      expect(data.endpoints).toHaveLength(readOnlyMapEndpointAllowlist.length);
      expect(data.endpoints.every((endpoint) => endpoint.state === "fallback")).toBe(true);
      expect(
        data.endpoints.every(
          (endpoint) => endpoint.failureKind === "network-or-fetch-error",
        ),
      ).toBe(true);
      expect(data.recommendationPacket.authority_denials).toContain(
        "write authority is not granted",
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("treats malformed endpoint shapes as fallback instead of live data", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ unexpected: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });

    try {
      const data = await getReadOnlyMapData("https://spirit.test");

      expect(data.mode).toBe("static-fallback");
      expect(
        data.endpoints.every((endpoint) => endpoint.failureKind === "malformed-shape"),
      ).toBe(true);
      expect(
        data.endpoints.every((endpoint) => endpoint.shapeSummary === "malformed-shape"),
      ).toBe(true);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("normalizes success, non-OK, timeout, and failed fetch states", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);

      if (url.endsWith("/v1/cartographer/live-state")) {
        return new Response(
          JSON.stringify({
            current_branch: "main",
            current_head: "abc123",
            recommended_safety_state: "blocked",
          }),
          {
            status: 200,
            headers: { "content-type": "application/json" },
          },
        );
      }

      if (url.endsWith("/v1/cartographer/status")) {
        return new Response("unavailable", { status: 503 });
      }

      if (url.endsWith("/v1/cartographer/repo-map")) {
        throw new DOMException("Aborted", "AbortError");
      }

      throw new Error("offline");
    };

    try {
      const data = await getReadOnlyMapData("https://spirit.test");
      const statesByEndpoint = Object.fromEntries(
        data.endpoints.map((endpoint) => [endpoint.endpoint, endpoint]),
      );

      expect(data.mode).toBe("read-only-live");
      expect(data.statusLabel).toBe("Partial live read-only display");
      expect(statesByEndpoint["/v1/cartographer/live-state"]?.state).toBe("live");
      expect(statesByEndpoint["/v1/cartographer/status"]?.failureKind).toBe(
        "http-error",
      );
      expect(statesByEndpoint["/v1/cartographer/repo-map"]?.failureKind).toBe(
        "timeout",
      );
      expect(
        statesByEndpoint["/v1/cartographer/sub-cartographers"]?.failureKind,
      ).toBe("network-or-fetch-error");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("uses static fallback when no request origin is available", async () => {
    const data = await getReadOnlyMapData(null);

    expect(data.mode).toBe("static-fallback");
    expect(data.endpoints.every((endpoint) => endpoint.failureKind === "missing-origin")).toBe(
      true,
    );
  });

  it("normalizes the Plan 2 truth packet as display-only NO-GO data", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          current_branch: "main",
          current_head: "abc123",
          recommended_safety_state: "caution",
          tracked_dirty_files: ["docs/note.md"],
          untracked_files: [],
          protected_lane_matches: [],
          git_available: true,
          truth_packet: {
            schema_version: "cartographer.truth-packet.v0.1",
            status: "caution",
            decision_default: "no_go",
            advisory_only: true,
            facts: {
              total_dirty_count: 1,
              protected_lane_count: 0,
              git_available: true,
            },
            recommendations: {
              confidence: "high",
              no_go_reason: "human_review_required",
              safe_next_action: "Review dirty tree facts manually.",
            },
            state_flags: {
              verified: true,
              blocked: false,
              stale: false,
              unknown: false,
              caution: true,
              clear: false,
              no_go: true,
              advisory_only: true,
            },
            authority: {
              authority_granted: false,
              write_actions_enabled: false,
              queue_authority_granted: false,
              can_mutate: false,
            },
            verified_fields: ["facts.current_branch"],
            unknown_fields: [],
            stale_fields: [],
          },
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      );

    try {
      const liveState = await getCartographerLiveState("https://spirit.test");

      expect(liveState.truthPacket.schemaVersion).toBe(
        "cartographer.truth-packet.v0.1",
      );
      expect(liveState.truthPacket.status).toBe("caution");
      expect(liveState.truthPacket.decisionDefault).toBe("no_go");
      expect(liveState.truthPacket.stateFlags.noGo).toBe(true);
      expect(liveState.truthPacket.stateFlags.advisoryOnly).toBe(true);
      expect(liveState.truthPacket.authority.authorityGranted).toBe(false);
      expect(liveState.truthPacket.authority.writeActionsEnabled).toBe(false);
      expect(liveState.truthPacket.authority.queueAuthorityGranted).toBe(false);
      expect(liveState.truthPacket.authority.canMutate).toBe(false);
      expect(liveState.truthPacket.verifiedFields).toContain("facts.current_branch");
      expect(liveState.truthPacket.unknownFields).toEqual([]);
      expect(liveState.truthPacket.staleFields).toEqual([]);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("normalizes stale truth packets as read-only NO-GO data", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          current_branch: "main",
          current_head: "abc123",
          recommended_safety_state: "clear",
          tracked_dirty_files: [],
          untracked_files: [],
          protected_lane_matches: [],
          git_available: true,
          truth_packet: {
            schema_version: "cartographer.truth-packet.v0.1",
            status: "stale",
            decision_default: "no_go",
            advisory_only: true,
            facts: {
              total_dirty_count: 0,
              protected_lane_count: 0,
              git_available: true,
            },
            recommendations: {
              confidence: "low",
              no_go_reason: "stale_fields_present",
              safe_next_action: "Refresh live repository facts before proceeding.",
            },
            state_flags: {
              verified: false,
              blocked: true,
              stale: true,
              unknown: false,
              caution: false,
              clear: false,
              no_go: true,
              advisory_only: true,
            },
            authority: {
              authority_granted: false,
              write_actions_enabled: false,
              queue_authority_granted: false,
              can_mutate: false,
            },
            verified_fields: ["facts.current_branch"],
            unknown_fields: [],
            stale_fields: ["recency.collected_at"],
          },
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      );

    try {
      const liveState = await getCartographerLiveState("https://spirit.test");

      expect(liveState.truthPacket.status).toBe("stale");
      expect(liveState.truthPacket.decisionDefault).toBe("no_go");
      expect(liveState.truthPacket.stateFlags.noGo).toBe(true);
      expect(liveState.truthPacket.stateFlags.blocked).toBe(true);
      expect(liveState.truthPacket.stateFlags.stale).toBe(true);
      expect(liveState.truthPacket.stateFlags.clear).toBe(false);
      expect(liveState.truthPacket.recommendations.confidence).toBe("low");
      expect(liveState.truthPacket.recommendations.noGoReason).toBe(
        "stale_fields_present",
      );
      expect(liveState.truthPacket.staleFields).toEqual(["recency.collected_at"]);
      expect(liveState.truthPacket.authority.authorityGranted).toBe(false);
      expect(liveState.truthPacket.authority.writeActionsEnabled).toBe(false);
      expect(liveState.truthPacket.authority.queueAuthorityGranted).toBe(false);
      expect(liveState.truthPacket.authority.canMutate).toBe(false);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("uses the local self-signed HTTPS dispatcher for private LAN read-only origins", async () => {
    const originalFetch = globalThis.fetch;
    const fetchInits: RequestInit[] = [];

    globalThis.fetch = async (_input, init) => {
      fetchInits.push(init ?? {});
      return new Response(
        JSON.stringify({
          current_branch: "main",
          current_head: "abc123",
          recommended_safety_state: "blocked",
          status: "observing",
          write_actions_enabled: false,
          maps: [],
          roles: [],
          score: 40,
          events: [],
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      );
    };

    try {
      const data = await getReadOnlyMapData("https://10.0.0.186:3000");
      const liveState = await getCartographerLiveState("https://10.0.0.186:3000");

      expect(data.mode).toBe("read-only-live");
      expect(liveState.available).toBe(true);
      expect(
        fetchInits.every((init) => "dispatcher" in (init as Record<string, unknown>)),
      ).toBe(true);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("does not attach the local self-signed HTTPS dispatcher to public origins", async () => {
    const originalFetch = globalThis.fetch;
    const fetchInits: RequestInit[] = [];

    globalThis.fetch = async (_input, init) => {
      fetchInits.push(init ?? {});
      throw new Error("offline");
    };

    try {
      await getReadOnlyMapData("https://spirit.example");

      expect(
        fetchInits.every((init) => !("dispatcher" in (init as Record<string, unknown>))),
      ).toBe(true);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("does not contain POST fetches in Phase 1 read-only adapters", () => {
    const sources = [
      "src/app/map/read-only-map-data.ts",
      "src/app/map/cartographer-live-state.ts",
    ].map((path) => readFileSync(resolve(process.cwd(), path), "utf8"));

    for (const source of sources) {
      expect(source).not.toMatch(/method:\s*['"]POST['"]/);
      const forbiddenFetchWords = [
        "approve",
        "apply",
        "commit",
        "push",
        ["queue", "run-next"].join("/"),
        "safe" + "-write",
        ["verification", "run"].join("/"),
      ];
      expect(source).not.toMatch(
        new RegExp(`fetch\\([^\\n]*(${forbiddenFetchWords.map(escapeRegExp).join("|")})`),
      );
    }
  });

  it("keeps forbidden action endpoint strings out of /map executable wiring", () => {
    const executableMapSources = [
      "src/app/map/page.tsx",
      "src/app/map/read-only-map-data.ts",
      "src/app/map/cartographer-live-state.ts",
      "src/app/map/map-information-architecture.ts",
    ].map((path) => readFileSync(resolve(process.cwd(), path), "utf8").replace(/\s+/g, " "));
    const combinedSource = executableMapSources.join("\n");
    const forbiddenEndpointFragments = [
      "apply" + "-approved",
      ["docs-autopilot", "apply"].join("/"),
      "/" + "approve",
      "/" + "commit",
      "/" + "push",
      "safe" + "-write",
      ["verification", "run"].join("/"),
      ["queue", "run-next"].join("/"),
    ];
    const forbiddenHandlerFragments = ["<" + "button\\b", "on" + "Click=", "on" + "Submit="];

    expect(combinedSource).not.toMatch(
      new RegExp(forbiddenEndpointFragments.map(escapeRegExp).join("|")),
    );
    expect(combinedSource).not.toMatch(new RegExp(forbiddenHandlerFragments.join("|")));
  });
});

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
