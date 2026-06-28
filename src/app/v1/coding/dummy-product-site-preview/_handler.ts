import { readFile } from "node:fs/promises";
import path from "node:path";

const REPO_ROOT = process.cwd();
const FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/";

/**
 * Resolves the relative asset path from the request URL to an absolute on-disk fixture path.
 * The "Open LumaCart page" link points at the viewer root, and the generated index.html
 * references assets with relative paths like "src/styles.css" / "src/main.js", which the
 * browser resolves against the viewer root. We map any sub-path back under the fixture root.
 *
 * Only relative paths under the fixture root are allowed. Absolute, parent-traversal, or
 * encoded paths that escape the fixture root are rejected so the route cannot be used to
 * read arbitrary repo files.
 */
export function resolveFixturePath(rawPath: string | null | undefined): string | null {
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

function contentTypeFor(relPath: string): string {
  const lower = relPath.toLowerCase();
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
 * Normalizes a served index.html so the LumaCart page actually renders.
 *
 * The model-authored fixture commonly writes `main.js` using ES module syntax
 * (`import products from './products.js'`) but loads it with a plain `<script src=...>`.
 * A classic script that contains an `import` statement throws a SyntaxError and the page
 * stays blank. This rewrite marks any external `<script src=...>` without an explicit type
 * as `type="module"` so relative ESM imports resolve against the viewer route. It only
 * touches the type attribute and leaves everything else (content, paths) untouched.
 */
function normalizeHtmlForPreview(html: string): string {
  return html.replace(
    /<script\b([^>]*?)\bsrc=(["'])([^"']+)\2([^>]*?)>/gi,
    (match, before, quote, src, after) => {
      const attrs = `${before} ${after}`;
      return /\btype\s*=/.test(attrs) ? match : `<script type="module"${attrs} src=${quote}${src}${quote}>`;
    },
  );
}

/**
 * Shared viewer handler for the LumaCart dummy-product-site fixture. Used by the root route
 * (the "Open LumaCart page" link) and the catch-all route (relative asset requests like
 * src/styles.css, src/main.js). Read-only: never writes, applies, or commits.
 *
 * Reads the fixture directly from the repo working tree on disk. The fixture is a plain static
 * site that Prompt 1 wrote under tests/ui-agent-trials/fixtures/dummy-product-site/, so there is
 * no need to round-trip through Source Proxy just to view it (the proxy round-trip was fragile
 * and produced a blank page when the workspace-read response shape differed).
 */
export async function serveFixtureAsset(fixtureSubPath: string | null | undefined): Promise<Response> {
  const fixtureRelPath = resolveFixturePath(fixtureSubPath);
  if (!fixtureRelPath) {
    return new Response("Refusing to read a path outside the LumaCart fixture root.", {
      headers: { "content-type": "text/plain; charset=utf-8" },
      status: 400,
    });
  }

  // Resolve to an absolute path and confirm the normalized result still lives under the fixture
  // root (guards against symlink or OS-specific normalization escapes).
  const absRoot = path.resolve(REPO_ROOT, FIXTURE_ROOT);
  const absTarget = path.resolve(REPO_ROOT, fixtureRelPath);
  const relFromRoot = path.relative(absRoot, absTarget);
  if (relFromRoot.startsWith("..") || path.isAbsolute(relFromRoot)) {
    return new Response("Refusing to read a path outside the LumaCart fixture root.", {
      headers: { "content-type": "text/plain; charset=utf-8" },
      status: 400,
    });
  }

  try {
    const content = await readFile(absTarget, "utf8");
    if (!content.trim()) {
      return new Response(
        fixtureRelPath.endsWith("index.html")
          ? "LumaCart index.html exists but is empty. Run Prompt 1 to create the fixture."
          : `${fixtureRelPath} is empty.`,
        {
          headers: { "content-type": "text/plain; charset=utf-8" },
          status: 200,
        },
      );
    }
    const isHtml = fixtureRelPath.toLowerCase().endsWith(".html");
    const servedContent = isHtml ? normalizeHtmlForPreview(content) : content;
    return new Response(servedContent, {
      headers: {
        "content-type": contentTypeFor(fixtureRelPath),
        "cache-control": "no-store",
      },
      status: 200,
    });
  } catch (error) {
    const notFound =
      error instanceof Error &&
      ("code" in error && (error as NodeJS.ErrnoException).code === "ENOENT");
    return new Response(
      notFound
        ? `${fixtureRelPath} not found on disk. Run Prompt 1 to create the LumaCart fixture.`
        : error instanceof Error
          ? error.message
          : "Failed to read LumaCart fixture.",
      {
        headers: { "content-type": "text/plain; charset=utf-8" },
        status: notFound ? 404 : 500,
      },
    );
  }
}
