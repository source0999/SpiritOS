import { describe, expect, it } from "vitest";

import { getWebSearchProviderConfig } from "@/lib/server/web-search/provider-config";

describe("getWebSearchProviderConfig", () => {
  it("keeps the provider ladder disabled and local-only by default", () => {
    const config = getWebSearchProviderConfig({});

    expect(config.enabled).toBe(false);
    expect(config.providerOrder).toEqual(["cache", "searxng"]);
    expect(config.searxng.url).toBe("");
    expect(config.fetchPage.enabled).toBe(false);
    expect(config.paidFallback.enabled).toBe(false);
    expect(config.paidFallback.requireApproval).toBe(true);
  });

  it("reads the explicit paid fallback approval env name", () => {
    const config = getWebSearchProviderConfig({
      WEB_SEARCH_PAID_FALLBACK_REQUIRES_APPROVAL: "false",
    });

    expect(config.paidFallback.requireApproval).toBe(false);
  });
});
