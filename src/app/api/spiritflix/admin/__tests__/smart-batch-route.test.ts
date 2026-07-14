import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../smart/batch/route";

describe("SpiritFlix smart batch mutation route", () => {
  it("fails closed before interpreting a caller supplied action or root", async () => {
    const response = await POST(new NextRequest("http://localhost/api/spiritflix/admin/smart/batch", { body: JSON.stringify({ action: "run", path: "/outside", force: true }), method: "POST" }));
    expect(response.status).toBe(410);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_admin_direct_mutation_forbidden" });
  });
});
