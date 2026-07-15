import { ESLint } from "eslint";
import { describe, expect, it } from "vitest";

async function messagesFor(filePath: string, source: string) {
  const eslint = new ESLint({ cwd: process.cwd() });
  const [result] = await eslint.lintText(source, { filePath });
  return result.messages;
}

describe("Campaign 1 import boundary enforcement", () => {
  it("rejects a deliberate production-to-labs import", async () => {
    const messages = await messagesFor("src/components/coding/boundary-violation.ts", 'import "@/labs/legacy-shell";');
    expect(messages.some((message) => message.ruleId === "no-restricted-imports")).toBe(true);
  }, 30_000);

  it("rejects a deliberate product-to-product import", async () => {
    const messages = await messagesFor("src/components/coding/boundary-violation.ts", 'import "@/components/spiritflix/SpiritFlixPlayer";');
    expect(messages.some((message) => message.ruleId === "no-restricted-imports")).toBe(true);
  });

  it("rejects a deliberate production-to-fixture import", async () => {
    const messages = await messagesFor("src/components/coding/boundary-violation.ts", 'import "@/tests/fixtures/prompt-1";');
    expect(messages.some((message) => message.ruleId === "no-restricted-imports")).toBe(true);
  });
});
