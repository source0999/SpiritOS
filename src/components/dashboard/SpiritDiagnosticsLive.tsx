"use client";

// ── SpiritDiagnosticsLive - single /api/spirit/health poll - one sheet, tight rows ─
// > Chunky bordered rows were a UX war crime - strip + divides keeps the rail scannable.
// > Do not spin a second poll; SpiritHealthIndicator is legacy/tests only.
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { DiagnosticRow } from "@/components/dashboard/DiagnosticRow";
import { cn } from "@/lib/cn";

const POLL_MS = 20_000;

type LoadState = "checking" | "ready" | "error";

type HealthDiagnostics = {
  engine?: string;
  maxOutputTokens?: number;
  maxOutputTokensSource?: string;
  oracleMaxOutputTokens?: number;
  oracleMaxOutputTokensSource?: string;
  chatModel?: string;
  oracleLaneModel?: string;
  context?: { label?: string; source?: string };
  tts?: { provider?: string; voice?: string; source?: string };
};

type HealthPayload = {
  ok?: boolean;
  model?: string;
  baseURL?: string;
  diagnostics?: HealthDiagnostics;
};

function StatusText({
  children,
  tone,
}: {
  children: string;
  tone: "accent" | "muted" | "pulse";
}) {
  return (
    <span
      className={cn(
        "font-mono text-xs tracking-tight",
        tone === "accent" &&
          "text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_88%,white)]",
        tone === "muted" && "text-chalk/50",
        tone === "pulse" && "animate-pulse text-chalk/45",
      )}
      aria-live="polite"
    >
      {children}
    </span>
  );
}

function healthDotClasses(
  loadState: LoadState,
  backendOk: boolean,
): { dot: string; ring: string } {
  if (loadState === "checking") {
    return {
      dot: "bg-chalk/35 shadow-none",
      ring: "ring-1 ring-chalk/18",
    };
  }
  if (loadState === "error" || !backendOk) {
    return {
      dot: "bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.45)]",
      ring: "ring-1 ring-rose-400/35",
    };
  }
  return {
    dot: "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.42)]",
    ring: "ring-1 ring-cyan-400/28",
  };
}

export function SpiritDiagnosticsLive() {
  const [loadState, setLoadState] = useState<LoadState>("checking");
  const [data, setData] = useState<HealthPayload | null>(null);
  const devOriginHost = useSyncExternalStore(
    () => () => {},
    () =>
      process.env.NODE_ENV === "development" && typeof window !== "undefined"
        ? window.location.host
        : "",
    () => "",
  );
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
        const json = (await res.json()) as HealthPayload;
        if (cancelledRef.current || ac.signal.aborted) return;
        setData(json);
        setLoadState("ready");
      } catch {
        if (!cancelledRef.current && !ac.signal.aborted) {
          setData(null);
          setLoadState("error");
        }
      }
    };

    void tick();
    const id = setInterval(() => void tick(), POLL_MS);
    return () => {
      cancelledRef.current = true;
      clearInterval(id);
      abortRef.current?.abort();
    };
  }, []);

  const d = data?.diagnostics;
  const backendOk = data?.ok === true;

  const backendLabel =
    loadState === "checking"
      ? "Checking…"
      : loadState === "error"
        ? "Offline"
        : backendOk
          ? "Online"
          : "Offline";

  const backendTone: "accent" | "muted" | "pulse" =
    loadState === "checking"
      ? "pulse"
      : loadState === "error" || !backendOk
        ? "muted"
        : "accent";

  const backendSubtitle =
    loadState === "error"
      ? "Probe failed · check API route"
      : loadState === "checking"
        ? "Polling /api/spirit/health…"
        : loadState === "ready" && data?.baseURL
          ? data.baseURL
          : "OpenAI-compat bridge";

  const checking = loadState === "checking";
  const failed = loadState === "error";

  const { dot, ring } = healthDotClasses(loadState, backendOk);

  const engineVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : (
    (d?.engine ?? "-")
  );
  const engineHint = failed ? "-" : checking ? "…" : "OpenAI-compat · local";

  const modelVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : (
    (d?.chatModel ?? data?.model ?? "-")
  );
  const modelHint = failed ? "-" : checking ? "…" : "OLLAMA_MODEL · /chat";

  const oracleModelVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : (
    (d?.oracleLaneModel ?? "-")
  );
  const oracleModelHint = failed
    ? "-"
    : checking
      ? "…"
      : "ORACLE_OLLAMA_MODEL or chat model";

  const oracleCapVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : typeof d?.oracleMaxOutputTokens === "number" ? (
    String(d.oracleMaxOutputTokens)
  ) : (
    "-"
  );
  const oracleCapHint = failed
    ? "-"
    : checking
      ? "…"
      : (d?.oracleMaxOutputTokensSource ?? "…");

  const ctxVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : (
    (d?.context?.label ?? "-")
  );
  const ctxHint = failed ? "-" : checking ? "…" : (d?.context?.source ?? "…");

  const capVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : typeof d?.maxOutputTokens === "number" ? (
    String(d.maxOutputTokens)
  ) : (
    "-"
  );
  const capHint = failed
    ? "-"
    : checking
      ? "…"
      : (d?.maxOutputTokensSource ?? "…");

  const voiceVal = checking ? (
    <StatusText tone="pulse">Checking…</StatusText>
  ) : failed ? (
    "-"
  ) : d?.tts ? (
    `${d.tts.provider} · ${d.tts.voice}`
  ) : (
    "-"
  );
  const voiceHint = failed ? "-" : checking ? "…" : (d?.tts?.source ?? "…");

  return (
    <div className="overflow-hidden rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_85%,transparent)] bg-black/[0.22] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="border-b border-white/[0.06] bg-gradient-to-b from-white/[0.04] to-transparent px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              "relative h-2 w-2 shrink-0 rounded-full",
              dot,
              ring,
              loadState === "checking" && "animate-pulse",
            )}
            aria-hidden
          />
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.18em] text-chalk/40">
              Backend
            </p>
            <div className="mt-1">
              <StatusText tone={backendTone}>{backendLabel}</StatusText>
            </div>
            <p
              className="mt-px truncate font-mono text-[10px] leading-tight text-chalk/38"
              title={backendSubtitle}
            >
              {backendSubtitle}
            </p>
          </div>
        </div>
      </div>

      <dl className="divide-y divide-white/[0.05] px-3 py-2">
        <DiagnosticRow label="Engine" value={engineVal} hint={engineHint} />
        <DiagnosticRow label="Model" value={modelVal} hint={modelHint} />
        <DiagnosticRow
          label="Oracle lane"
          value={oracleModelVal}
          hint={oracleModelHint}
        />
        <DiagnosticRow label="Context" value={ctxVal} hint={ctxHint} />
        <DiagnosticRow label="Out cap" value={capVal} hint={capHint} />
        <DiagnosticRow
          label="Oracle cap"
          value={oracleCapVal}
          hint={oracleCapHint}
        />
        <DiagnosticRow label="Voice" value={voiceVal} hint={voiceHint} />
        {process.env.NODE_ENV === "development" && devOriginHost ? (
          <DiagnosticRow
            label="Origin"
            value={<span className="font-mono text-chalk/80">{devOriginHost}</span>}
            hint="Local settings, Dexie threads, and voice prefs are per-origin (LAN vs Tailscale differ)."
          />
        ) : null}
      </dl>
    </div>
  );
}
