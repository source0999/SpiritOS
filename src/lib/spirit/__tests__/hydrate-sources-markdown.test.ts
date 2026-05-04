import { describe, expect, it } from "vitest";

import {
  hydrateDegenerateSourcesMarkdown,
  isDegenerateSourcesBlock,
} from "@/components/chat/hydrate-sources-markdown";
import type { SpiritWebSourcesHeaderPayload } from "@/lib/spirit/spirit-web-sources";

describe("isDegenerateSourcesBlock", () => {
  it("flags ordered list with only citation numbers", () => {
    expect(isDegenerateSourcesBlock("1. 1\n2. 2")).toBe(true);
  });

  it("flags [n](url) stub links", () => {
    expect(isDegenerateSourcesBlock("1. [1](https://a.edu/x)\n2. [2](https://b.org/y)")).toBe(true);
  });

  it("rejects real titled links", () => {
    expect(isDegenerateSourcesBlock("1. [PubMed — ASD](https://pubmed.ncbi.nlm.nih.gov/x)")).toBe(false);
  });
});

describe("hydrateDegenerateSourcesMarkdown", () => {
  const payload: SpiritWebSourcesHeaderPayload = {
    provider: "openai",
    count: 2,
    sources: [
      { title: "Article A", url: "https://a.edu/paper" },
      { title: "", url: "https://www.b.org/long-path" },
    ],
  };

  it("replaces stub Sources with header-backed markdown links", () => {
    const md = `## Executive Summary\n\nBlah\n\n## Sources\n\n1. 1\n2. 2\n`;
    const out = hydrateDegenerateSourcesMarkdown(md, payload);
    expect(out).toContain("- [Article A](https://a.edu/paper)");
    expect(out).toContain("https://www.b.org/long-path");
    expect(out).not.toMatch(/\n1\. 1\n/);
  });

  it("leaves good Sources untouched", () => {
    const md = "## Sources\n\n- [NIH](https://www.nih.gov/)\n";
    expect(hydrateDegenerateSourcesMarkdown(md, payload)).toBe(md);
  });
});
