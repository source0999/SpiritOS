import { serveFixtureAsset } from "./_handler";

/**
 * Root of the LumaCart dummy-product-site preview ("Open LumaCart page" link). Serves the
 * fixture's index.html. Relative asset requests (src/styles.css, src/main.js) are handled by
 * the sibling catch-all route under [...path]/.
 */
export async function GET() {
  return serveFixtureAsset(null);
}
