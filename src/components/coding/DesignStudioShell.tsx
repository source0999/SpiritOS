"use client";

import { Eye, FileJson, LockKeyhole, PanelRight, ShieldCheck } from "lucide-react";

const intakeFields = [
  ["Target", "Route or component"],
  ["Intent", "Visual direction"],
  ["Context", "Design refs"],
  ["Output", "Preview packet"],
];

const guardrails = [
  "No model call",
  "No apply authority",
  "No memory write",
  "No raw CSS ingest",
];

const packetRows = [
  ["design_packet_id", "preview-shell-local"],
  ["trace_id", "preview-shell-trace"],
  ["target_surface", "/coding/design-studio"],
  ["consumer_event_id", "blocked_until_packet_acceptance"],
];

export default function DesignStudioShell() {
  return (
    <main className="min-h-screen bg-[color:var(--spirit-bg)] text-chalk">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--spirit-border)] pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Design Studio
            </p>
            <h1 className="mt-1 text-2xl font-semibold text-[color:var(--spirit-accent-strong)]">
              Preview Workbench
            </h1>
          </div>
          <div className="flex flex-wrap gap-2">
            {guardrails.map((guardrail) => (
              <span
                className="rounded-md border border-[color:var(--spirit-border)] bg-white/[0.03] px-3 py-2 text-xs font-medium text-[color:var(--spirit-secondary-mix)]"
                key={guardrail}
              >
                {guardrail}
              </span>
            ))}
          </div>
        </header>

        <section className="grid flex-1 gap-5 lg:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.4fr)_minmax(280px,0.8fr)]">
          <aside className="rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.025] p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--spirit-accent-strong)]">
              <FileJson className="size-4" aria-hidden="true" />
              Intake
            </div>
            <div className="mt-4 space-y-3">
              {intakeFields.map(([label, value]) => (
                <label className="block" key={label}>
                  <span className="text-xs font-medium text-[color:var(--spirit-secondary-mix)]">
                    {label}
                  </span>
                  <input
                    className="mt-1 h-10 w-full rounded-md border border-[color:var(--spirit-border)] bg-black/20 px-3 text-sm text-chalk outline-none"
                    value={value}
                    readOnly
                  />
                </label>
              ))}
            </div>
          </aside>

          <section className="rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.02] p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--spirit-accent-strong)]">
                <Eye className="size-4" aria-hidden="true" />
                Surface Preview
              </div>
              <span className="rounded-md border border-amber-300/35 bg-amber-950/30 px-2.5 py-1 text-xs font-semibold text-amber-100">
                Draft only
              </span>
            </div>

            <div className="mt-4 min-h-[420px] rounded-lg border border-dashed border-[color:var(--spirit-border)] bg-black/20 p-4">
              <div className="grid h-full min-h-[380px] place-items-center rounded-md border border-white/10 bg-[linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.015))]">
                <div className="w-full max-w-lg px-4 text-center">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
                    Preview packet
                  </p>
                  <p className="mt-3 text-lg font-medium text-chalk">
                    Waiting for an accepted design packet before any apply path appears.
                  </p>
                  <div className="mt-6 grid gap-2 sm:grid-cols-2">
                    {["Desktop proof pending", "Mobile proof pending", "Critic pending", "Repair pending"].map(
                      (item) => (
                        <span
                          className="rounded-md border border-[color:var(--spirit-border)] bg-black/25 px-3 py-2 text-xs text-[color:var(--spirit-secondary-mix)]"
                          key={item}
                        >
                          {item}
                        </span>
                      ),
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <aside className="rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.025] p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--spirit-accent-strong)]">
              <PanelRight className="size-4" aria-hidden="true" />
              Packet State
            </div>
            <dl className="mt-4 space-y-3">
              {packetRows.map(([label, value]) => (
                <div
                  className="rounded-md border border-[color:var(--spirit-border)] bg-black/20 p-3"
                  key={label}
                >
                  <dt className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                    {label}
                  </dt>
                  <dd className="mt-1 break-words font-mono text-xs text-chalk">{value}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-4 grid gap-3">
              <div className="rounded-md border border-[color:var(--spirit-border)] bg-black/20 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                  Design Packet
                </p>
                <p className="mt-1 text-sm text-chalk">Preview-only design_packet is visible.</p>
              </div>
              <div className="rounded-md border border-[color:var(--spirit-border)] bg-black/20 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                  Coder Packet
                </p>
                <p className="mt-1 text-sm text-chalk">
                  Bounded coder_packet waits for sandbox apply approval.
                </p>
              </div>
            </div>
            <div className="mt-4 rounded-md border border-emerald-300/25 bg-emerald-950/20 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-emerald-100">
                <ShieldCheck className="size-4" aria-hidden="true" />
                Guard
              </div>
              <p className="mt-2 text-sm leading-6 text-emerald-50/80">
                Preview opening is not GO. Downstream consumption is required.
              </p>
            </div>
            <div className="mt-3 rounded-md border border-rose-300/25 bg-rose-950/20 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-rose-100">
                <LockKeyhole className="size-4" aria-hidden="true" />
                Apply locked
              </div>
              <p className="mt-2 text-sm leading-6 text-rose-50/80">
                Apply, commit, push, and memory write remain unavailable here.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
