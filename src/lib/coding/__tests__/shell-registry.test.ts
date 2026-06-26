import { describe, expect, it } from "vitest";

import {
  activeCodingApiRouteSequence,
  activeCodingShell,
  codingApiRouteRegistry,
  codingApiRoutesByStatus,
  codingShellById,
  codingShellRegistry,
  codingShellsByStatus,
} from "../shell-registry";

describe("coding shell registry", () => {
  it("marks /coding as the active cockpit shell without deleting alternates", () => {
    expect(activeCodingShell).toMatchObject({
      id: "coding-cockpit-shell",
      route: "/coding",
      status: "active",
      component: "src/components/coding/CodingCockpitShell.tsx",
    });
    expect(codingShellsByStatus("active")).toHaveLength(1);
    expect(codingShellById("coding-command-center-shell")).toMatchObject({
      status: "experimental",
      ownerDecision: "undecided",
    });
  });

  it("keeps every shell reversible with a rollback note", () => {
    expect(codingShellRegistry.length).toBeGreaterThanOrEqual(2);
    for (const shell of codingShellRegistry) {
      expect(shell.component).toMatch(/^src\/components\/coding\//);
      expect(shell.rollback.length).toBeGreaterThan(20);
    }
  });

  it("marks the canonical /coding API sequence while keeping dormant alternates explicit", () => {
    expect(activeCodingApiRouteSequence.map((route) => route.route)).toEqual([
      "/v1/decisions/prompt-packet",
      "/v1/verification/diff-preview",
      "/v1/actions/execute-approved",
    ]);
    expect(codingApiRoutesByStatus("dormant").map((route) => route.route)).toEqual(
      expect.arrayContaining([
        "/v1/coding/codex",
        "/v1/coding/bounded-diff-preview",
        "/v1/coding/research-preview",
        "/v1/coding/helper-agents/preview",
      ]),
    );
    for (const route of codingApiRouteRegistry) {
      expect(route.operatorSurface.length).toBeGreaterThan(20);
      if (route.status === "dormant") {
        expect(route.dormantReason?.length).toBeGreaterThan(20);
      }
    }
  });
});
