/// <reference types="vitest/globals" />

import { mkdtempSync, readFileSync, rmSync } from "fs";
import os from "os";
import path from "path";

import {
  approvedFileContentFor,
  executeApprovedAction,
} from "@/lib/spirit/approved-action-execution";

describe("approved action execution", () => {
  let tmpRoot: string;

  beforeEach(() => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-approved-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    rmSync(tmpRoot, { recursive: true, force: true });
  });

  it("builds the approved design-demo coding page content", () => {
    expect(
      approvedFileContentFor(
        "create file",
        "src/app/design-demo/coding/page.tsx",
      ),
    ).toContain('redirect("/coding")');
  });

  it("creates the approved design-demo coding page through file-edit tools", async () => {
    const result = await executeApprovedAction({
      action: "create file",
      content: [
        'import { redirect } from "next/navigation";',
        "",
        "export default function DesignDemoCodingPage() {",
        '  redirect("/coding");',
        "}",
        "",
      ].join("\n"),
      target: "src/app/design-demo/coding/page.tsx",
    });

    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.message);

    const written = readFileSync(
      path.join(tmpRoot, "src/app/design-demo/coding/page.tsx"),
      "utf8",
    );
    expect(written).toContain('redirect("/coding")');
    expect(result.relativeFilePath).toBe("src/app/design-demo/coding/page.tsx");
  });

  it("creates a generic approved file from explicit content", async () => {
    const result = await executeApprovedAction({
      action: "create file",
      content: "export const approved = true;\n",
      target: "src/lib/generated-approved.ts",
    });

    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.message);

    const written = readFileSync(
      path.join(tmpRoot, "src/lib/generated-approved.ts"),
      "utf8",
    );
    expect(written).toBe("export const approved = true;\n");
  });

  it("rejects approved actions without executable content", async () => {
    const result = await executeApprovedAction({
      action: "create file",
      target: "src/app/unknown/page.tsx",
    });

    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected rejection");
    expect(result.code).toBe("NO_APPROVED_EXECUTION_TEMPLATE");
  });

  it("applies a unified diff when content is empty", async () => {
    const rel = "src/lib/__probe_approved_diff_target.txt";
    const abs = path.join(tmpRoot, rel);
    const dir = path.dirname(abs);
    const { mkdirSync, writeFileSync } = await import("fs");
    mkdirSync(dir, { recursive: true });
    writeFileSync(abs, "line1\nline2\n", "utf8");

    const patch = [
      `--- a/${rel}`,
      `+++ b/${rel}`,
      "@@ -1,2 +1,2 @@",
      "-line1",
      "+line1-patched",
      " line2",
      "",
    ].join("\n");

    const result = await executeApprovedAction({
      action: "modify file",
      approvedDiff: patch,
      content: "",
      target: rel,
    });

    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error(result.message);
    const written = readFileSync(abs, "utf8");
    expect(written).toBe("line1-patched\nline2\n");
  });
});
