"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";

type HealthData = {
  status?: string;
  url?: string;
  engine?: string;
  model?: string;
  context?: number | string;
  output?: number | string;
};

type FetchState = "checking" | "online" | "offline";

interface Props {
  className?: string;
}

export function HomelabBackendHealthCard({ className = "" }: Props) {
  const [state, setState] = useState<FetchState>("checking");
  const [data, setData] = useState<HealthData>({});

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function poll() {
      try {
        const res = await fetch("/api/spirit/health", {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!active) return;
        if (res.ok) {
          const json = (await res.json()) as HealthData;
          if (!active) return;
          setData(json ?? {});
          setState("online");
        } else {
          setState("offline");
        }
      } catch {
        if (active) setState("offline");
      }
    }

    poll();
    const id = setInterval(poll, 20_000);
    return () => {
      active = false;
      clearInterval(id);
      controller.abort();
    };
  }, []);

  const badgeVariant = state === "online" ? "live" : state === "offline" ? "offline" : "pending";
  const badgeLabel = state === "checking" ? "Checking" : state === "online" ? "Online" : "Offline";

  return (
    <section
      aria-label="Backend Health"
      className={`homelab-panel p-4 ${className}`}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
            Spirit · Backend
          </p>
          <h2 className="mt-0.5 font-mono text-[15px] font-semibold uppercase tracking-tight text-chalk">
            Backend Health
          </h2>
        </div>
        <HomelabStatusBadge variant={badgeVariant}>{badgeLabel}</HomelabStatusBadge>
      </div>

      <dl className="grid gap-y-1 font-mono text-[11px]">
        {state === "offline" && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/[0.06] px-2 py-1.5 text-[10px] text-rose-300/90">
            Backend unreachable - /api/spirit/health returned no response
          </div>
        )}
        {data.url && (
          <div className="flex gap-x-2">
            <dt className="text-chalk/45">URL</dt>
            <dd className="min-w-0 truncate text-chalk/75">{data.url}</dd>
          </div>
        )}
        {data.engine && (
          <div className="flex gap-x-2">
            <dt className="text-chalk/45">Engine</dt>
            <dd className="text-[color:var(--spirit-accent-strong)]">{data.engine}</dd>
          </div>
        )}
        {data.model && (
          <div className="flex gap-x-2">
            <dt className="text-chalk/45">Model</dt>
            <dd className="min-w-0 truncate text-chalk/85">{data.model}</dd>
          </div>
        )}
        {data.context != null && (
          <div className="flex gap-x-2">
            <dt className="text-chalk/45">Context</dt>
            <dd className="tabular-nums text-chalk/75">{data.context}</dd>
          </div>
        )}
        {data.output != null && (
          <div className="flex gap-x-2">
            <dt className="text-chalk/45">Output cap</dt>
            <dd className="tabular-nums text-chalk/75">{data.output}</dd>
          </div>
        )}
        {state === "online" && !data.engine && !data.model && (
          <div className="text-chalk/40">Connected · no details returned</div>
        )}
      </dl>

      <div className="mt-3 border-t border-white/[0.06] pt-2">
        <Link
          href="/chat"
          className="font-mono text-[10px] text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110"
        >
          Open Chat →
        </Link>
      </div>
    </section>
  );
}
