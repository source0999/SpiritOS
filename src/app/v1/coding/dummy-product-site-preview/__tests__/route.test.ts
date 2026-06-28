/// <reference types="vitest/globals" />

import { readFile } from "node:fs/promises";

import { resolveFixturePath, serveFixtureAsset } from "../_handler";

vi.mock("node:fs/promises", () => ({
  readFile: vi.fn(),
}));

const mockedReadFile = vi.mocked(readFile);

function asErrnoError(code: string): NodeJS.ErrnoException {
  const err = new Error(`${code}: no such file`) as NodeJS.ErrnoException;
  err.code = code;
  return err;
}

describe("coding dummy-product-site preview handler", () => {
  beforeEach(() => {
    mockedReadFile.mockReset();
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
    mockedReadFile.mockResolvedValueOnce(
      '<!doctype html><html><head><title>LumaCart</title><link rel="stylesheet" href="src/styles.css"></head><body><h1>LumaCart</h1><script src="src/main.js"></script></body></html>',
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
  });

  it("serves relative fixture assets (src/styles.css, src/main.js) with correct content types", async () => {
    mockedReadFile.mockResolvedValueOnce("body { color: #111; }");
    const css = await serveFixtureAsset("src/styles.css");
    expect(css.status).toBe(200);
    expect(css.headers.get("content-type")).toContain("text/css");

    mockedReadFile.mockResolvedValueOnce("console.log('LumaCart');");
    const js = await serveFixtureAsset("src/main.js");
    expect(js.status).toBe(200);
    expect(js.headers.get("content-type")).toContain("text/javascript");
  });

  it("returns 404 when a fixture asset is missing on disk", async () => {
    mockedReadFile.mockRejectedValueOnce(asErrnoError("ENOENT"));
    const response = await serveFixtureAsset("src/missing.js");
    expect(response.status).toBe(404);
    const text = await response.text();
    expect(text).toContain("not found on disk");
  });

  it("reports an honest empty-fixture state instead of faking a page", async () => {
    mockedReadFile.mockResolvedValueOnce("   ");
    const response = await serveFixtureAsset(null);
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(text).toContain("empty");
  });

  it("leaves scripts that already declare a type untouched", async () => {
    mockedReadFile.mockResolvedValueOnce(
      '<html><body><script type="application/json" src="data.json"></script></body></html>',
    );
    const response = await serveFixtureAsset(null);
    const text = await response.text();
    expect(text).toContain('type="application/json"');
    expect(text).not.toContain('type="module"');
  });
});
