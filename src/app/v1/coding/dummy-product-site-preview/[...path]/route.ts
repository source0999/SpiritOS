import { serveFixtureAsset } from "../_handler";

/**
 * Catch-all for the LumaCart dummy-product-site preview so relative asset requests
 * (src/styles.css, src/main.js, src/products.js) resolve to the viewer. Without this,
 * the browser's relative asset URLs 404 at the Next.js router level (a static route
 * only matches its exact path) and the rendered page is blank.
 */
export async function GET(_request: Request, context: { params: Promise<{ path?: string[] }> }) {
  const { path } = await context.params;
  return serveFixtureAsset(path?.join("/"));
}
