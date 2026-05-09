import { describe, expect, it } from "vitest";

import {
  appendSpiritActivityEvent,
  SPIRIT_ACTIVITY_EVENT_CAP,
  type SpiritActivityEvent,
} from "@/lib/spirit/spirit-activity-events";

describe("appendSpiritActivityEvent", () => {
  it("appends and caps list", () => {
    let list: SpiritActivityEvent[] = [];
    for (let i = 0; i < SPIRIT_ACTIVITY_EVENT_CAP + 5; i++) {
      list = appendSpiritActivityEvent(list, {
        kind: "message_submitted",
        label: `evt ${i}`,
      });
    }
    expect(list.length).toBe(SPIRIT_ACTIVITY_EVENT_CAP);
    expect(list.at(-1)?.label).toBe(`evt ${SPIRIT_ACTIVITY_EVENT_CAP + 4}`);
  });

  it("records mode change label", () => {
    const next = appendSpiritActivityEvent([], {
      kind: "mode_changed",
      label: "Mode switched to Teacher",
    });
    expect(next).toHaveLength(1);
    expect(next[0]!.kind).toBe("mode_changed");
    expect(next[0]!.label).toContain("Teacher");
  });
});
