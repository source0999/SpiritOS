import { GlassPanel } from "@/components/ui/GlassPanel";

const scopeGuards = [
  ["Route", "/coding/design-demo sandbox only"],
  ["Apply", "component-local page diff"],
  ["Protected", "no production route, global CSS, or raw CSS ingest"],
];

const designPacket = [
  ["Intent", "A focused studio surface that proves the DesignDNA can become a real screen."],
  ["System", "Muted glass, crisp dividers, readable density, and restrained cyan-lime accents."],
  ["Behavior", "Static sandbox apply with explicit proof, rollback, and downstream handoff cues."],
];

const coderPacket = [
  "Replace the placeholder vibe canvas with a real applied design review surface.",
  "Keep all styling inside the sandbox page and existing shared UI primitives.",
  "Expose authority boundaries in the UI so a screenshot cannot masquerade as production apply.",
];

const proofRail = ["git apply --check", "bounded diff", "no global styles", "no real app route"];

export default function Page() {
  return (
    <main className="min-h-screen bg-[color:var(--spirit-bg)] text-chalk antialiased">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-8 px-5 py-10 sm:px-8 lg:px-10">
        <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Plan 09 Sandbox Apply
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-light leading-tight text-[color:var(--spirit-accent-strong)] sm:text-5xl lg:text-6xl">
              Design Studio apply proof for the demo sandbox
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[color:var(--spirit-secondary-mix)]">
              A model-authored screen diff is applied only to the design-demo route, turning the preview packet into a bounded runtime surface with visible authority guards.
            </p>
          </div>

          <GlassPanel as="aside" className="rounded-lg p-5">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Scope Fence
            </p>
            <div className="mt-4 space-y-3">
              {scopeGuards.map(([label, value]) => (
                <div className="grid grid-cols-[7rem_1fr] gap-3 border-t border-[color:var(--spirit-border)] pt-3 first:border-t-0 first:pt-0" key={label}>
                  <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                    {label}
                  </span>
                  <span className="text-sm leading-6 text-chalk">{value}</span>
                </div>
              ))}
            </div>
          </GlassPanel>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {designPacket.map(([title, body]) => (
            <GlassPanel as="article" className="rounded-lg p-5" key={title}>
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
                {title}
              </p>
              <p className="mt-4 text-sm leading-6 text-[color:var(--spirit-secondary-mix)]">
                {body}
              </p>
            </GlassPanel>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_0.72fr]">
          <GlassPanel as="section" className="rounded-lg p-5">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Coder Packet
            </p>
            <div className="mt-5 grid gap-3">
              {coderPacket.map((item, index) => (
                <div className="flex gap-3 border-t border-[color:var(--spirit-border)] pt-3 first:border-t-0 first:pt-0" key={item}>
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[color:var(--spirit-border)] font-mono text-[11px] text-[color:var(--spirit-accent)]">
                    {index + 1}
                  </span>
                  <p className="text-sm leading-6 text-chalk">{item}</p>
                </div>
              ))}
            </div>
          </GlassPanel>

          <GlassPanel as="section" className="rounded-lg p-5">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Apply Proof
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {proofRail.map((item) => (
                <span className="rounded-md border border-[color:var(--spirit-border)] px-3 py-2 font-mono text-[11px] uppercase tracking-[0.12em] text-[color:var(--spirit-secondary-mix)]" key={item}>
                  {item}
                </span>
              ))}
            </div>
            <p className="mt-5 text-sm leading-6 text-[color:var(--spirit-secondary-mix)]">
              The next verifier must consume this sandbox output before any real app screen apply can be considered.
            </p>
          </GlassPanel>
        </div>
      </section>
    </main>
  );
}
