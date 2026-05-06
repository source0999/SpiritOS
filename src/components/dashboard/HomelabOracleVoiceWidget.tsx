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

const ctaLink =
  "inline-flex min-h-[48px] max-w-full touch-manipulation items-center justify-center gap-2 rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_46%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-4 font-mono text-[12px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] shadow-[0_0_22px_color-mix(in_oklab,var(--spirit-glow)_22%,transparent)] transition hover:brightness-110 active:scale-[0.98] [-webkit-tap-highlight-color:transparent]";

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
      className={`homelab-panel homelab-panel-accent relative touch-manipulation overflow-hidden ${className}`}
    >
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_15%_50%,color-mix(in_oklab,var(--spirit-accent)_9%,transparent),transparent_70%)]"
        aria-hidden
      />

      <div className="relative grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-[minmax(0,11rem)_1fr] lg:grid-cols-[minmax(0,13rem)_1fr]">
        <div className="flex min-w-0 flex-col items-center justify-center gap-2 px-3 pb-2 pt-4 sm:px-4 sm:py-4">
          <OracleOrbSprite visualState={visualState} variant="widget" />
          <OracleVoiceVisualizer state={visualState} compact className="w-full max-w-[220px]" />
        </div>

        <div className="flex min-w-0 flex-1 flex-col justify-between p-4 pl-1 sm:pl-2">
          <div>
            <div className="mb-3 flex min-w-0 flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
                  <span className="homelab-status-dot" aria-hidden />
                  Spirit · Oracle Voice
                </p>
                <h2 className="mt-1 font-mono text-[17px] font-semibold uppercase tracking-tight text-chalk">
                  Oracle Voice
                </h2>
                <p className="mt-0.5 font-mono text-[9.5px] text-chalk/40">
                  Hands-free · Whisper STT · TTS · text fallback
                </p>
              </div>
              <HomelabStatusBadge variant={badgeVariant}>{badgeLabel}</HomelabStatusBadge>
            </div>

            <dl className="grid min-w-0 gap-y-1 font-mono text-[10.5px]">
              <div className="flex min-w-0 gap-x-2">
                <dt className="w-[92px] shrink-0 text-chalk/45">Secure context</dt>
                <dd
                  className={
                    mounted && capability.isSecureContext === false
                      ? "text-rose-300/90"
                      : "min-w-0 text-chalk/80"
                  }
                >
                  {secureLabel}
                </dd>
              </div>
              <div className="flex min-w-0 gap-x-2">
                <dt className="w-[92px] shrink-0 text-chalk/45">Mic capability</dt>
                <dd
                  className={
                    mounted &&
                    !capability.canUseMic &&
                    capability.blockedReason !== "not-mounted"
                      ? "min-w-0 text-amber-300/80"
                      : "min-w-0 text-chalk/80"
                  }
                >
                  {micLabel}
                </dd>
              </div>
              <div className="flex gap-x-2">
                <dt className="w-[92px] shrink-0 text-chalk/45">STT</dt>
                <dd className="text-chalk/75">Whisper backend</dd>
              </div>
              <div className="flex gap-x-2">
                <dt className="w-[92px] shrink-0 text-chalk/45">TTS</dt>
                <dd className="text-chalk/75">/api/tts</dd>
              </div>
              <div className="flex gap-x-2">
                <dt className="w-[92px] shrink-0 text-chalk/45">Runtime</dt>
                <dd className="text-[color:var(--spirit-accent-strong)]">Oracle</dd>
              </div>
              {oracleModel && (
                <div className="flex min-w-0 gap-x-2">
                  <dt className="w-[92px] shrink-0 text-chalk/45">Model</dt>
                  <dd className="min-w-0 truncate text-chalk/80">{oracleModel}</dd>
                </div>
              )}
            </dl>

            {showInsecureWarning && (
              <p className="mt-2 rounded-lg border border-amber-500/30 bg-amber-500/[0.06] px-3 py-1.5 font-mono text-[9.5px] leading-relaxed text-amber-300/85">
                Voice requires HTTPS, localhost, or 127.0.0.1. Text fallback available.
              </p>
            )}
          </div>

          <div className="mt-3 min-w-0">
            <Link href="/oracle" className={ctaLink}>
              ◌ Open Oracle
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
