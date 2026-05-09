import { describe, expect, it } from "vitest";

import { getModelProfile, isModelProfileId, MODEL_PROFILES } from "@/lib/spirit/model-profiles";
import { DEFAULT_MODEL_PROFILE_ID } from "@/lib/spirit/model-profile.types";

describe("model-profiles", () => {
  it("Peer shortLabel and researcher flags", () => {
    expect(MODEL_PROFILES["normal-peer"].shortLabel).toBe("Peer");
    expect(MODEL_PROFILES["normal-peer"].label).toBe("Peer");
    expect(MODEL_PROFILES.researcher.searchPreferred).toBe(true);
    expect(MODEL_PROFILES.researcher.requiresCitationStyle).toBe(true);
    expect(MODEL_PROFILES.researcher.reportStyle).toBe(true);
  });

  it("Peer profile does not brand itself as a coding assistant by default", () => {
    const p = MODEL_PROFILES["normal-peer"].systemPrompt;
    expect(p).not.toMatch(/\bcoding assistant\b/i);
    expect(p).toContain("You are Spirit in Peer mode");
  });

  it("Peer profile describes concise conversational behavior", () => {
    expect(MODEL_PROFILES["normal-peer"].systemPrompt).toMatch(/1 to 4 sentences|casual replies short/i);
  });

  it("Peer profile reserves technical help for when user asks", () => {
    expect(MODEL_PROFILES["normal-peer"].systemPrompt).toMatch(
      /technical, coding, or build help|asks for technical/i,
    );
  });

  it("mode prompts differ between Peer and Teacher", () => {
    expect(MODEL_PROFILES["normal-peer"].systemPrompt).toContain("Peer mode");
    expect(MODEL_PROFILES.teacher.systemPrompt).toContain("Teacher mode");
    expect(MODEL_PROFILES["normal-peer"].systemPrompt).not.toContain("Teacher mode");
  });

  it("brutal and sassy summaries exist", () => {
    expect(MODEL_PROFILES.brutal.responseStyleSummary.length).toBeGreaterThan(2);
    expect(MODEL_PROFILES["sassy-chaotic"].responseStyleSummary.length).toBeGreaterThan(2);
  });

  it("returns normal-peer for missing id", () => {
    expect(getModelProfile(undefined).id).toBe(DEFAULT_MODEL_PROFILE_ID);
    expect(getModelProfile(null).id).toBe(DEFAULT_MODEL_PROFILE_ID);
  });

  it("returns normal-peer for invalid id", () => {
    expect(getModelProfile("nope").id).toBe(DEFAULT_MODEL_PROFILE_ID);
  });

  it("researcher temperature is 0.28", () => {
    expect(MODEL_PROFILES.researcher.temperature).toBe(0.28);
  });

  it("sassy-chaotic temperature is 1.05", () => {
    expect(MODEL_PROFILES["sassy-chaotic"].temperature).toBe(1.05);
  });

  it("isModelProfileId narrows union", () => {
    expect(isModelProfileId("teacher")).toBe(true);
    expect(isModelProfileId(1)).toBe(false);
  });

  it("researcher system prompt forbids invented citations", () => {
    expect(MODEL_PROFILES.researcher.systemPrompt).toMatch(/Never invent citations/i);
  });

  it("normal-peer explicitly allows technical depth for code, repo, and homelab questions", () => {
    const p = MODEL_PROFILES["normal-peer"].systemPrompt;
    expect(p).toMatch(/enough structure and detail|technical.*enough structure/i);
  });

  it("normal-peer does not hard-block technical framing, only casual defaults", () => {
    const p = MODEL_PROFILES["normal-peer"].systemPrompt;
    expect(p).toMatch(/When the user actually asks for coding|asks for coding, repo/i);
  });
});
