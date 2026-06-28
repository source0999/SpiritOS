/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { GET } from "../route";

vi.mock("@/lib/source-proxy-origin", () => ({
  sourceProxyFetch: vi.fn(),
}));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);

function proxyResponse(body: unknown, status = 200) {
  return {
    headers: new Headers({ "content-type": "application/json" }),
    status,
    statusText: status === 200 ? "OK" : "Error",
    text: async () => JSON.stringify(body),
    json: async () => body,
    ok: status >= 200 && status < 300,
  } as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>;
}

describe("coding dummy-product-site preview route", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("serves the LumaCart index.html as a viewable HTML page", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse({
        content:
          "<!doctype html><html><head><title>LumaCart</title></head><body><h1>LumaCart</h1></body></html>",
      }),
    );

    const response = await GET();
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    const text = await response.text();
    expect(text).toContain("<h1>LumaCart</h1>");
    // It must forward a read for the fixture index.html.
    expect(mockedSourceProxyFetch).toHaveBeenCalledTimes(1);
  });

  it("returns 404 when the fixture index.html is missing", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse("file not found", 404),
    );

    const response = await GET();
    expect(response.status).toBe(404);
  });

  it("refuses to serve when Source Proxy is off", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");
    const response = await GET();
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("reports an honest empty-fixture state instead of faking a page", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(proxyResponse({ content: "" }));

    const response = await GET();
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(text).toContain("empty");
  });
});
