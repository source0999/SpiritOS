import { describe, expect, it } from "vitest";

import {
  isVerifiedHttpUrl,
  normalizeToHttpUrl,
  resolveVerifiedHttpUrl,
} from "@/lib/verified-http-url";

describe("normalizeToHttpUrl", () => {
  it("prefixes bare host/path", () => {
    expect(normalizeToHttpUrl("www.example.com/foo")).toBe("https://www.example.com/foo");
  });

  it("handles protocol-relative URLs", () => {
    expect(normalizeToHttpUrl("//cdn.example.com/a")).toBe("https://cdn.example.com/a");
  });

  it("preserves existing http(s)", () => {
    expect(normalizeToHttpUrl("https://a.b/c")).toBe("https://a.b/c");
    expect(normalizeToHttpUrl("http://a.b/c")).toBe("http://a.b/c");
  });

  it("strips angle brackets from wrapped URLs", () => {
    expect(normalizeToHttpUrl("<https://example.com/a>")).toBe("https://example.com/a");
  });

  it("rejects junk and dangerous schemes", () => {
    expect(normalizeToHttpUrl("")).toBeUndefined();
    expect(normalizeToHttpUrl("   ")).toBeUndefined();
    expect(normalizeToHttpUrl("javascript:alert(1)")).toBeUndefined();
    expect(normalizeToHttpUrl("not a url")).toBeUndefined();
    expect(normalizeToHttpUrl("/relative-only")).toBeUndefined();
  });
});

describe("isVerifiedHttpUrl", () => {
  it("accepts only strings that normalize to http(s)", () => {
    expect(isVerifiedHttpUrl("www.example.com/abc")).toBe(true);
    expect(isVerifiedHttpUrl("https://x.y/z")).toBe(true);
    expect(isVerifiedHttpUrl(undefined)).toBe(false);
    expect(isVerifiedHttpUrl("")).toBe(false);
    expect(isVerifiedHttpUrl("ftp://x.com/a")).toBe(false);
  });
});

describe("resolveVerifiedHttpUrl", () => {
  it("returns canonical https for bare hosts", () => {
    expect(resolveVerifiedHttpUrl("www.example.com/abc")).toBe("https://www.example.com/abc");
  });
});
