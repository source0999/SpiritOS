"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

export type ClusterFetchState = "checking" | "loaded" | "error";

export type UseClusterTelemetryResult = {
  data: ClusterTelemetryResponse | null;
  state: ClusterFetchState;
  error: string | null;
  refetch: () => void;
};

export function useClusterTelemetry(pollMs = 15_000): UseClusterTelemetryResult {
  const [state, setState] = useState<ClusterFetchState>("checking");
  const [data, setData] = useState<ClusterTelemetryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refetchRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    let active = true;
    let ctrl = new AbortController();
    let reqId = 0;

    async function poll() {
      const id = ++reqId;
      try {
        const res = await fetch("/api/telemetry/cluster", {
          cache: "no-store",
          signal: ctrl.signal,
        });
        if (!active || id !== reqId) return;
        if (res.ok) {
          const json = (await res.json()) as ClusterTelemetryResponse;
          if (!active || id !== reqId) return;
          setData(json);
          setState("loaded");
          setError(null);
        } else {
          const msg = res.statusText?.trim()
            ? `${res.status} ${res.statusText}`
            : `HTTP ${res.status}`;
          if (active && id === reqId) {
            setState("error");
            setError(msg);
          }
        }
      } catch (e) {
        if (!active || id !== reqId) return;
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (e instanceof Error && e.name === "AbortError") return;
        setState("error");
        setError(e instanceof Error ? e.message : "fetch failed");
      }
    }

    refetchRef.current = () => {
      if (!active) return;
      ctrl.abort();
      ctrl = new AbortController();
      void poll();
    };

    void poll();
    const pollTimer = setInterval(() => {
      ctrl.abort();
      ctrl = new AbortController();
      void poll();
    }, pollMs);

    return () => {
      active = false;
      refetchRef.current = null;
      clearInterval(pollTimer);
      ctrl.abort();
    };
  }, [pollMs]);

  const refetch = useCallback(() => {
    refetchRef.current?.();
  }, []);

  return { data, state, error, refetch };
}
