import { describe, expect, it } from "vitest";

import {
  describeCodingProviderIntent,
  getCodingProviderStatuses,
} from "@/lib/coding/model-provider-status";

describe("getCodingProviderStatuses", () => {
  it("defaults local provider and marks cloud unavailable", () => {
    expect(getCodingProviderStatuses()).toEqual([
      expect.objectContaining({
        id: "local",
        label: "Local LLM",
        status: "default",
      }),
      expect.objectContaining({
        id: "cloud",
        label: "GPT/cloud",
        status: "unavailable",
      }),
      expect.objectContaining({
        id: "codex_worker",
        label: "Codex worker",
        status: "proposal-only",
      }),
      expect.objectContaining({
        id: "future",
        label: "Future providers",
        status: "future",
      }),
    ]);
  });

  it("marks cloud configured only when explicitly provided", () => {
    expect(getCodingProviderStatuses({ cloudConfigured: true })[1]).toEqual(
      expect.objectContaining({
        id: "cloud",
        status: "configured",
      }),
    );
  });

  it("describes provider intent without claiming a provider call ran", () => {
    expect(describeCodingProviderIntent("local")).toBe(
      "Intent: local LLM route. No provider call has run yet.",
    );
    expect(describeCodingProviderIntent("cloud")).toBe(
      "Intent: GPT/cloud route requested, but unavailable until configured. No provider call has run yet.",
    );
    expect(
      describeCodingProviderIntent("cloud", getCodingProviderStatuses({ cloudConfigured: true })),
    ).toBe("Intent: GPT/cloud route when submitted. No provider call has run yet.");
    expect(describeCodingProviderIntent("codex_worker")).toBe(
      "Intent: Codex worker proposal route. No apply, commit, push, or provider call has run yet.",
    );
    expect(describeCodingProviderIntent("future")).toBe(
      "Intent: future provider route requested, but unavailable until a safe Source Proxy route is configured. No provider call has run yet.",
    );
  });

  it("keeps provider switching authority-free", () => {
    expect(
      getCodingProviderStatuses().every((provider) => {
        return !provider.authority.apply && !provider.authority.commit && !provider.authority.push;
      }),
    ).toBe(true);
    expect(getCodingProviderStatuses().find((provider) => provider.id === "cloud")?.authority)
      .toEqual(expect.objectContaining({ externalCall: false }));
    expect(
      getCodingProviderStatuses({ cloudConfigured: true }).find((provider) => provider.id === "cloud")
        ?.authority,
    ).toEqual(expect.objectContaining({ externalCall: true }));
  });
});
