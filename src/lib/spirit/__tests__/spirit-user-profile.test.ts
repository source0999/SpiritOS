import { describe, expect, it, vi } from "vitest";

import {
  buildModeAwarePersonalizationSummary,
  buildPersonalizationSummary,
  defaultSpiritUserProfile,
  loadSpiritUserProfile,
  saveSpiritUserProfile,
} from "@/lib/spirit/spirit-user-profile";

describe("spirit-user-profile", () => {
  it("defaults load with seeded preferences", () => {
    const p = defaultSpiritUserProfile();
    expect(p.preferences.length).toBeGreaterThan(3);
    expect(p.preferences.some((x) => x.label.includes("Communication"))).toBe(true);
  });

  it("buildPersonalizationSummary excludes when send disabled", () => {
    const p = defaultSpiritUserProfile();
    p.sendPersonalizationToServer = false;
    expect(buildPersonalizationSummary(p)).toBe("");
  });

  it("edit/delete affects summary", () => {
    const p = defaultSpiritUserProfile();
    const filtered = {
      ...p,
      preferences: p.preferences.filter((x) => x.id !== "tone"),
    };
    const s1 = buildPersonalizationSummary(p);
    const s2 = buildPersonalizationSummary(filtered);
    expect(s1).toContain("Communication");
    expect(s2).not.toContain("Communication");
  });

  it("loadSpiritUserProfile reads localStorage", () => {
    const ls = vi.spyOn(Storage.prototype, "getItem");
    ls.mockReturnValueOnce(
      JSON.stringify({
        version: 1,
        sendPersonalizationToServer: true,
        preferences: [{ id: "a", label: "L", value: "V" }],
      }),
    );
    const out = loadSpiritUserProfile();
    expect(out.preferences).toEqual([{ id: "a", label: "L", value: "V", source: "default" }]);
    ls.mockRestore();
  });

  it("saveSpiritUserProfile writes localStorage", () => {
    const spy = vi.spyOn(Storage.prototype, "setItem");
    const p = defaultSpiritUserProfile();
    saveSpiritUserProfile(p);
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it("buildModeAwarePersonalizationSummary adds research block for Researcher", () => {
    const p = defaultSpiritUserProfile();
    p.sendPersonalizationToServer = true;
    const s = buildModeAwarePersonalizationSummary(p, "researcher");
    expect(s).toContain("Web search default (Researcher): ON");
  });

  it("buildModeAwarePersonalizationSummary omits research block for Peer", () => {
    const p = defaultSpiritUserProfile();
    p.sendPersonalizationToServer = true;
    const s = buildModeAwarePersonalizationSummary(p, "normal-peer");
    expect(s).not.toContain("Research settings (local):");
  });

  it("loadSpiritUserProfile tolerates legacy JSON without researchSettings", () => {
    const ls = vi.spyOn(Storage.prototype, "getItem");
    ls.mockReturnValueOnce(
      JSON.stringify({
        version: 1,
        sendPersonalizationToServer: true,
        preferences: [{ id: "a", label: "L", value: "V" }],
      }),
    );
    const out = loadSpiritUserProfile();
    expect(out.researchSettings?.webSearchDefaultResearcher).toBe(true);
    ls.mockRestore();
  });
});
