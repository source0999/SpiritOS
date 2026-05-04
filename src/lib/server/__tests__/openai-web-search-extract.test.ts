import { describe, expect, it } from "vitest";

import {
  appendVerifiedUrlsFromAnswerPreview,
  extractWebSearchSourcesFromOpenAiResponseJson,
} from "@/lib/server/openai-web-search";

describe("extractWebSearchSourcesFromOpenAiResponseJson", () => {
  it("reads web_search_call.action.sources (OpenAI Responses include shape)", () => {
    const { sources } = extractWebSearchSourcesFromOpenAiResponseJson(
      {
        output: [
          {
            type: "web_search_call",
            action: {
              type: "search",
              sources: [
                { type: "url", url: "https://a.edu/x" },
                { type: "url", url: "www.b.org/y" },
              ],
            },
          },
        ],
      },
      12,
    );
    expect(sources).toHaveLength(2);
    expect(sources[0]?.url).toBe("https://a.edu/x");
    expect(sources[1]?.url).toBe("https://www.b.org/y");
  });

  it("picks href / start_url style citation objects", () => {
    const { sources } = extractWebSearchSourcesFromOpenAiResponseJson(
      {
        output: [
          {
            type: "message",
            content: [
              {
                type: "output_text",
                text: "See ref",
                annotations: [
                  {
                    type: "url_citation",
                    href: "www.ncbi.nlm.nih.gov/books/NBK1/",
                    title: "NBK",
                  },
                ],
              },
            ],
          },
        ],
      },
      12,
    );
    expect(sources.some((s) => s.url === "https://www.ncbi.nlm.nih.gov/books/NBK1/")).toBe(true);
  });

  it("appendVerifiedUrlsFromAnswerPreview scrapes https links from grounded preview when structured urls missing", () => {
    const out = appendVerifiedUrlsFromAnswerPreview(
      [{ title: "stub", url: undefined }],
      "Sources include https://pubmed.ncbi.nlm.nih.gov/123 and https://cdc.gov/foo.",
      8,
    );
    expect(out.some((s) => s.url?.includes("pubmed.ncbi"))).toBe(true);
    expect(out.some((s) => s.url?.includes("cdc.gov"))).toBe(true);
  });
});
