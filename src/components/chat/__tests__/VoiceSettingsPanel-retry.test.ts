import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("VoiceSettingsPanel retry affordance (Prompt 9J)", () => {
  it("exposes Retry / Refresh voices for catalog failures", () => {
    const p = resolve(process.cwd(), "src/components/chat/VoiceSettingsPanel.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("onRetryVoiceCatalog");
    expect(src).toContain("Retry / Refresh voices");
  });
});
