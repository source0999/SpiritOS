import { access, readFile, readdir } from "node:fs/promises";
import path from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

async function productionSourceFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(async (entry) => {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return entry.name === "__tests__" ? [] : productionSourceFiles(fullPath);
    }
    return /\.(?:ts|tsx)$/.test(entry.name) ? [fullPath] : [];
  }));
  return files.flat();
}

describe("canonical coding shell ownership", () => {
  it("keeps the design-demo compatibility route delegated to /coding", async () => {
    const source = await readFile(path.join(root, "src/app/design-demo/coding/page.tsx"), "utf8");
    expect(source).toContain('redirect("/coding")');
    expect(source).not.toContain("CodingAgentInterface");
  });

  it("embeds the canonical cockpit in chat without a second coding shell", async () => {
    const source = await readFile(path.join(root, "src/components/chat/SpiritTrinityChatShell.tsx"), "utf8");
    expect(source).toContain('import CodingCockpitShell from "@/components/coding/CodingCockpitShell"');
    expect(source).toContain("<CodingCockpitShell embedded />");
    expect(source).not.toContain("CodingAgentInterface");
  });

  it("has no production mount or import of the retired CodingAgentInterface", async () => {
    const files = (await Promise.all([
      productionSourceFiles(path.join(root, "src/app")),
      productionSourceFiles(path.join(root, "src/components")),
      productionSourceFiles(path.join(root, "src/lib")),
    ])).flat();
    const mounted = await Promise.all(files.map(async (file) => ({
      file: path.relative(root, file),
      source: await readFile(file, "utf8"),
    })));
    expect(mounted.filter(({ source }) => /(?:import|from).*CodingAgentInterface|<CodingAgentInterface\b/.test(source))).toEqual([]);
    await expect(access(path.join(root, "src/components/coding/CodingAgentInterface.tsx"))).rejects.toThrow();
    await expect(access(path.join(root, "labs/coding/CodingAgentInterface.tsx"))).resolves.toBeUndefined();
  });
});
