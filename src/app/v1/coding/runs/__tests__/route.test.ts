import { beforeEach, describe, expect, it, vi } from "vitest";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { GET as getRuns, POST as createRun } from "@/app/v1/coding/runs/route";
import { GET as getRun, PATCH as patchRun } from "@/app/v1/coding/runs/[runId]/route";
import { POST as upsertRow } from "@/app/v1/coding/runs/[runId]/rows/[promptId]/route";

vi.mock("@/lib/source-proxy-origin", () => ({ sourceProxyFetch: vi.fn() }));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

describe("read-only Next coding-run routes", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
  });

  it("rejects every local create, patch, and row mutation with backend ownership", async () => {
    const createResponse = await createRun(
      new Request("http://localhost/v1/coding/runs", {
        body: JSON.stringify({ status: "completed" }),
        method: "POST",
      }),
    );
    const patchResponse = await patchRun(
      new Request("http://localhost/v1/coding/runs/task-1", {
        body: JSON.stringify({ status: "completed" }),
        method: "PATCH",
      }),
      { params: Promise.resolve({ runId: "task-1" }) },
    );
    const rowResponse = await upsertRow(
      new Request("http://localhost/v1/coding/runs/task-1/rows/prompt-1", {
        body: JSON.stringify({ result_label: "PASS", status: "completed" }),
        method: "POST",
      }),
      { params: Promise.resolve({ promptId: "prompt-1", runId: "task-1" }) },
    );

    for (const response of [createResponse, patchResponse, rowResponse]) {
      expect(response.status).toBe(405);
      expect(response.headers.get("allow")).toBe("GET");
      await expect(response.json()).resolves.toMatchObject({
        error: "next_coding_run_mutation_forbidden",
        authority: { owner: "source_proxy", store: "long_running_tasks_sqlite" },
      });
    }
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("fails closed when Source Proxy truth is unavailable instead of serving cache", async () => {
    mockedSourceProxyFetch.mockRejectedValue(new Error("source proxy unavailable"));

    const listResponse = await getRuns(new Request("http://localhost/v1/coding/runs?limit=10"));
    const detailResponse = await getRun(
      new Request("http://localhost/v1/coding/runs/task-1"),
      { params: Promise.resolve({ runId: "task-1" }) },
    );

    for (const response of [listResponse, detailResponse]) {
      expect(response.status).toBe(502);
      await expect(response.json()).resolves.toMatchObject({
        error: "source_proxy_coding_run_projection_unavailable",
        authority: { owner: "source_proxy" },
      });
    }
  });
});
