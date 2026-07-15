import { describe, expect, it } from "vitest";

import { assertAuthoritativeFileCeilings } from "../context/authoritative-file-ceilings.mjs";

describe("authoritative context file ceilings", () => {
  it("accepts the registered ceilings", () => {
    expect(() => assertAuthoritativeFileCeilings()).not.toThrow();
  });

  it("fails visibly when a ceiling is exceeded", () => {
    expect(() => assertAuthoritativeFileCeilings({ maxBytesOverride: 1 })).toThrow(
      "AUTHORITATIVE_FILE_SIZE_CEILING_EXCEEDED",
    );
  });
});
