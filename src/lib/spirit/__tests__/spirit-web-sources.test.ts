import { describe, expect, it } from "vitest";

import { parseSpiritWebSourcesHeader } from "@/lib/spirit/spirit-web-sources";

describe("parseSpiritWebSourcesHeader", () => {
  it("parses valid JSON header payload", () => {
    const json = JSON.stringify({
      provider: "openai",
      count: 1,
      sources: [{ title: "T", url: "https://t" }],
    });
    const out = parseSpiritWebSourcesHeader(json);
    expect(out?.provider).toBe("openai");
    expect(out?.count).toBe(1);
    expect(out?.sources[0]?.url).toBe("https://t");
  });

  it("returns null on invalid JSON", () => {
    expect(parseSpiritWebSourcesHeader("{")).toBeNull();
  });

  it("returns null for empty input", () => {
    expect(parseSpiritWebSourcesHeader(null)).toBeNull();
    expect(parseSpiritWebSourcesHeader("")).toBeNull();
  });
});
