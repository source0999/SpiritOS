import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../smart/analysis/route";

describe("SpiritFlix smart analysis mutation route", () => {
  it("fails closed before interpreting a caller supplied path or action", async () => {
    const response = await POST(new NextRequest("http://localhost/api/spiritflix/admin/smart/analysis", { body: JSON.stringify({ action: "exportMetadata", path: "/outside" }), method: "POST" }));
    expect(response.status).toBe(410);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_admin_direct_mutation_forbidden" });
  });
});
