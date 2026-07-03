"use client";

import { Component, lazy, Suspense, type ErrorInfo, type ReactNode } from "react";

import { SpiritFlixSplash } from "./SpiritFlixSplash";

const SpiritFlixApp = lazy(() =>
  import("./SpiritFlixApp").then((module) => ({
    default: module.SpiritFlixApp,
  })),
);

const RELOAD_STORAGE_KEY = "spiritflix_chunk_retry_at";
const RELOAD_THROTTLE_MS = 30_000;

function isChunkLoadError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  return /ChunkLoadError|Loading chunk|failed to fetch dynamically imported module/i.test(`${error.name} ${error.message}`);
}

class SpiritFlixChunkBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    if (!isChunkLoadError(error) || typeof window === "undefined") return;
    const previousRetry = Number(window.sessionStorage.getItem(RELOAD_STORAGE_KEY) ?? "0");
    const now = Date.now();
    if (!Number.isFinite(previousRetry) || now - previousRetry > RELOAD_THROTTLE_MS) {
      window.sessionStorage.setItem(RELOAD_STORAGE_KEY, String(now));
      window.location.reload();
    }
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main className="spiritflix-shell">
        <SpiritFlixSplash
          message="SpiritFlix could not finish loading on this connection."
          action={
            <button className="spiritflix-secondary-button" type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          }
        />
      </main>
    );
  }
}

export function SpiritFlixRouteClient() {
  return (
    <SpiritFlixChunkBoundary>
      <Suspense
        fallback={
          <main className="spiritflix-shell">
            <SpiritFlixSplash />
          </main>
        }
      >
        <SpiritFlixApp />
      </Suspense>
    </SpiritFlixChunkBoundary>
  );
}
