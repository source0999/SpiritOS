/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { POST } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/actions/execute-approved", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("execute-approved route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("blocks approved file edits without a task_id", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        content: "new\n",
        target: "src/demo.ts",
      }),
    );

    await expect(response.json()).resolves.toEqual({
      error:
        "execute-approved requires task_id so Source Proxy can re-run verification before apply.",
    });
    expect(response.status).toBe(400);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("forwards task-backed approved diffs to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      {
        headers: new Headers({ "content-type": "application/json" }),
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify({ ok: true }),
      } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>,
    );

    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["src/demo.ts"],
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toEqual({ ok: true });
    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledTimes(1);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/tasks/long-running/task-123/execute-approved",
      expect.objectContaining({
        method: "POST",
      }),
    );
    const [, init] = mockedSourceProxyFetch.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toEqual({
      action: "modify file",
      allowed_files: ["src/demo.ts"],
      approved: true,
      approval_id: "approval-54865365133e9340",
      approved_by: "coding-ui",
      approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
      changed_files: ["src/demo.ts"],
      commit_authority: false,
      diff_hash: "fe27d77ea2ed4d425e08fda5fb202b554aff43e0b591c8477efa7ad86d7889fe",
      push_authority: false,
      target: "src/demo.ts",
    });
  });

  it("rejects approved diffs outside allowed_files before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["docs/safe.md"],
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      allowed_files: ["docs/safe.md"],
      changed_files: ["src/demo.ts"],
      error: "execute-approved approved_diff changed files are outside allowed_files.",
      unexpected_files: ["src/demo.ts"],
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects protected paths before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: [".env.local"],
        approved: true,
        approved_diff: "--- a/.env.local\n+++ b/.env.local\n@@ -1 +1 @@\n-old\n+new\n",
        target: ".env.local",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      changed_files: [".env.local"],
      error: "execute-approved rejected protected path in approved_diff.",
    });
    expect(response.status).toBe(403);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("rejects stale approval ids before forwarding", async () => {
    const response = await POST(
      jsonRequest({
        action: "modify file",
        allowed_files: ["src/demo.ts"],
        approval_id: "approval-stale",
        approved: true,
        approved_diff: "--- a/src/demo.ts\n+++ b/src/demo.ts\n@@ -1 +1 @@\n-old\n+new\n",
        target: "src/demo.ts",
        task_id: "task-123",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      error:
        "execute-approved approval_id does not match task_id, target, and approved_diff.",
      expected_approval_id: "approval-54865365133e9340",
    });
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });
});
