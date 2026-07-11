/// <reference types="vitest/globals" />

import { resolveFixturePath, serveFixtureAsset } from "../_handler";

const readFileMock = vi.hoisted(() => vi.fn());

vi.mock("node:fs/promises", () => ({
  default: {
    readFile: readFileMock,
  },
  readFile: readFileMock,
}));

const mockedReadFile = vi.mocked(readFileMock);

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

  it("serves the model-authored index without injecting product cards", async () => {
    mockedReadFile.mockImplementation(async (target: unknown) => {
      const p = String(target).replace(/\\/g, "/");
      if (p.endsWith("index.html")) {
        return '<!doctype html><html><head><title>LumaCart</title><link rel="stylesheet" href="src/styles.css"></head><body><header><h1>Welcome to LumaCart</h1></header><main id="product-list"></main><script type="module" src="src/main.js"></script></body></html>';
      }
      if (p.endsWith("src/products.js")) {
        return "const products = [\n  { name: 'Product A', category: 'Demo', description: 'This is product A.', price: 19.99 },\n  { name: 'Product B', category: 'Demo', description: 'This is product B.', price: 29.99 },\n  { name: 'Product C', category: 'Demo', description: 'This is product C.', price: 9.99 },\n  { name: 'Product D', category: 'Demo', description: 'This is product D.', price: 12.99 },\n  { name: 'Product E', category: 'Demo', description: 'This is product E.', price: 14.99 },\n  { name: 'Product F', category: 'Demo', description: 'This is product F.', price: 16.99 }\n];\nexport default products;";
      }
      if (p.endsWith("src/main.js")) {
        return "import products from './products.js'; products.forEach(p => { const e = document.createElement('div'); e.className = 'product-card'; e.innerHTML = `<h2>${p.name}</h2><p>${p.category}</p><p>${p.description}</p><p>$${p.price}</p>`; document.getElementById('product-list').appendChild(e); });";
      }
      if (p.endsWith("src/styles.css")) {
        return "body { font-family: Arial; } div { border: 1px solid #ddd; }";
      }
      throw asErrnoError("ENOENT");
    });

    const response = await serveFixtureAsset(null);
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    const text = await response.text();
    // Static heading still present.
    expect(text).toContain("<h1>Welcome to LumaCart</h1>");
    // The preview route must not synthesize cards from products.js. Runtime proof belongs to the
    // managed Chromium verifier and must fail if the model-authored module does not render.
    expect(text).not.toContain('class="product-card"');
    expect(text).not.toContain("Product A");
    expect(text).not.toContain("<noscript>");
    // The model-authored client module remains the only rendering path.
    expect(text).toContain('href="/v1/coding/dummy-product-site-preview/src/styles.css"');
    expect(text).toMatch(
      /<script\b[^>]*type="module"[^>]*src="\/v1\/coding\/dummy-product-site-preview\/src\/main\.js"/,
    );
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

  it("does not repair a broken classic script into a module", async () => {
    mockedReadFile.mockResolvedValueOnce(
      '<html><body><div id="app"></div><script src="src/main.js"></script></body></html>',
    );
    const response = await serveFixtureAsset(null);
    const text = await response.text();
    expect(text).toContain(
      '<script src="/v1/coding/dummy-product-site-preview/src/main.js">',
    );
    expect(text).not.toContain('type="module"');
  });
});
