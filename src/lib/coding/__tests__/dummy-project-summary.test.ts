import { describe, expect, it } from "vitest";

import { buildExistingDummyProjectSummary } from "@/lib/coding/dummy-project-summary";

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
});
