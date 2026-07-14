#!/usr/bin/env node

import { chromium } from "@playwright/test";

const DEFAULT_MANAGED_ORIGIN = "https://localhost:3000";
const MANAGED_ORIGIN = managedOrigin();
const PREVIEW_PATH = "/v1/coding/dummy-product-site-preview";
const EXPECTED_ASSET_PATHS = [
  PREVIEW_PATH,
  `${PREVIEW_PATH}/src/main.js`,
  `${PREVIEW_PATH}/src/products.js`,
  `${PREVIEW_PATH}/src/styles.css`,
];

function argValue(name, fallback) {
  const prefix = `--${name}=`;
  const inline = process.argv.find((value) => value.startsWith(prefix));
  if (inline) return inline.slice(prefix.length);
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

function managedOrigin() {
  const candidate = String(process.env.SPIRITOS_E2E_FRONTEND_ORIGIN ?? "").trim().replace(/\/+$/, "");
  if (process.env.SPIRITOS_OPERATOR_E2E_MODE !== "true" || !candidate) return DEFAULT_MANAGED_ORIGIN;
  try {
    const parsed = new URL(candidate);
    if (
      parsed.protocol !== "https:" ||
      !["127.0.0.1", "localhost"].includes(parsed.hostname) ||
      !parsed.port ||
      parsed.port === "3000" ||
      parsed.username ||
      parsed.password ||
      parsed.pathname !== "/" ||
      parsed.search ||
      parsed.hash
    ) return DEFAULT_MANAGED_ORIGIN;
    return candidate;
  } catch {
    return DEFAULT_MANAGED_ORIGIN;
  }
}

function managedPreviewUrl() {
  const raw = argValue("url", `${MANAGED_ORIGIN}${PREVIEW_PATH}`);
  const parsed = new URL(raw);
  if (parsed.origin !== MANAGED_ORIGIN || parsed.pathname !== PREVIEW_PATH) {
    throw new Error(
      `managed_preview_url_required:${MANAGED_ORIGIN}${PREVIEW_PATH}`,
    );
  }
  parsed.searchParams.set("browser_proof", String(Date.now()));
  return parsed.toString();
}

function boundedTimeout() {
  const raw = Number(argValue("timeout-ms", "30000"));
  return Number.isFinite(raw) ? Math.max(5_000, Math.min(raw, 45_000)) : 30_000;
}

function responseStatusByPath(events, path) {
  const match = [...events].reverse().find((event) => {
    try {
      return new URL(event.url).pathname === path;
    } catch {
      return false;
    }
  });
  return match?.status ?? null;
}

async function main() {
  const previewUrl = managedPreviewUrl();
  const timeoutMs = boundedTimeout();
  const responses = [];
  const consoleErrors = [];
  const pageErrors = [];
  const requestFailures = [];
  let browser;

  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ ignoreHTTPSErrors: true });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text().slice(0, 500));
    });
    page.on("pageerror", (error) => pageErrors.push(String(error).slice(0, 500)));
    page.on("requestfailed", (request) => {
      requestFailures.push({
        error: request.failure()?.errorText ?? "request_failed",
        url: request.url(),
      });
    });
    page.on("response", (response) => {
      if (response.url().startsWith(MANAGED_ORIGIN)) {
        responses.push({ status: response.status(), url: response.url() });
      }
    });

    const navigation = await page.goto(previewUrl, {
      timeout: timeoutMs,
      waitUntil: "domcontentloaded",
    });
    await page.waitForFunction(
      () =>
        [...document.querySelectorAll(".product-card")].filter((element) => {
          const style = window.getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        }).length >= 6,
      undefined,
      { timeout: timeoutMs },
    );
    await page.waitForLoadState("networkidle", { timeout: timeoutMs });

    const productsUrl = `${MANAGED_ORIGIN}${PREVIEW_PATH}/src/products.js`;
    const dom = await page.evaluate(async ({ productsUrl: runtimeProductsUrl }) => {
      const normalize = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
      const visible = (element) => {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      const module = await import(runtimeProductsUrl);
      const products = Array.isArray(module.default)
        ? module.default
        : Array.isArray(module.products)
          ? module.products
          : [];
      const cards = [...document.querySelectorAll(".product-card")]
        .filter(visible)
        .map((card) => ({
          heading: normalize(card.querySelector("h1,h2,h3,h4")?.textContent),
          text: normalize(card.innerText || card.textContent),
        }));
      const productFieldMatches = products.map((product) => {
        const fields = {
          name: normalize(product?.name),
          price: normalize(product?.price),
          category: normalize(product?.category),
          description: normalize(product?.description),
        };
        const matchingCard = cards.find((card) =>
          Object.values(fields).every((value) => value && card.text.includes(value)),
        );
        return {
          fields_present: Object.values(fields).every(Boolean),
          name: fields.name,
          rendered: Boolean(matchingCard),
        };
      });
      return {
        document_ready_state: document.readyState,
        module_script_loaded: [...document.scripts].some(
          (script) => script.type === "module" && new URL(script.src).pathname.endsWith("/src/main.js"),
        ),
        noscript_card_count: document.querySelectorAll("noscript .product-card").length,
        product_count: products.length,
        product_field_matches: productFieldMatches,
        rendered_card_count: cards.length,
        rendered_headings: cards.map((card) => card.heading).filter(Boolean),
        stylesheet_loaded: [...document.styleSheets].some(
          (sheet) => sheet.href && new URL(sheet.href).pathname.endsWith("/src/styles.css"),
        ),
        title: document.title,
      };
    }, { productsUrl });

    const assetResponses = Object.fromEntries(
      EXPECTED_ASSET_PATHS.map((path) => [path, responseStatusByPath(responses, path)]),
    );
    const visibleFields = {
      name: dom.product_field_matches.every((item) => item.fields_present && item.rendered),
      price: dom.product_field_matches.every((item) => item.fields_present && item.rendered),
      category: dom.product_field_matches.every((item) => item.fields_present && item.rendered),
      description: dom.product_field_matches.every((item) => item.fields_present && item.rendered),
    };
    const passed = Boolean(
      navigation?.status() === 200 &&
        dom.document_ready_state === "complete" &&
        dom.module_script_loaded &&
        dom.stylesheet_loaded &&
        dom.product_count >= 6 &&
        dom.rendered_card_count === dom.product_count &&
        dom.product_field_matches.every((item) => item.fields_present && item.rendered) &&
        dom.noscript_card_count === 0 &&
        Object.values(assetResponses).every((status) => status === 200) &&
        consoleErrors.length === 0 &&
        pageErrors.length === 0 &&
        requestFailures.length === 0,
    );

    process.stdout.write(JSON.stringify({
      schema_version: "dummy-storefront-browser-proof/v1",
      status: passed ? "passed" : "failed",
      browser_verification_status: passed ? "passed" : "failed",
      storefront_runtime_status: passed ? "passed" : "failed",
      storefront_runtime_engine: "playwright_chromium",
      real_browser_used: true,
      managed_frontend_origin: MANAGED_ORIGIN,
      preview_url: previewUrl,
      preview_http_status: navigation?.status() ?? null,
      document_ready_state: dom.document_ready_state,
      product_count: dom.product_count,
      rendered_card_count: dom.rendered_card_count,
      visible_fields: visibleFields,
      rendered_headings: dom.rendered_headings,
      product_field_matches: dom.product_field_matches,
      module_script_loaded: dom.module_script_loaded,
      stylesheet_loaded: dom.stylesheet_loaded,
      noscript_card_count: dom.noscript_card_count,
      asset_responses: assetResponses,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      request_failures: requestFailures,
      observed_at: new Date().toISOString(),
    }));
  } finally {
    await browser?.close();
  }
}

main().catch((error) => {
  process.stdout.write(JSON.stringify({
    schema_version: "dummy-storefront-browser-proof/v1",
    status: "failed",
    browser_verification_status: "failed",
    storefront_runtime_status: "failed",
    storefront_runtime_engine: "playwright_chromium",
    real_browser_used: false,
    managed_frontend_origin: MANAGED_ORIGIN,
    error: error instanceof Error ? error.message : String(error),
    observed_at: new Date().toISOString(),
  }));
  process.exitCode = 2;
});
