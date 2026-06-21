import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const workerPath = path.join(process.cwd(), "scripts/media-ingest-worker.mjs");

describe("media-ingest-worker MKV guardrails", () => {
  it("disables legacy Dell MKV output by default", () => {
    const source = fs.readFileSync(workerPath, "utf8");
    expect(source).toContain('process.env.MEDIA_INGEST_ENCODER || "disabled"');
    expect(source).toContain("MEDIA_INGEST_ALLOW_LEGACY_MKV_OUTPUT");
    expect(source).toContain("Legacy Dell HEVC/MKV media-ingest output is disabled");
  });

  it("keeps MKV publishing behind an explicit legacy escape hatch", () => {
    const source = fs.readFileSync(workerPath, "utf8");
    expect(source).toContain("ALLOW_LEGACY_MKV_OUTPUT === \"1\"");
    expect(source).toContain("Blocked legacy MKV live output candidate");
    expect(source).toContain('replace(/\\.[^.]+$/, ".mkv")');
  });
});
