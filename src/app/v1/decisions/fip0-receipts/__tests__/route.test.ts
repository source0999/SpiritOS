/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { GET as getByRunId } from "../[runId]/route";
import { GET as getTraceByRunId } from "../[runId]/trace/route";
import { GET as getLatest } from "../latest/route";
import { GET as getLatestTrace } from "../latest/trace/route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function proxyJson(body: unknown) {
  return {
    headers: new Headers({ "content-type": "application/json" }),
    status: 200,
    statusText: "OK",
    text: async () => JSON.stringify(body),
  } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>;
}

describe("FIP-0 receipt retrieval routes", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("proxies latest receipt retrieval to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyJson({
        run_id: "fip0-abc123",
        receipt: { run_id: "fip0-abc123" },
      }),
    );

    const response = await getLatest();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/decisions/fip0-receipts/latest",
      { method: "GET" },
    );
    expect(body.run_id).toBe("fip0-abc123");
  });

  it("proxies run-id receipt retrieval to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyJson({
        run_id: "fip0-deadbeef",
        receipt: { run_id: "fip0-deadbeef" },
      }),
    );

    const response = await getByRunId(
      new Request("http://localhost/v1/decisions/fip0-receipts/fip0-deadbeef"),
      { params: Promise.resolve({ runId: "fip0-deadbeef" }) },
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/decisions/fip0-receipts/fip0-deadbeef",
      { method: "GET" },
    );
    expect(body.run_id).toBe("fip0-deadbeef");
  });

  it("proxies latest operator trace retrieval to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyJson({
        run_id: "fip0-abc123",
        operator_trace: { run_metadata: { run_id: "fip0-abc123" } },
      }),
    );

    const response = await getLatestTrace();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/decisions/fip0-receipts/latest/trace",
      { method: "GET" },
    );
    expect(body.operator_trace.run_metadata.run_id).toBe("fip0-abc123");
  });

  it("proxies run-id operator trace retrieval to Source Proxy", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyJson({
        run_id: "fip0-deadbeef",
        operator_trace: { run_metadata: { run_id: "fip0-deadbeef" } },
      }),
    );

    const response = await getTraceByRunId(
      new Request("http://localhost/v1/decisions/fip0-receipts/fip0-deadbeef/trace"),
      { params: Promise.resolve({ runId: "fip0-deadbeef" }) },
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(mockedSourceProxyFetch).toHaveBeenCalledWith(
      "/v1/decisions/fip0-receipts/fip0-deadbeef/trace",
      { method: "GET" },
    );
    expect(body.operator_trace.run_metadata.run_id).toBe("fip0-deadbeef");
  });
});
