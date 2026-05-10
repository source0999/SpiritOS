import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("spirit-trinity-chat.css thread rail (compact / no chunky grid hacks)", () => {
  const css = readFileSync(
    resolve(process.cwd(), "src/styles/spirit-trinity-chat.css"),
    "utf8",
  );

  it("does not force legacy 2.125rem action chrome on recent thread rows", () => {
    expect(css).not.toMatch(/2\.125rem/);
  });

  it("keeps a subtle active accent for trinity-recent rows", () => {
    expect(css).toMatch(/\[data-action-layout="trinity-recent"\]\[data-active="true"\]/);
    expect(css).toMatch(/inset 2px 0 0 rgba\(99, 216, 248/);
  });

  it("uses coarse-pointer media for larger touch targets where needed", () => {
    expect(css).toMatch(/@media \(pointer: coarse\)/);
  });
});
