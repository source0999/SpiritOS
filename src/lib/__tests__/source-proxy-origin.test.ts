/// <reference types="vitest/globals" />

import {
  SOURCE_PROXY_STREAM_UNDICI_OPTIONS,
  sourceProxyFetch,
  sourceProxyStreamFetch,
} from "@/lib/source-proxy-origin";

describe("sourceProxyStreamFetch policy", () => {
  it("disables undici default 10s connect timeout for SSE upstream (see undici connect.js timeout fallback)", () => {
    expect(SOURCE_PROXY_STREAM_UNDICI_OPTIONS.connectTimeout).toBe(0);
  });

  it("disables body idle timeout so long gaps between SSE chunks do not kill the bridge", () => {
    expect(SOURCE_PROXY_STREAM_UNDICI_OPTIONS.bodyTimeout).toBe(0);
  });

  it("is a distinct export from JSON-oriented sourceProxyFetch (guard against accidental merge)", () => {
    expect(typeof sourceProxyStreamFetch).toBe("function");
    expect(sourceProxyStreamFetch).not.toBe(sourceProxyFetch);
  });
});
