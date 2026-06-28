/// <reference types="vitest/globals" />

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { resolveFixturePath, serveFixtureAsset } from "../_handler";

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

describe("coding dummy-product-site preview handler", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("resolves the root request to index.html", () => {
    expect(resolveFixturePath(null)).toBe(
      "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
    );
  });

  it("resolves relative asset sub-paths under the fixture root", () => {
    expect(resolveFixturePath("src/styles.css")).toBe(
      "tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
    );
    expect(resolveFixturePath("/src/main.js")).toBe(
      "tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
    );
  });

  it("rejects paths that try to escape the fixture root", () => {
    expect(resolveFixturePath("../../package.json")).toBeNull();
    expect(resolveFixturePath("/etc/passwd")).toBeNull();
    expect(resolveFixturePath("C:/Windows/system32")).toBeNull();
  });

  it("serves the LumaCart index.html as a viewable HTML page at the root", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse({
        content:
          "<!doctype html><html><head><title>LumaCart</title><link rel=\"stylesheet\" href=\"src/styles.css\"></head><body><h1>LumaCart</h1><script src=\"src/main.js\"></script></body></html>",
      }),
    );

    const response = await serveFixtureAsset(null);
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    const text = await response.text();
    expect(text).toContain("<h1>LumaCart</h1>");
    // The model-authored main.js uses ESM imports; the viewer must mark external scripts as
    // type="module" so the page is not blank.
    expect(text).toContain('<script type="module"  src="src/main.js">');
    expect(text).toContain('href="src/styles.css"');
    const body = JSON.parse(
      String((mockedSourceProxyFetch.mock.calls[0]?.[1]?.body as string) ?? "{}"),
    );
    expect(body.path).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/index.html");
  });

  it("serves relative fixture assets (src/styles.css, src/main.js) with correct content types", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(proxyResponse({ content: "body { color: #111; }" }));

    const css = await serveFixtureAsset("src/styles.css");
    expect(css.status).toBe(200);
    expect(css.headers.get("content-type")).toContain("text/css");

    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse({ content: "console.log('LumaCart');" }),
    );
    const js = await serveFixtureAsset("src/main.js");
    expect(js.status).toBe(200);
    expect(js.headers.get("content-type")).toContain("text/javascript");

    const jsBody = JSON.parse(
      String((mockedSourceProxyFetch.mock.calls[1]?.[1]?.body as string) ?? "{}"),
    );
    expect(jsBody.path).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js");
  });

  it("returns 404 when a fixture asset is missing", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(proxyResponse("file not found", 404));
    const response = await serveFixtureAsset("src/missing.js");
    expect(response.status).toBe(404);
  });

  it("refuses to serve when Source Proxy is off", async () => {
    vi.stubEnv("SPIRIT_CODING_USE_PROXY", "false");
    const response = await serveFixtureAsset(null);
    expect(response.status).toBe(409);
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("reports an honest empty-fixture state instead of faking a page", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(proxyResponse({ content: "" }));
    const response = await serveFixtureAsset(null);
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(text).toContain("empty");
  });

  it("leaves scripts that already declare a type untouched", async () => {
    mockedSourceProxyFetch.mockResolvedValueOnce(
      proxyResponse({
        content:
          "<html><body><script type=\"application/json\" src=\"data.json\"></script></body></html>",
      }),
    );
    const response = await serveFixtureAsset(null);
    const text = await response.text();
    expect(text).toContain('type="application/json"');
    expect(text).not.toContain("type=\"module\"");
  });
});
