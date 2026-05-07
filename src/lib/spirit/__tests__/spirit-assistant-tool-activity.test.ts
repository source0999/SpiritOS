import type { UIMessage } from "ai";
import { describe, expect, it } from "vitest";

import {
  mergeSpiritToolActivityCardsForMessage,
  toolUIPartsToActivityCards,
} from "../spirit-assistant-tool-activity";
import { createSpiritToolActivityCard } from "../spirit-activity-events";

describe("mergeSpiritToolActivityCardsForMessage", () => {
  it("uses assistant message metadata spiritToolActivity", () => {
    const c = createSpiritToolActivityCard({
      kind: "workspace_list",
      label: "List workspace files",
      status: "completed",
      target: "src/lib/spirit",
      summary: "3 entries",
    });
    const msg = {
      id: "m1",
      role: "assistant" as const,
      metadata: { spiritToolActivity: [c] },
      parts: [{ type: "text" as const, text: "hello" }],
    } satisfies UIMessage;
    const merged = mergeSpiritToolActivityCardsForMessage(msg);
    expect(merged).toHaveLength(1);
    expect(merged[0]?.kind).toBe("workspace_list");
    expect(merged[0]?.target).not.toMatch(/^\//);
  });

  it("maps list_workspace_files tool output to workspace_list card", () => {
    const msg = {
      id: "m2",
      role: "assistant" as const,
      parts: [
        {
          type: "tool-list_workspace_files" as const,
          toolCallId: "call_1",
          state: "output-available" as const,
          input: { directory: "src" },
          output: {
            ok: true,
            directory: "src",
            entries: [],
            truncated: false,
          },
        },
      ],
    } satisfies UIMessage;
    const merged = mergeSpiritToolActivityCardsForMessage(msg);
    expect(merged.some((x) => x.kind === "workspace_list" && x.status === "completed")).toBe(
      true,
    );
  });

  it("prefers metadata over tool parts when ids collide", () => {
    const fromMeta = createSpiritToolActivityCard({
      id: "toolpart_call_1",
      kind: "workspace_read",
      label: "Read workspace file",
      status: "completed",
      target: "README.md",
    });
    const msg = {
      id: "m3",
      role: "assistant" as const,
      metadata: { spiritToolActivity: [fromMeta] },
      parts: [
        {
          type: "tool-read_workspace_file" as const,
          toolCallId: "call_1",
          state: "output-available" as const,
          input: { filePath: "package.json" },
          output: { ok: true, filePath: "package.json", content: "", size: 0, truncated: false },
        },
      ],
    } as UIMessage;
    const merged = mergeSpiritToolActivityCardsForMessage(msg);
    const one = merged.find((x) => x.id === "toolpart_call_1");
    expect(one?.target).toBe("README.md");
  });
});

describe("toolUIPartsToActivityCards", () => {
  it("maps blocked list_workspace_files result to tool_blocked", () => {
    const parts: UIMessage["parts"] = [
      {
        type: "tool-list_workspace_files",
        toolCallId: "c2",
        state: "output-available",
        input: { directory: ".env.local" },
        output: { ok: false, code: "PATH_BLOCKED", message: "blocked file pattern" },
      },
    ];
    const cards = toolUIPartsToActivityCards(parts);
    expect(cards[0]?.kind).toBe("tool_blocked");
    expect(cards[0]?.status).toBe("blocked");
    expect(cards[0]?.safeMessage).toMatch(/blocked/i);
  });

  it("maps dev command confirmation to confirmation_required", () => {
    const parts: UIMessage["parts"] = [
      {
        type: "tool-run_dev_command",
        toolCallId: "c3",
        state: "output-available",
        input: { commandId: "npm_test", confirm: false },
        output: {
          ok: false,
          commandId: "npm_test",
          label: "npx vitest run",
          requiresConfirmation: true,
          message: "confirm first",
        },
      },
    ];
    const cards = toolUIPartsToActivityCards(parts);
    expect(cards[0]?.status).toBe("confirmation_required");
    expect(cards[0]?.target).toBe("npm_test");
  });
});
