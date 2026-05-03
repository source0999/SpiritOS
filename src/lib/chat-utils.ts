// ── Shared AI SDK message helpers ───────────────────────────────────────────
// > Design language: _blueprints/design_system.md — one source, zero dupes
import type { UIMessage } from "ai";

/** Pull plain text from v5 UI message parts (no duplicate implementations). */
export function textFromParts(message: UIMessage): string {
  return message.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");
}
