import { GlassPanel } from "@/components/ui/GlassPanel";

const scopeGuards = [
  ["Route", "/coding/design-demo sandbox only"],
  ["Apply", "Plan 05.2 scoped sandbox diff"],
  ["Protected", ".env, global CSS, and production routes blocked"],
];

const designPacket = [
  ["Intent", "Turn the Design Studio packet into a real bounded review screen."],
  ["System", "Dense evidence panels, crisp scope rails, and restrained cyan-lime accents."],
  ["Behavior", "Static sandbox apply with trace, diff, and downstream handoff cues."],
];

const coderPacket = [
  "Apply only to src/app/coding/design-demo/page.tsx.",
  "Render the design_packet_hash and coder_packet_hash used for the sandbox handoff.",
  "Keep production routes, global styles, and protected paths outside the diff.",
];

const proofRail = ["bounded diff", "allowed file only", "protected paths blocked", "no production route"];

const repairLoop = [
  ["Critic", "critic-design-studio-trace-24e3574ecc8f-r-packet"],
  ["Repair", "repair-critic-design-studio-trace-24e3574ecc8f-r-packet-1"],
  ["Attempts", "1 of 2 bounded repair attempts"],
  ["Retest", "screenshot, anti-template, and critic rerun required"],
];

const traceFacts = [
  ["Trace", "design-studio-trace-24e3574ecc8f-r-packet"],
  ["Design", "999875b640e1270e38555d435c85a150573515c24d6e0a25d8f0022c039f6cf2"],
  ["Coder", "preview_bb110d8d"],
];

export default function Page() {
  return (
    <main className="min-h-screen bg-[color:var(--spirit-bg)] text-chalk antialiased">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-8 px-5 py-10 sm:px-8 lg:px-10">
        <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr] lg:items-end">
          <div>
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
              Plan 08 Bounded Repair
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-light leading-tight text-[color:var(--spirit-accent-strong)] sm:text-5xl lg:text-6xl">
              Critic-repaired Design Studio sandbox packet
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[color:var(--spirit-secondary-mix)]">
              The generated coder packet has been repaired only inside this design-demo route, with visible trace markers for screenshot, anti-template, and critic reruns.
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
              Trace Link
            </p>
            <div className="mt-5 space-y-3">
              {traceFacts.map(([label, value]) => (
                <div className="border-t border-[color:var(--spirit-border)] pt-3 first:border-t-0 first:pt-0" key={label}>
                  <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                    {label}
                  </p>
                  <p className="mt-1 break-all font-mono text-xs leading-5 text-chalk">{value}</p>
                </div>
              ))}
            </div>
          </GlassPanel>
        </div>

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

        <GlassPanel as="section" className="rounded-lg p-5">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--spirit-accent)]">
            Critic Repair Loop
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {repairLoop.map(([label, value]) => (
              <div className="border-t border-[color:var(--spirit-border)] pt-3 first:border-t-0 first:pt-0 sm:odd:border-t-0 sm:odd:pt-0" key={label}>
                <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-[color:var(--spirit-secondary-mix)]">
                  {label}
                </p>
                <p className="mt-1 break-words text-sm leading-6 text-chalk">{value}</p>
              </div>
            ))}
          </div>
        </GlassPanel>
      </section>
    </main>
  );
}
