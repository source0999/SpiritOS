import { describe, it, expect, vi, afterEach } from "vitest";
import { GET } from "../route";
import type { CapabilityRegistryResponse } from "@/lib/server/capabilities/types";

vi.mock("@/lib/server/capabilities/get-capabilities", () => ({
  getCapabilityRegistry: vi.fn().mockResolvedValue({
    ok: true,
    collectedAt: "2026-05-04T12:00:00.000Z",
    host: { id: "host-a", label: "Host A", source: "local" },
    nodes: [],
    tools: [
      { name: "get_capabilities", enabled: true, readOnly: true, requiresApproval: false },
      { name: "list_nodes", enabled: true, readOnly: true, requiresApproval: false },
      { name: "get_node_status", enabled: true, readOnly: true, requiresApproval: false },
    ],
  }),
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("GET /api/telemetry/capabilities", () => {
  it("returns Cache-Control: no-store", async () => {
    const res = await GET();
    expect(res.headers.get("Cache-Control")).toBe("no-store");
  });

  it("returns tools get_capabilities, list_nodes, get_node_status", async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    const json = (await res.json()) as CapabilityRegistryResponse;
    const names = json.tools.map((t) => t.name).sort();
    expect(names).toEqual(["get_capabilities", "get_node_status", "list_nodes"]);
    expect(json.tools.every((t) => t.enabled && t.readOnly && !t.requiresApproval)).toBe(true);
  });
});
