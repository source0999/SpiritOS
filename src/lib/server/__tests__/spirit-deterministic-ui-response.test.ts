import { describe, expect, it } from "vitest";

import { createSpiritToolActivityCard } from "@/lib/spirit/spirit-activity-events";

import { createDeterministicAssistantUIMessageResponse } from "../spirit-deterministic-ui-response";

describe("createDeterministicAssistantUIMessageResponse", () => {
  it("sets x-spirit-tool-activity-json for deterministic tool telemetry", () => {
    const card = createSpiritToolActivityCard({
      kind: "workspace_list",
      label: "List workspace files",
      status: "completed",
      target: "src",
    });
    const res = createDeterministicAssistantUIMessageResponse({
      text: "ok",
      originalMessages: [],
      toolActivity: [card],
    });
    const raw = res.headers.get("x-spirit-tool-activity-json");
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!) as unknown[];
    expect(parsed).toHaveLength(1);
    expect((parsed[0] as { target?: string }).target).toBe("src");
  });
});
