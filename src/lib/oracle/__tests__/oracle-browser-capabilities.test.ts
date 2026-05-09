// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getOracleBrowserCapabilityReport,
  getOracleHttpsUpgradeUrl,
} from "@/lib/oracle/oracle-browser-capabilities";

// jsdom won't let us cross-origin replaceState, so we patch the
// window.location pieces we read instead. Spirit refuses to fight jsdom about it.
function patchLocation(over: { protocol?: string; host?: string; pathname?: string; search?: string; hash?: string }) {
  const cur = window.location;
  const value = {
    protocol: over.protocol ?? cur.protocol,
    host: over.host ?? cur.host,
    pathname: over.pathname ?? cur.pathname,
    search: over.search ?? cur.search,
    hash: over.hash ?? cur.hash,
    origin: `${over.protocol ?? cur.protocol}//${over.host ?? cur.host}`,
    href: `${over.protocol ?? cur.protocol}//${over.host ?? cur.host}${over.pathname ?? cur.pathname}`,
    reload: cur.reload.bind(cur),
    assign: cur.assign.bind(cur),
    replace: cur.replace.bind(cur),
    toString: () => `${over.protocol ?? cur.protocol}//${over.host ?? cur.host}${over.pathname ?? cur.pathname}`,
    ancestorOrigins: cur.ancestorOrigins,
  } as unknown as Location;
  Object.defineProperty(window, "location", { configurable: true, writable: true, value });
}

function patchSecure(isSecure: boolean) {
  Object.defineProperty(window, "isSecureContext", {
    value: isSecure,
    configurable: true,
  });
}

function patchNavigator(over: { hasMediaDevices?: boolean; hasGetUserMedia?: boolean }) {
  const md: Partial<MediaDevices> | undefined = over.hasMediaDevices
    ? {
        getUserMedia: over.hasGetUserMedia
          ? (vi.fn() as unknown as MediaDevices["getUserMedia"])
          : (undefined as unknown as MediaDevices["getUserMedia"]),
      }
    : undefined;
  Object.defineProperty(navigator, "mediaDevices", {
    value: md,
    configurable: true,
  });
}

function patchRecorder(present: boolean) {
  if (present) {
    vi.stubGlobal(
      "MediaRecorder",
      class {
        static isTypeSupported() {
          return true;
        }
      },
    );
  } else {
    vi.stubGlobal("MediaRecorder", undefined as unknown);
  }
}

const originalLocation = window.location;

describe("getOracleBrowserCapabilityReport", () => {
  beforeEach(() => {
    patchSecure(true);
    patchNavigator({ hasMediaDevices: true, hasGetUserMedia: true });
    patchRecorder(true);
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns stable not-mounted state when mounted=false", () => {
    const r = getOracleBrowserCapabilityReport(false);
    expect(r.mounted).toBe(false);
    expect(r.blockedReason).toBe("not-mounted");
    expect(r.canUseMic).toBe(false);
    expect(r.userMessage).toMatch(/checking voice input/i);
    expect(r.isSecureContext).toBeNull();
  });

  it("returns canUseMic=true for secure supported browser", () => {
    const r = getOracleBrowserCapabilityReport(true);
    expect(r.mounted).toBe(true);
    expect(r.canUseMic).toBe(true);
    expect(r.blockedReason).toBeNull();
    expect(r.userMessage).toMatch(/mic ready/i);
  });

  it("flags insecure context blockedReason", () => {
    patchSecure(false);
    const r = getOracleBrowserCapabilityReport(true);
    expect(r.blockedReason).toBe("insecure-context");
    expect(r.canUseMic).toBe(false);
    expect(r.userMessage).toMatch(/HTTP address/);
  });

  it("flags missing mediaDevices in secure context", () => {
    patchNavigator({ hasMediaDevices: false });
    const r = getOracleBrowserCapabilityReport(true);
    expect(r.blockedReason).toBe("missing-media-devices");
    expect(r.canUseMic).toBe(false);
  });

  it("flags missing getUserMedia in secure context", () => {
    patchNavigator({ hasMediaDevices: true, hasGetUserMedia: false });
    const r = getOracleBrowserCapabilityReport(true);
    expect(r.blockedReason).toBe("missing-get-user-media");
    expect(r.canUseMic).toBe(false);
  });

  it("flags missing MediaRecorder when other APIs exist", () => {
    patchRecorder(false);
    const r = getOracleBrowserCapabilityReport(true);
    expect(r.blockedReason).toBe("missing-media-recorder");
    expect(r.canUseMic).toBe(false);
    expect(r.userMessage).toMatch(/recording/i);
  });
});

describe("getOracleHttpsUpgradeUrl", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
  });

  it("returns null when secure context", () => {
    patchSecure(true);
    expect(getOracleHttpsUpgradeUrl()).toBeNull();
  });

  it("returns https variant for plain http://", () => {
    patchSecure(false);
    patchLocation({ protocol: "http:", host: "10.0.0.186:3000", pathname: "/oracle", search: "", hash: "" });
    expect(getOracleHttpsUpgradeUrl()).toBe("https://10.0.0.186:3000/oracle");
  });
});
