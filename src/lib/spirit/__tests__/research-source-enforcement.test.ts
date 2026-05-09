import { describe, expect, it } from "vitest";

import {
  buildResearchSourcePolicy,
  hasUsableResearchSources,
  stripFakeCitationsWhenNoSources,
  userRequestedFreshExternalSources,
} from "@/lib/spirit/research-source-enforcement";

describe("research-source-enforcement", () => {
  it("hasUsableResearchSources requires http(s) URLs", () => {
    expect(hasUsableResearchSources([{ url: "https://a.edu/x" }])).toBe(true);
    expect(hasUsableResearchSources([{ url: "" }, { url: "not-a-url" }])).toBe(false);
  });

  it("hasUsableResearchSources treats bare hosts as verified after normalize", () => {
    expect(hasUsableResearchSources([{ url: "www.example.com/abc" }])).toBe(true);
  });

  it("buildResearchSourcePolicy teacher mode mandates links in Study aids when URLs exist", () => {
    const p = buildResearchSourcePolicy({
      searchStatus: "used",
      sources: [{ url: "https://example.com/a" }, { url: "https://example.org/b" }],
      requestedFreshSources: false,
      modelProfileId: "teacher",
    });
    expect(p).toContain("Study aids");
    expect(p).toContain("markdown bullet");
    expect(p).not.toContain("End with **## Sources**");
  });

  it("buildResearchSourcePolicy forbids citations when no URLs", () => {
    const p = buildResearchSourcePolicy({
      searchStatus: "skipped",
      sources: [],
      requestedFreshSources: false,
    });
    expect(p).toContain("Search used: no");
    expect(p).toContain("Do **not** include numbered citations");
  });

  it("stripFakeCitationsWhenNoSources removes Cochrane cosplay tail", () => {
    const t = `Search used: no (user_disabled_web_search)

## Executive Summary
Blah

## Sources
[1] Cochrane review
[2] PLOS One
[3] JADD`;
    const out = stripFakeCitationsWhenNoSources(t);
    expect(out).not.toContain("## Sources");
    expect(out).not.toMatch(/\[1\]/);
  });

  it("userRequestedFreshExternalSources detects 2024+ proof asks", () => {
    expect(
      userRequestedFreshExternalSources("Give me 2025 peer-reviewed sources on autism interventions"),
    ).toBe(true);
    expect(userRequestedFreshExternalSources("What is gravity")).toBe(false);
  });
});
