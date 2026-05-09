import { describe, expect, it } from "vitest";

import { buildAllowedDevOrigins } from "./allowed-dev-origins";

describe("buildAllowedDevOrigins", () => {
  it("includes defaults and env extras without duplicates", () => {
    const list = buildAllowedDevOrigins({
      NEXT_ALLOWED_DEV_ORIGINS: "mybox.ts.net, 100.111.32.31 ,custom.local",
    });
    expect(list).toContain("localhost");
    expect(list).toContain("100.111.32.31");
    expect(list).toContain("*.ts.net");
    expect(list).toContain("mybox.ts.net");
    expect(list.filter((h) => h === "100.111.32.31")).toHaveLength(1);
  });

  it("works with empty env override", () => {
    const list = buildAllowedDevOrigins({});
    expect(list.length).toBeGreaterThanOrEqual(5);
  });
});
