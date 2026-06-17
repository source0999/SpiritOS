"use client";

import { useEffect } from "react";

/** SpiritOS LAN dev speaks TLS on :3000. Plain http:// gives empty replies and broken fetches. */
export function LanProtocolGuard() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.protocol !== "http:") return;
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") return;
    const target = `https://${window.location.host}${window.location.pathname}${window.location.search}${window.location.hash}`;
    window.location.replace(target);
  }, []);

  return null;
}
