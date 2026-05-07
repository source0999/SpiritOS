import { describe, expect, it } from "vitest";

import { createSpiritToolActivityCard } from "../spirit-activity-events";
import { parseSpiritToolActivityHeader } from "../spirit-tool-activity-response";

describe("parseSpiritToolActivityHeader", () => {
  it("returns empty array when header missing", () => {
    const res = new Response(null, { status: 200 });
    expect(parseSpiritToolActivityHeader(res)).toEqual([]);
  });

  it("parses compact tool activity JSON array", () => {
    const card = createSpiritToolActivityCard({
      kind: "workspace_list",
      label: "List workspace files",
      status: "completed",
      target: "src",
    });
    const res = new Response(null, {
      headers: { "x-spirit-tool-activity-json": JSON.stringify([card]) },
    });
    const parsed = parseSpiritToolActivityHeader(res);
    expect(parsed).toHaveLength(1);
    expect(parsed[0]?.kind).toBe("workspace_list");
    expect(parsed[0]?.target).not.toMatch(/^\//);
  });
});
