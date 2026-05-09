import { describe, expect, it } from "vitest";

import { formatResearchContextForHermes } from "@/lib/server/spirit-web-research-guard";

/** Teacher digest: bare-host OpenAI payloads must surface as real https links (same gate as policy). */
describe("Teacher web digest + bare-host sources", () => {
  it("includes https://www.example.com/abc in Verified URL digest lines", () => {
    const ctx = formatResearchContextForHermes("stimulus over-selectivity", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "Example resource", url: "www.example.com/abc" }],
    });
    expect(ctx).toContain("Web research digest");
    expect(ctx).toContain("Verified URL sources (1):");
    expect(ctx).toContain("https://www.example.com/abc");
  });

  it("normalizes www.ncbi.nlm.nih.gov into digest https links (Teacher digest parity)", () => {
    const ctx = formatResearchContextForHermes("autism sensory modulation", {
      ok: true,
      searched: true,
      provider: "openai",
      query: "q",
      sources: [{ title: "Bookshelf", url: "www.ncbi.nlm.nih.gov/books/NBK1430/" }],
    });
    expect(ctx).toContain("Web research digest");
    expect(ctx).toContain("https://www.ncbi.nlm.nih.gov/books/NBK1430/");
    expect(ctx).toMatch(/Verified URL sources \(1\):/);
  });
});
