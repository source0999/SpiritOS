import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type JsonRecord = Record<string, unknown>;

const FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/";

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

/**
 * Resolves the relative asset path from the request URL to a fixture-relative path.
 * The "Open LumaCart page" link points at this route's root, and the generated index.html
 * references assets with relative paths like "src/styles.css" / "src/main.js", which the
 * browser resolves against this route. We map any sub-path back under the fixture root.
 *
 * Only relative paths under the fixture root are allowed. Absolute, parent-traversal, or
 * encoded paths that escape the fixture root are rejected so the route cannot be used to
 * read arbitrary repo files.
 */
function resolveFixturePath(rawPath: string | null): string | null {
  if (!rawPath) return `${FIXTURE_ROOT}index.html`;
  // Strip a leading slash so "/src/styles.css" -> "src/styles.css".
  const trimmed = rawPath.replace(/^\/+/, "");
  if (!trimmed) return `${FIXTURE_ROOT}index.html`;
  const decoded = (() => {
    try {
      return decodeURIComponent(trimmed);
    } catch {
      return trimmed;
    }
  })();
  // Reject anything that tries to escape the fixture root.
  if (decoded.includes("..") || decoded.startsWith("/") || /^[A-Za-z]:/.test(decoded)) {
    return null;
  }
  return `${FIXTURE_ROOT}${decoded}`;
}

function contentTypeFor(path: string): string {
  const lower = path.toLowerCase();
  if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html; charset=utf-8";
  if (lower.endsWith(".css")) return "text/css; charset=utf-8";
  if (lower.endsWith(".js") || lower.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (lower.endsWith(".json")) return "application/json; charset=utf-8";
  if (lower.endsWith(".svg")) return "image/svg+xml";
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  if (lower.endsWith(".gif")) return "image/gif";
  if (lower.endsWith(".webp")) return "image/webp";
  if (lower.endsWith(".ico")) return "image/x-icon";
  return "text/plain; charset=utf-8";
}

/**
 * Serves the LumaCart dummy-product-site fixture as a viewable page so Britton can click one
 * link and see the page the coder agent made, instead of copy-pasting fixture paths. Read-only:
 * it never writes, applies, or commits. Handles index.html and its relative asset references
 * (src/styles.css, src/main.js, ...) so the rendered page is not blank.
 */
export async function GET(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return new Response("SPIRIT_CODING_USE_PROXY is not true", {
      headers: { "content-type": "text/plain; charset=utf-8" },
      status: 409,
    });
  }

  const url = new URL(request.url);
  const fixturePath = resolveFixturePath(url.pathname.replace(/^\/v1\/coding\/dummy-product-site-preview\/?/, ""));
  if (!fixturePath) {
    return new Response("Refusing to read a path outside the LumaCart fixture root.", {
      headers: { "content-type": "text/plain; charset=utf-8" },
      status: 400,
    });
  }

  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({ max_bytes: 1_000_000, path: fixturePath }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      return new Response(
        text || `Could not read ${fixturePath} (Source Proxy HTTP ${response.status}).`,
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
        fixturePath.endsWith("index.html")
          ? "LumaCart index.html exists but is empty. Run Prompt 1 to create the fixture."
          : `${fixturePath} is empty.`,
        {
          headers: { "content-type": "text/plain; charset=utf-8" },
          status: 200,
        },
      );
    }
    return new Response(content, {
      headers: {
        "content-type": contentTypeFor(fixturePath),
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
