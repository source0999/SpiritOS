"use client";

// ── SpiritHealthIndicator - legacy isolated poll (unit tests only) ─────────────
// > Isolated poll for unit tests; do not stack with other /api/spirit/health clients.
import { useEffect, useRef, useState } from "react";

type HealthState = "checking" | "online" | "offline";

const POLL_MS = 20_000;

export function SpiritHealthIndicator() {
  const [state, setState] = useState<HealthState>("checking");
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    const abortRef = { current: null as AbortController | null };

    const tick = async () => {
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;
      try {
        const res = await fetch("/api/spirit/health", {
          signal: ac.signal,
          cache: "no-store",
        });
        const data = (await res.json()) as { ok?: boolean };
        if (cancelledRef.current || ac.signal.aborted) return;
        setState(data.ok === true ? "online" : "offline");
      } catch {
        if (!cancelledRef.current && !ac.signal.aborted) {
          setState("offline");
        }
      }
    };

    void tick();
    const id = setInterval(() => {
      void tick();
    }, POLL_MS);

    return () => {
      cancelledRef.current = true;
      clearInterval(id);
      abortRef.current?.abort();
    };
  }, []);

  const label =
    state === "checking"
      ? "Checking…"
      : state === "online"
        ? "Online"
        : "Offline";

  const className =
    state === "online"
      ? "font-mono text-sm text-[color:var(--spirit-accent-strong)]"
      : state === "offline"
        ? "font-mono text-sm text-chalk/50"
        : "animate-pulse font-mono text-sm text-chalk/45";

  return (
    <span className={className} aria-live="polite">
      {label}
    </span>
  );
}
