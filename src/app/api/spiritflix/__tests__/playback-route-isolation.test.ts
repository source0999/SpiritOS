import fs from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";

const FORBIDDEN_PLAYBACK_IMPORTS = [
  "admin/smart/scanner",
  "face-organizer",
  "conversion-bridge",
  "converterServerQueue",
  "library-smart-rescan",
  "mobile-optimized",
];

describe("SpiritFlix playback route isolation", () => {
  it("keeps stream, HLS, gallery, and jobs list routes free of scan, face, move, and conversion work", async () => {
    const repoRoot = process.cwd();
    const routes = [
      path.join(repoRoot, "src/app/api/spiritflix/stream/route.ts"),
      path.join(repoRoot, "src/app/api/spiritflix/hls/route.ts"),
      path.join(repoRoot, "src/app/api/spiritflix/gallery/route.ts"),
      path.join(repoRoot, "src/app/api/spiritflix/gallery/image/route.ts"),
      path.join(repoRoot, "src/app/api/spiritflix/admin/jobs/route.ts"),
    ];

    for (const routePath of routes) {
      const source = await fs.readFile(routePath, "utf8");
      FORBIDDEN_PLAYBACK_IMPORTS.forEach((forbidden) => {
        expect(source, `${path.basename(path.dirname(routePath))} route should not reference ${forbidden}`).not.toContain(forbidden);
      });
    }
  });
});
