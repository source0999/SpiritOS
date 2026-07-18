import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../actions/route";

describe("SpiritFlix admin actions route", () => {
  it("rejects requests without an approval_id", async () => {
    const response = await POST(new NextRequest("http://localhost/api/spiritflix/admin/actions", {
      body: JSON.stringify({ action: "softDelete", mode: "execute", sourcePath: "/outside" }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    }));
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ reason_code: "spiritflix_admin_approval_missing" });
  });

  it("rejects forged or invalid approval_id without executing the mutation", async () => {
    const response = await POST(new NextRequest("http://localhost/api/spiritflix/admin/actions", {
      body: JSON.stringify({ action: "softDelete", mode: "execute", sourcePath: "/outside", approval_id: "forged-nonexistent-approval" }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    }));
    expect(response.status).toBeGreaterThanOrEqual(400);
    const body = await response.json();
    expect(body.reason_code ?? body.error).toBeTruthy();
  });
});
