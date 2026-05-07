"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import Link from "next/link";

import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { OracleOrbSprite } from "@/components/oracle/OracleOrbSprite";
import { OracleVoiceVisualizer } from "@/components/oracle/OracleVoiceVisualizer";
import "@/components/oracle/oracle-visuals.css";
import { getOracleBrowserCapabilityReport } from "@/lib/oracle/oracle-browser-capabilities";
import {
  getOracleVisualStateForHomelab,
  type HomelabOracleBadgeVariant,
} from "@/lib/oracle/oracle-visual-state";
import { cn } from "@/lib/cn";

const ctaLink =
  "spirit-dashboard-v2-cta-primary inline-flex min-h-[48px] max-w-full touch-manipulation items-center justify-center gap-2 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_48%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_16%,transparent)] px-8 font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 active:scale-[0.98] [-webkit-tap-highlight-color:transparent]";

const noop = () => () => {};

export function HomelabOracleVoiceWidget({ className = "" }: { className?: string }) {
  const mounted = useSyncExternalStore(noop, () => true, () => false);
  const [oracleModel, setOracleModel] = useState<string | null>(null);

  useEffect(() => {
    if (!mounted) return;
    let active = true;
    fetch("/api/spirit/health", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((json: { model?: string } | null) => {
        if (active && json?.model) setOracleModel(json.model);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [mounted]);

  const capability = useMemo(() => getOracleBrowserCapabilityReport(mounted), [mounted]);

  const secureLabel =
    !mounted || capability.isSecureContext === null
      ? "Checking…"
      : capability.isSecureContext
        ? "OK"
        : "Blocked";

  const micLabel =
    !mounted
      ? "Checking…"
      : capability.canUseMic
        ? "Available"
        : capability.blockedReason === "not-mounted"
          ? "Checking…"
          : capability.blockedReason === "insecure-context"
            ? "Blocked - insecure context"
            : capability.hasMediaDevices
              ? "Available"
              : "Unavailable";

  const badgeVariant: HomelabOracleBadgeVariant =
    !mounted
      ? "pending"
      : capability.canUseMic
        ? "live"
        : capability.isSecureContext === false
          ? "offline"
          : "ready";

  const badgeLabel =
    !mounted ? "Checking" : capability.canUseMic ? "Ready" : "Degraded";

  const showInsecureWarning = mounted && capability.isSecureContext === false;

  const visualState = useMemo(
    () => getOracleVisualStateForHomelab({ mounted, capability, badgeVariant }),
    [mounted, capability, badgeVariant],
  );

  return (
    <section
      aria-label="Oracle Voice"
      className={cn(
        "spirit-dashboard-v2-glass spirit-dashboard-v2-glass--oracle relative touch-manipulation",
        className,
      )}
    >
      <span className="spirit-dashboard-v2-glass__shine-t" aria-hidden />
      <span className="spirit-dashboard-v2-glass__shine-l hidden lg:block" aria-hidden />

      <div className="relative grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-7 lg:grid-cols-[minmax(0,11.25rem)_1fr] lg:gap-9 lg:p-9 xl:grid-cols-[minmax(0,12rem)_1fr]">
        <div className="relative flex min-h-[156px] min-w-0 flex-col items-center justify-center gap-3 sm:min-h-[172px]">
          <div className="spirit-dashboard-v2-fairy-halo pointer-events-none" aria-hidden />
          <div className="relative z-[1] flex w-full flex-col items-center gap-2.5">
            <OracleOrbSprite visualState={visualState} variant="widget" />
            <OracleVoiceVisualizer state={visualState} compact className="w-full max-w-[210px]" />
          </div>
        </div>

        <div className="relative z-[1] flex min-w-0 flex-1 flex-col justify-between gap-5">
          <div>
            <div className="mb-4 flex min-w-0 flex-wrap items-center justify-between gap-3">
              <div className="min-w-0 pr-2">
                <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-chalk/48">
                  <span className="homelab-status-dot" aria-hidden />
                  Spirit · Oracle Voice
                </p>
                <h2 className="mt-1.5 font-mono text-[clamp(1.15rem,3.2vw,1.55rem)] font-semibold uppercase tracking-tight text-chalk">
                  Oracle Voice
                </h2>
                <p className="mt-1 max-w-lg font-mono text-[10px] leading-relaxed text-chalk/42">
                  Hands-free · Whisper STT · TTS · text fallback
                </p>
              </div>
              <HomelabStatusBadge variant={badgeVariant}>{badgeLabel}</HomelabStatusBadge>
            </div>

            <dl className="grid min-w-0 gap-y-1.5 font-mono text-[10.5px]">
              <div className="flex min-w-0 gap-x-3">
                <dt className="w-[100px] shrink-0 text-chalk/42">Secure context</dt>
                <dd
                  className={
                    mounted && capability.isSecureContext === false
                      ? "text-rose-300/90"
                      : "min-w-0 text-chalk/82"
                  }
                >
                  {secureLabel}
                </dd>
              </div>
              <div className="flex min-w-0 gap-x-3">
                <dt className="w-[100px] shrink-0 text-chalk/42">Mic capability</dt>
                <dd
                  className={
                    mounted &&
                    !capability.canUseMic &&
                    capability.blockedReason !== "not-mounted"
                      ? "min-w-0 text-amber-300/80"
                      : "min-w-0 text-chalk/82"
                  }
                >
                  {micLabel}
                </dd>
              </div>
              <div className="flex gap-x-3">
                <dt className="w-[100px] shrink-0 text-chalk/42">STT</dt>
                <dd className="text-chalk/78">Whisper backend</dd>
              </div>
              <div className="flex gap-x-3">
                <dt className="w-[100px] shrink-0 text-chalk/42">TTS</dt>
                <dd className="text-chalk/78">/api/tts</dd>
              </div>
              <div className="flex gap-x-3">
                <dt className="w-[100px] shrink-0 text-chalk/42">Runtime</dt>
                <dd className="text-[color:var(--spirit-accent-strong)]">Oracle</dd>
              </div>
              {oracleModel && (
                <div className="flex min-w-0 gap-x-3">
                  <dt className="w-[100px] shrink-0 text-chalk/42">Model</dt>
                  <dd className="min-w-0 truncate text-chalk/80">{oracleModel}</dd>
                </div>
              )}
            </dl>

            {showInsecureWarning && (
              <p className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/[0.06] px-4 py-2 font-mono text-[9.5px] leading-relaxed text-amber-300/85">
                Voice requires HTTPS, localhost, or 127.0.0.1. Text fallback available.
              </p>
            )}
          </div>

          <div className="min-w-0 pt-1">
            <Link href="/oracle" className={cn(ctaLink, "w-full sm:w-auto")}>
              ◌ Open Oracle
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
