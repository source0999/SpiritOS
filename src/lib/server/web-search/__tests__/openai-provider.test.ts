import { describe, expect, it, vi } from "vitest";

import { runOpenAiWebSearch } from "@/lib/server/openai-web-search";
import { runOpenAiFallbackWebSearch } from "@/lib/server/web-search/openai-provider";

vi.mock("@/lib/server/openai-web-search", () => ({
  runOpenAiWebSearch: vi.fn(),
}));

describe("runOpenAiFallbackWebSearch", () => {
  it("adapts existing OpenAI results into the generic contract", async () => {
    vi.mocked(runOpenAiWebSearch).mockResolvedValueOnce({
      ok: true,
      searched: true,
      provider: "openai",
      query: "docs",
      sources: [
        { title: "Docs", url: "https://example.com/docs", snippet: "Grounded" },
        { title: "Unsafe", url: "javascript:alert(1)" },
      ],
      answerPreview: "preview",
    });

    const result = await runOpenAiFallbackWebSearch({ query: "docs", maxResults: 5 });

    expect(runOpenAiWebSearch).toHaveBeenCalledWith({ query: "docs", maxResults: 5, timeoutMs: undefined });
    expect(result).toMatchObject({
      ok: true,
      searched: true,
      provider: "openai",
      query: "docs",
      answerPreview: "preview",
      sources: [{ title: "Docs", url: "https://example.com/docs", snippet: "Grounded", provider: "openai" }],
    });
  });

  it("preserves existing OpenAI failure details", async () => {
    vi.mocked(runOpenAiWebSearch).mockResolvedValueOnce({
      ok: false,
      searched: false,
      provider: "openai",
      error: "missing_key",
      detail: "OPENAI_API_KEY is not configured",
    });

    const result = await runOpenAiFallbackWebSearch({ query: "docs", maxResults: 5 });

    expect(result).toMatchObject({
      ok: false,
      searched: false,
      provider: "openai",
      error: "missing_key",
      detail: "OPENAI_API_KEY is not configured",
    });
  });
});
