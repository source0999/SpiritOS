import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("SpiritChat oracle contract", () => {
  it("threads sidebar only when persistence + workspace shell", () => {
    const p = resolve(process.cwd(), "src/components/chat/SpiritChat.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("savedChatShell && showThreadSidebar !== false");
    expect(src).toContain("oracleVoiceSurface");
    expect(src).toContain("OracleVoiceStatusCard");
  });

  it("/chat page still mounts workspace shell", () => {
    const p = resolve(process.cwd(), "src/app/chat/page.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("SpiritWorkspaceShell");
  });

  it("Oracle voice surface is standalone (no SpiritChat import)", () => {
    const p = resolve(process.cwd(), "src/components/oracle/OracleVoiceSurface.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).not.toContain('from "@/components/chat/SpiritChat"');
    expect(src).toContain("useSpiritChatTransport");
  });

  it("/oracle uses OracleVoiceSurface", () => {
    const p = resolve(process.cwd(), "src/app/oracle/page.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("OracleVoiceSurface");
  });
});