import { beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "../actions/route";
import { clearSpiritFlixAdminPreviewStore, getSmokeRoot, handleSpiritFlixAdminAction } from "@/lib/spiritflix/admin/actions";

vi.mock("@/lib/spiritflix/admin/actions", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/spiritflix/admin/actions")>();
  return {
    ...actual,
    handleSpiritFlixAdminAction: vi.fn(actual.handleSpiritFlixAdminAction),
  };
});

describe("SpiritFlix admin actions route", () => {
  beforeEach(() => {
    clearSpiritFlixAdminPreviewStore();
    vi.mocked(handleSpiritFlixAdminAction).mockClear();
  });

  it("rejects invalid JSON", async () => {
    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/actions", {
        method: "POST",
        body: "not-json",
      }) as never,
    );
    expect(response.status).toBe(400);
  });

  it("rejects missing action", async () => {
    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "preview" }),
      }) as never,
    );
    expect(response.status).toBe(400);
  });

  it("POST preview does not require confirm token", async () => {
    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "createFolder",
          mode: "preview",
          parentPath: getSmokeRoot(),
          name: "route-preview-folder",
        }),
      }) as never,
    );
    const payload = await response.json();
    expect(handleSpiritFlixAdminAction).toHaveBeenCalled();
    expect(payload.previewId).toBeTruthy();
  });

  it("POST execute requires confirmation token", async () => {
    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "createFolder",
          mode: "execute",
          confirmToken: "missing",
          parentPath: getSmokeRoot(),
          name: "route-exec-folder",
        }),
      }) as never,
    );
    const payload = await response.json();
    expect(payload.allowed).toBe(false);
  });

  it("rejects unsafe paths through the action engine", async () => {
    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "softDelete",
          mode: "preview",
          sourcePath: "/mnt/spirit-8tb/media",
        }),
      }) as never,
    );
    const payload = await response.json();
    expect(payload.allowed).toBe(false);
    expect(response.status).toBe(400);
  });
});
