import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../actions/route";

describe("SpiritFlix admin actions route", () => {
  it("fails closed before any caller-controlled mutation request is interpreted", async () => {
    const response = await POST(new NextRequest("http://localhost/api/spiritflix/admin/actions", {
      body: JSON.stringify({ action: "softDelete", mode: "execute", sourcePath: "/outside" }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    }));
    expect(response.status).toBe(410);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_admin_direct_mutation_forbidden" });
  });
});
