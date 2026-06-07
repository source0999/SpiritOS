import { describe, expect, it, vi } from "vitest";

import {
  buildAgentLabBaselineSnapshot,
  readWorkspaceFileContent,
  sweepAgentLabBaselineServer,
  sweepAgentLabLeftoverFilesServer,
} from "@/lib/coding/agent-lab-baseline-server";
import { sourceProxyFetch, sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
  sourceProxyLongJsonFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);
const mockedSourceProxyLongJsonFetch = vi.mocked(sourceProxyLongJsonFetch);
const proxyResponse = (
  body?: BodyInit | null,
  init?: ResponseInit,
): Awaited<ReturnType<typeof sourceProxyFetch>> =>
  new Response(body, init) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>;

describe("agent-lab-baseline-server", () => {
  it("treats workspace read HTTP 400 as missing when the proxy says the file is gone", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse(JSON.stringify({ error: "path not found in workspace" }), { status: 400 }),
    );
    await expect(readWorkspaceFileContent("src/app/agent-lab/calculator/page.tsx")).resolves.toEqual({
      status: "missing",
    });
  });

  it("extracts task id from long-running task envelope and deletes agent-lab files", async () => {
    const fileContent = "export default function Page() { return null; }\n";
    mockedSourceProxyFetch
      .mockResolvedValueOnce(proxyResponse(JSON.stringify({ content: fileContent }), { status: 200 }))
      .mockResolvedValueOnce(proxyResponse(JSON.stringify({ content: fileContent }), { status: 200 }))
      .mockResolvedValueOnce(proxyResponse("", { status: 404 }));

    mockedSourceProxyLongJsonFetch
      .mockResolvedValueOnce(
        proxyResponse(
          JSON.stringify({
            task: { id: "task-cleanup-1", status: "running" },
            tool: "long_running_task_tracker",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(proxyResponse(JSON.stringify({ ok: true }), { status: 200 }));

    const result = await sweepAgentLabLeftoverFilesServer(["src/app/agent-lab/cards/page.tsx"]);
    expect(result.removed).toBe(1);
    expect(result.failures).toEqual([]);
    expect(mockedSourceProxyLongJsonFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-cleanup-1/execute-approved",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("does not keep a deleted unreverted receipt target dirty in the sweep response", async () => {
    let fileExists = true;
    const fileContent = "export default function AgentLabPage() { return null; }\n";
    mockedSourceProxyFetch.mockImplementation(async (path, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as { path?: string } : {};
      if (path === "/v1/workspace/list") {
        return proxyResponse(
          JSON.stringify({
            entries:
              body.path === "src/app/agent-lab" && fileExists
                ? [{ kind: "file", path: "src/app/agent-lab/page.tsx" }]
                : [],
          }),
          { status: 200 },
        );
      }
      if (path === "/v1/workspace/read") {
        if (body.path === "src/app/agent-lab/page.tsx" && fileExists) {
          return proxyResponse(JSON.stringify({ content: fileContent }), { status: 200 });
        }
        return proxyResponse(JSON.stringify({ error: "path not found in workspace" }), { status: 404 });
      }
      return proxyResponse(JSON.stringify({ error: "unexpected" }), { status: 500 });
    });
    mockedSourceProxyLongJsonFetch.mockImplementation(async (path) => {
      if (path === "/v1/tasks/long-running") {
        return proxyResponse(JSON.stringify({ task: { id: "task-cleanup-2" } }), { status: 200 });
      }
      if (path === "/v1/tasks/long-running/task-cleanup-2/execute-approved") {
        fileExists = false;
        return proxyResponse(JSON.stringify({ ok: true }), { status: 200 });
      }
      return proxyResponse(JSON.stringify({ error: "unexpected" }), { status: 500 });
    });

    const result = await sweepAgentLabBaselineServer(["src/app/agent-lab/page.tsx"]);

    expect(result.removed).toBe(1);
    expect(result.snapshot).toMatchObject({
      baseline_agent_lab_files: [],
      baseline_clean_for_fresh_suite: true,
      baseline_dirty_agent_lab_files: [],
      baseline_unreverted_receipts: [],
    });
  });

  it("does not treat stale local receipt targets as baseline leftovers when files are gone", async () => {
    mockedSourceProxyFetch.mockImplementation(async (path, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as { path?: string } : {};
      if (path === "/v1/workspace/list") {
        return proxyResponse(JSON.stringify({ entries: [] }), { status: 200 });
      }
      if (path === "/v1/workspace/read") {
        return proxyResponse(
          JSON.stringify({ error: `${body.path ?? "path"} not found in workspace` }),
          { status: 404 },
        );
      }
      return proxyResponse(JSON.stringify({ error: "unexpected" }), { status: 500 });
    });

    await expect(buildAgentLabBaselineSnapshot(["src/app/agent-lab/page.tsx"])).resolves.toMatchObject({
      baseline_agent_lab_files: [],
      baseline_clean_for_fresh_suite: true,
      baseline_dirty_agent_lab_files: [],
      baseline_unreverted_receipts: [],
    });
  });
});
