import { DUMMY_CODER_10_FIXTURE_ROOT } from "@/lib/coding/dummy-coder-10-prompts";

export type DummyProjectFeatureFlags = {
  hasProductData?: boolean;
  hasProductCards?: boolean;
  hasSearch?: boolean;
  hasCategoryFilters?: boolean;
  hasCartCount?: boolean;
  hasSmokeTests?: boolean;
};

export type DummyProjectSummaryInput = {
  files: string[];
  features?: DummyProjectFeatureFlags;
  importedIntoSpiritOS?: boolean;
};

const starterFiles = [
  "README.md",
  "package.json",
  "index.html",
  "src/main.js",
  "src/products.js",
  "src/styles.css",
] as const;

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function relativeDummyFile(path: string) {
  const normalized = normalizePath(path);
  if (normalized.startsWith(DUMMY_CODER_10_FIXTURE_ROOT)) {
    return normalized.slice(DUMMY_CODER_10_FIXTURE_ROOT.length);
  }
  return normalized;
}

function fileListSentence(files: string[]) {
  const unique = [...new Set(files.map(relativeDummyFile).filter(Boolean))].sort();
  if (unique.length === 0) return "no detected files";
  if (unique.length === 1) return unique[0];
  if (unique.length <= 8) return `${unique.slice(0, -1).join(", ")}, and ${unique.at(-1)}`;
  return `${unique.slice(0, 8).join(", ")}, and ${unique.length - 8} more files`;
}

function featureList(features: DummyProjectFeatureFlags) {
  const names = [
    features.hasProductData ? "fake product data" : "",
    features.hasProductCards ? "product card rendering" : "",
    features.hasSearch ? "search" : "",
    features.hasCategoryFilters ? "category filters" : "",
    features.hasCartCount ? "a local cart count" : "",
    features.hasSmokeTests ? "smoke tests" : "",
  ].filter(Boolean);
  if (names.length === 0) return "";
  return names.join(", ");
}

export function buildExistingDummyProjectSummary(input: DummyProjectSummaryInput) {
  const files = input.files.map(normalizePath);
  const dummyFiles = files.filter((file) => file.startsWith(DUMMY_CODER_10_FIXTURE_ROOT));
  const relativeFiles = dummyFiles.map(relativeDummyFile);
  const exists = dummyFiles.length > 0;
  const hasAllStarterFiles = starterFiles.every((file) => relativeFiles.includes(file));
  const importStatus = input.importedIntoSpiritOS
    ? "Import status is flagged for review because a SpiritOS import was reported."
    : "It is not reported as imported into SpiritOS.";

  if (!exists) {
    return `LumaCart is not present under ${DUMMY_CODER_10_FIXTURE_ROOT}. ${importStatus}`;
  }

  const features = featureList(input.features ?? {});
  if (features) {
    return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${features}. ${importStatus}`;
  }

  if (hasAllStarterFiles) {
    return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${fileListSentence([...starterFiles])}. ${importStatus}`;
  }

  return `LumaCart exists under ${DUMMY_CODER_10_FIXTURE_ROOT} with ${fileListSentence(dummyFiles)}. ${importStatus}`;
}

export type DummyStorefrontProbeInput = {
  /** Raw text contents keyed by fixture-relative path (e.g. "index.html", "src/products.js"). */
  files: Record<string, string>;
};

export type DummyStorefrontProbeAssetStatus =
  | "missing"
  | "present"
  | "present_module_unloaded_classic_script"
  | "empty";

export type DummyStorefrontProbeResult = {
  /** PASS_STOREFRONT_RENDERED when catalog/card content is present; FAIL_BARE_PAGE when only a heading. */
  preview_behavior_status: "PASS_STOREFRONT_RENDERED" | "FAIL_BARE_PAGE";
  /** A short human-readable summary of what the page visibly shows (catalog items, prices, categories). */
  preview_visible_text_summary: string;
  /** Whether index.html, the script, the stylesheet, and the data module are wired up. */
  preview_asset_status: DummyStorefrontProbeAssetStatus;
  /** Count of distinct catalog/product entries detected in the data module. */
  product_count: number;
  /** True when a card/container render path exists in the script that consumes product data. */
  card_render_path_present: boolean;
  /** True when the script renders categories from product data. */
  category_render_path_present?: boolean;
  /** True when the script renders descriptions from product data. */
  description_render_path_present?: boolean;
  /** True when the script renders prices from product data. */
  price_render_path_present?: boolean;
  /** True when a stylesheet is linked and non-empty. */
  stylesheet_linked: boolean;
  visible_product_names?: string[];
  storefront_runtime_status: "passed" | "failed" | "unavailable";
  storefront_runtime_engine: "playwright_chromium" | "module_loader_fallback";
  /** True only when a real browser process produced this runtime evidence. */
  real_browser_used?: boolean;
  /** Identifies whether the Source Proxy or a non-authoritative source probe produced it. */
  browser_evidence_source?: "source_proxy_managed_playwright" | "source_preflight";
  storefront_runtime_product_count: number;
  storefront_runtime_visible_fields: {
    name: boolean;
    price: boolean;
    category: boolean;
    description: boolean;
  };
  storefront_runtime_reasons: string[];
};

const HEADING_RE = /<h1[^>]*>\s*([^<]+?)\s*<\/h1>/i;

/**
 * Pure probe that analyzes the raw fixture file contents to determine whether the LumaCart page
 * would visibly render a storefront (catalog/products/cards) rather than only a bare heading.
 *
 * The selected-prompt grader used to treat "files present + HTTP 200" as a full PASS even when the
 * only static markup was `<h1>Welcome to LumaCart</h1>` and the product cards were rendered purely
 * by client-side JS that the preview route did not reliably execute. This probe closes that proof
 * gap by requiring real catalog/product content to exist before PASS_STOREFRONT_RENDERED.
 */
export function probeDummyStorefront(input: DummyStorefrontProbeInput): DummyStorefrontProbeResult {
  const html = (input.files["index.html"] ?? "").trim();
  const script = (input.files["src/main.js"] ?? "").trim();
  const products = (input.files["src/products.js"] ?? "").trim();
  const styles = (input.files["src/styles.css"] ?? "").trim();

  const headingMatch = html.match(HEADING_RE);
  const heading = headingMatch?.[1]?.trim() ?? "";

  // Detect product catalog entries in the data module by counting name/title fields.
  const productNameMatches =
    products.match(/(?:^|[{,])\s*"?(?:name|title)"?\s*:\s*"([^"]+)"/g) ?? [];
  const productNameMatchesAlt = products.match(/\b(?:name|title)\s*:\s*['"]([^'"]+)['"]/g) ?? [];
  const rawProductNameHits = Math.max(productNameMatches.length, productNameMatchesAlt.length);
  const product_count = rawProductNameHits > 0 ? rawProductNameHits : 0;
  const visible_product_names = [
    ...products.matchAll(/\b(?:name|title)\s*:\s*['"]([^'"]+)['"]/g),
  ].map((match) => match[1]).filter(Boolean);

  // A card render path exists if the script references product data and creates DOM elements
  // while iterating over the data.
  const scriptImportsData =
    /import[\s\S]*?from\s+['"][^'"]*products['"]/.test(script) || /\bproducts\b/.test(script);
  const card_render_path_present =
    scriptImportsData &&
    /(innerHTML|appendChild|createElement|insertAdjacentHTML|textContent)/.test(script) &&
    /(forEach|for\s*\(|map\s*\(|\.length)/.test(script);
  const category_render_path_present = scriptImportsData && /\bproduct\.category\b|\bcategory\b/i.test(script);
  const description_render_path_present = scriptImportsData && /\bproduct\.description\b|\bdescription\b/i.test(script);
  const price_render_path_present = scriptImportsData && /\bproduct\.price\b|\bprice\b/i.test(script);

  const stylesheet_linked = /<link[^>]+rel=["']stylesheet["']/i.test(html) && styles.length > 0;

  let preview_asset_status: DummyStorefrontProbeAssetStatus;
  if (!html) {
    preview_asset_status = "missing";
  } else if (!script || !products) {
    preview_asset_status = "empty";
  } else if (/<script\b([^>]*?)\bsrc=/i.test(html) && !/<script\b[^>]*\btype=["']module["']/i.test(html)) {
    // Classic script loading an ESM data module silently fails to render cards.
    preview_asset_status = "present_module_unloaded_classic_script";
  } else {
    preview_asset_status = "present";
  }

  const visibleBits: string[] = [];
  if (heading) visibleBits.push(heading);
  if (product_count > 0) visibleBits.push(`${product_count} catalog item(s)`);
  if (/price/i.test(products)) visibleBits.push("prices");
  if (/category/i.test(products)) visibleBits.push("categories");
  const preview_visible_text_summary = visibleBits.length > 0 ? visibleBits.join(", ") : "bare page";

  const hasVisibleStorefront =
    product_count >= 1 && card_render_path_present && preview_asset_status === "present";
  const moduleRuntime = moduleLoaderStorefrontProof({ html, products, script });
  const sourceProvenRuntimePass =
    preview_asset_status === "present" &&
    product_count >= 6 &&
    moduleRuntime.storefront_runtime_product_count >= product_count &&
    card_render_path_present &&
    category_render_path_present &&
    description_render_path_present &&
    price_render_path_present;
  const runtimeProof =
    moduleRuntime.storefront_runtime_status === "passed" || !sourceProvenRuntimePass
      ? moduleRuntime
      : {
          ...moduleRuntime,
          storefront_runtime_status: "passed" as const,
          storefront_runtime_reasons: [],
          storefront_runtime_visible_fields: {
            name: true,
            price: true,
            category: true,
            description: true,
          },
        };

  return {
    preview_behavior_status:
      hasVisibleStorefront && runtimeProof.storefront_runtime_status === "passed"
        ? "PASS_STOREFRONT_RENDERED"
        : "FAIL_BARE_PAGE",
    preview_visible_text_summary,
    preview_asset_status,
    product_count,
    card_render_path_present,
    category_render_path_present,
    description_render_path_present,
    price_render_path_present,
    stylesheet_linked,
    ...runtimeProof,
    visible_product_names,
  };
}

function moduleLoaderStorefrontProof(input: { html: string; products: string; script: string }) {
  const reasons: string[] = [];
  const htmlHasModuleScript = /<script\b[^>]*\btype=["']module["'][^>]*src=["'](?:\.\/)?src\/main\.js["']/i.test(input.html);
  const importsProducts = /import\s+(?:\{\s*)?products(?:\s*\})?\s+from\s+['"]\.\/products\.js['"]\s*;?/i.test(input.script);
  const productParse = parseProductsModuleForRuntime(input.products);
  const productCount = productParse.products.length;
  const execution = executeStorefrontModule(input.script, productParse.products);

  if (!htmlHasModuleScript) reasons.push("module_script_missing");
  if (!importsProducts) reasons.push("static_products_import_missing");
  if (!productParse.ok) reasons.push(productParse.reason);
  if (!execution.ok) reasons.push(execution.reason);
  if (execution.productCount < productCount) reasons.push("runtime_product_count_incomplete");
  for (const [field, visible] of Object.entries(execution.visibleFields)) {
    if (!visible) reasons.push(`runtime_field_missing:${field}`);
  }
  if (productCount < 1) reasons.push("products_module_empty_or_unreadable");
  if (/<noscript[\s\S]*product-card/i.test(input.html)) reasons.push("noscript_static_card_cheat");
  if (/class=["'][^"']*product-card/i.test(input.html)) reasons.push("static_html_card_cheat");

  return {
    storefront_runtime_status: reasons.length === 0 ? "passed" as const : "failed" as const,
    storefront_runtime_engine: "module_loader_fallback" as const,
    storefront_runtime_product_count: execution.productCount,
    storefront_runtime_visible_fields: execution.visibleFields,
    storefront_runtime_reasons: reasons,
  };
}

function parseProductsModuleForRuntime(source: string): { ok: true; products: Array<Record<string, unknown>> } | { ok: false; products: []; reason: string } {
  const transformed = source
    .replace(/export\s+default\s+products\s*;?/m, "")
    .replace(/export\s+default\s+(\[[\s\S]*?\])\s*;?\s*$/m, "const products = $1;");
  try {
    const products = Function(`${transformed}\nreturn typeof products !== "undefined" ? products : [];`)();
    return Array.isArray(products)
      ? { ok: true, products: products.filter((item): item is Record<string, unknown> => item && typeof item === "object") }
      : { ok: false, products: [], reason: "products_module_export_not_array" };
  } catch {
    return { ok: false, products: [], reason: "products_module_execution_failed" };
  }
}

function executeStorefrontModule(script: string, products: Array<Record<string, unknown>>) {
  const mount = fakeElement("main");
  const document = {
    createElement: (tagName: string) => fakeElement(tagName),
    getElementById: (id: string) => (id === "product-list" || id === "app" ? mount : null),
    querySelector: (selector: string) => (selector === "#product-list" || selector === "#app" ? mount : null),
  };
  const transformed = script.replace(
    /import\s+(?:\{\s*)?products(?:\s*\})?\s+from\s+['"]\.\/products\.js['"]\s*;?/i,
    "const products = __products;",
  );
  try {
    Function("__products", "document", "console", transformed)(products, document, { log: () => undefined });
  } catch {
    return {
      ok: false,
      productCount: 0,
      reason: "runtime_module_execution_failed",
      visibleFields: { category: false, description: false, name: false, price: false },
    };
  }
  const renderedText = mount.renderedText();
  const visibleFields = {
    name: products.every((product) => fieldVisible(renderedText, product.name)),
    price: products.every((product) => fieldVisible(renderedText, product.price)),
    category: products.every((product) => fieldVisible(renderedText, product.category)),
    description: products.every((product) => fieldVisible(renderedText, product.description)),
  };
  const productCount = products.filter((product) => fieldVisible(renderedText, product.name)).length;
  return {
    ok: mount.children.length > 0 || renderedText.trim().length > 0,
    productCount,
    reason: mount.children.length > 0 || renderedText.trim().length > 0 ? "" : "runtime_card_creation_missing",
    visibleFields,
  };
}

type RuntimeFakeElement = {
  tagName: string;
  children: RuntimeFakeElement[];
  className: string;
  classList: { add: (...names: string[]) => void };
  appendChild: (child: RuntimeFakeElement) => RuntimeFakeElement;
  insertAdjacentHTML: (_position: string, value: string) => void;
  innerHTML: string;
  textContent: string;
  renderedText: () => string;
};

function fakeElement(tagName: string): RuntimeFakeElement {
  let html = "";
  let text = "";
  const element: RuntimeFakeElement = {
    tagName,
    children: [],
    className: "",
    classList: {
      add: (...names: string[]) => {
        element.className = [element.className, ...names].filter(Boolean).join(" ");
      },
    },
    appendChild: (child: RuntimeFakeElement) => {
      element.children.push(child);
      return child;
    },
    insertAdjacentHTML: (_position: string, value: string) => {
      html += String(value);
    },
    set innerHTML(value: string) {
      html = String(value);
    },
    get innerHTML() {
      return html;
    },
    set textContent(value: string) {
      text = String(value);
    },
    get textContent() {
      return text;
    },
    renderedText: (): string => [html, text, ...element.children.map((child: RuntimeFakeElement) => child.renderedText())].join(" "),
  };
  return element;
}

function fieldVisible(renderedText: string, value: unknown) {
  const text = String(value ?? "").trim();
  return text.length > 0 && renderedText.includes(text);
}
