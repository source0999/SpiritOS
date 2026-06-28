import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

/**
 * Serves the LumaCart dummy-product-site fixture's index.html as a viewable page so
 * Britton can click one link and see the page the coder agent made, instead of
 * copy-pasting fixture paths. Read-only: it never writes, applies, or commits.
 *
 * The fixture is a plain static site (index.html + src/*.js + src/styles.css) written
 * under tests/ui-agent-trials/fixtures/dummy-product-site/, so we only need to return
 * the index.html body. Relative asset references resolve against this route's path.
 */
export async function GET() {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return new Response("SPIRIT_CODING_USE_PROXY is not true", {
      headers: { "content-type": "text/plain; charset=utf-8" },
      status: 409,
    });
  }

  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({
        max_bytes: 256_000,
        path: "tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return new Response(
        text || `Could not read LumaCart index.html (Source Proxy HTTP ${response.status}).`,
        {
          headers: { "content-type": "text/plain; charset=utf-8" },
          status: response.status === 404 ? 404 : 502,
        },
      );
    }
    const payload = asRecord(await response.json().catch(() => ({})));
    const content =
      typeof payload.content === "string"
        ? payload.content
        : typeof payload.excerpt === "string"
          ? payload.excerpt
          : "";
    if (!content.trim()) {
      return new Response(
        "LumaCart index.html exists but is empty. Run Prompt 1 to create the fixture.",
        {
          headers: { "content-type": "text/plain; charset=utf-8" },
          status: 200,
        },
      );
    }
    return new Response(content, {
      headers: {
        // text/html so the browser renders the dummy storefront page.
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
      },
      status: 200,
    });
  } catch (error) {
    return new Response(
      error instanceof Error ? error.message : "Failed to read LumaCart fixture.",
      {
        headers: { "content-type": "text/plain; charset=utf-8" },
        status: 502,
      },
    );
  }
}
