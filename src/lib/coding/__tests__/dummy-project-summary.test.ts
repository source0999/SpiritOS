import { describe, expect, it } from "vitest";

import { buildExistingDummyProjectSummary, probeDummyStorefront } from "@/lib/coding/target-plugins/lumacart/project-summary";

const root = "tests/ui-agent-trials/fixtures/dummy-product-site/";

describe("dummy project factual summary", () => {
  it("handles a missing LumaCart fixture with a short factual summary", () => {
    expect(buildExistingDummyProjectSummary({ files: [] })).toBe(
      "LumaCart is not present under tests/ui-agent-trials/fixtures/dummy-product-site/. It is not reported as imported into SpiritOS.",
    );
  });

  it("summarizes Prompt 001 starter files without dumping contents", () => {
    const summary = buildExistingDummyProjectSummary({
      files: [
        `${root}README.md`,
        `${root}package.json`,
        `${root}index.html`,
        `${root}src/main.js`,
        `${root}src/products.js`,
        `${root}src/styles.css`,
      ],
    });

    expect(summary).toBe(
      "LumaCart exists under tests/ui-agent-trials/fixtures/dummy-product-site/ with README.md, index.html, package.json, src/main.js, src/products.js, and src/styles.css. It is not reported as imported into SpiritOS.",
    );
  });

  it("summarizes detected feature flags deterministically", () => {
    const summary = buildExistingDummyProjectSummary({
      files: [`${root}src/main.js`, `${root}src/products.js`, `${root}src/cart.js`],
      features: {
        hasCartCount: true,
        hasCategoryFilters: true,
        hasProductCards: true,
        hasProductData: true,
        hasSearch: true,
        hasSmokeTests: true,
      },
    });

    expect(summary).toBe(
      "LumaCart exists under tests/ui-agent-trials/fixtures/dummy-product-site/ with fake product data, product card rendering, search, category filters, a local cart count, smoke tests. It is not reported as imported into SpiritOS.",
    );
  });

  it("flags reported SpiritOS imports for review", () => {
    expect(buildExistingDummyProjectSummary({ files: [`${root}index.html`], importedIntoSpiritOS: true })).toContain(
      "Import status is flagged for review",
    );
  });

  it("never reports 'not present' when dummy fixture files exist (no contradictory state)", () => {
    const summary = buildExistingDummyProjectSummary({
      files: [`${root}index.html`, `${root}src/main.js`],
    });

    // The contradiction to guard against: files present + "LumaCart is not present".
    expect(summary).toContain("LumaCart exists under");
    expect(summary).not.toContain("not present");
  });

  it("reports absent only when no dummy fixture files exist", () => {
    const summary = buildExistingDummyProjectSummary({ files: [] });

    expect(summary).toContain("LumaCart is not present");
    expect(summary).not.toContain("LumaCart exists");
  });
});

describe("dummy storefront probe", () => {
  const realFixture = {
    "index.html":
      '<!DOCTYPE html><html><head><title>LumaCart</title><link rel="stylesheet" href="src/styles.css"></head><body><header><h1>Welcome to LumaCart</h1></header><main id="product-list"></main><script type="module" src="src/main.js"></script></body></html>',
    "src/main.js":
      "import products from './products.js';\nconst productList = document.getElementById('product-list');\nproducts.forEach(product => { const e = document.createElement('div'); e.className = 'product-card'; e.innerHTML = `<h2>${product.name}</h2><p>${product.description}</p><p>${product.category}</p><p>$${product.price}</p>`; productList.appendChild(e); });",
    "src/products.js":
      "const products = [\n  { name: 'Product A', category: 'Lighting', description: 'This is product A.', price: 19.99 },\n  { name: 'Product B', category: 'Storage', description: 'This is product B.', price: 29.99 }\n];\nexport default products;",
    "src/styles.css": "body { font-family: Arial; } #product-list { display: flex; } div { border: 1px solid #ddd; }",
  };

  it("passes a real storefront fixture with catalog items and a card render path", () => {
    const probe = probeDummyStorefront({ files: realFixture });
    expect(probe.preview_behavior_status).toBe("PASS_STOREFRONT_RENDERED");
    expect(probe.product_count).toBe(2);
    expect(probe.card_render_path_present).toBe(true);
    expect(probe.category_render_path_present).toBe(true);
    expect(probe.description_render_path_present).toBe(true);
    expect(probe.price_render_path_present).toBe(true);
    expect(probe.stylesheet_linked).toBe(true);
    expect(probe.storefront_runtime_status).toBe("passed");
    expect(probe.storefront_runtime_engine).toBe("module_loader_fallback");
    expect(probe.storefront_runtime_product_count).toBe(2);
    expect(probe.storefront_runtime_visible_fields).toEqual({
      category: true,
      description: true,
      name: true,
      price: true,
    });
    expect(probe.visible_product_names).toEqual(["Product A", "Product B"]);
    expect(probe.preview_visible_text_summary).toContain("2 catalog item(s)");
  });

  it("fails a bare page with only a heading and no product data", () => {
    const probe = probeDummyStorefront({
      files: {
        "index.html": "<html><body><h1>Welcome to LumaCart</h1></body></html>",
        "src/main.js": "",
        "src/products.js": "",
        "src/styles.css": "",
      },
    });
    expect(probe.preview_behavior_status).toBe("FAIL_BARE_PAGE");
    expect(probe.product_count).toBe(0);
    expect(probe.storefront_runtime_status).toBe("failed");
    expect(probe.preview_visible_text_summary).toBe("Welcome to LumaCart");
  });

  it("flags a classic script that fails to load an ESM data module", () => {
    const probe = probeDummyStorefront({
      files: {
        ...realFixture,
        "index.html":
          '<html><body><h1>Welcome to LumaCart</h1><script src="src/main.js"></script></body></html>',
      },
    });
    expect(probe.preview_asset_status).toBe("present_module_unloaded_classic_script");
    expect(probe.preview_behavior_status).toBe("FAIL_BARE_PAGE");
    expect(probe.storefront_runtime_status).toBe("failed");
  });

  it("fails broken JS that only contains right-looking product tokens", () => {
    const probe = probeDummyStorefront({
      files: {
        ...realFixture,
        "src/main.js": "import products from './products.js'; products.forEach(product => product.price); appendChild;",
      },
    });

    expect(probe.preview_behavior_status).toBe("FAIL_BARE_PAGE");
    expect(probe.storefront_runtime_status).toBe("failed");
    expect(probe.storefront_runtime_reasons).toContain("runtime_module_execution_failed");
  });

  it("fails static HTML or noscript card cheats", () => {
    const probe = probeDummyStorefront({
      files: {
        ...realFixture,
        "index.html":
          '<html><body><main id="product-list"><article class="product-card">Product A</article></main><noscript><article class="product-card">Product B</article></noscript><script type="module" src="src/main.js"></script></body></html>',
        "src/main.js": "import products from './products.js'; console.log(products.length);",
      },
    });

    expect(probe.preview_behavior_status).toBe("FAIL_BARE_PAGE");
    expect(probe.storefront_runtime_status).toBe("failed");
    expect(probe.storefront_runtime_reasons).toEqual(
      expect.arrayContaining(["noscript_static_card_cheat", "runtime_card_creation_missing"]),
    );
  });
});
