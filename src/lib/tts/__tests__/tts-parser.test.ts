import { describe, expect, it } from "vitest";

import { parseTtsSegments, stripTextForTts } from "@/lib/tts/tts-parser";

describe("stripTextForTts", () => {
  it("strips fenced code and inline markers", () => {
    const s = stripTextForTts("See `x` and [a](http://b) **bold**");
    expect(s).toContain("x");
    expect(s).toContain("a");
    expect(s).not.toContain("**");
  });
});

describe("parseTtsSegments", () => {
  it("parses plain speech", () => {
    expect(parseTtsSegments("Hello world")).toEqual([
      { type: "speech", text: "Hello world" },
    ]);
  });

  it("parses pause markers", () => {
    expect(parseTtsSegments("A [pause:100] B")).toEqual([
      { type: "speech", text: "A" },
      { type: "pause", ms: 100 },
      { type: "speech", text: "B" },
    ]);
    expect(parseTtsSegments("A [pause:1s] B")).toEqual([
      { type: "speech", text: "A" },
      { type: "pause", ms: 1000 },
      { type: "speech", text: "B" },
    ]);
    expect(parseTtsSegments("A [[pause 250ms]] B")).toEqual([
      { type: "speech", text: "A" },
      { type: "pause", ms: 250 },
      { type: "speech", text: "B" },
    ]);
  });
});
