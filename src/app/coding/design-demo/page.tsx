import { GlassPanel } from "@/components/ui/GlassPanel";

const panels = [
  ["Surface", "Glass depth, border glow, and foreground contrast."],
  ["Rhythm", "Spacing, type scale, and responsive stacking."],
  ["Signal", "Accent color, quiet metadata, and hover-ready density."],
];

export default function Page() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[color:var(--spirit-bg)] text-chalk antialiased">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_110%_70%_at_50%_-10%,color-mix(in_oklab,var(--spirit-accent)_18%,transparent),transparent_58%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-16">
        <section className="mx-auto max-w-4xl text-center">
          <h1 className="text-6xl font-light tracking-tighter text-[color:var(--spirit-accent-strong)] drop-shadow-[0_0_44px_color-mix(in_oklab,var(--spirit-accent)_32%,transparent)]">
            Design Demo — Vibe Test Canvas
          </h1>
        </section>

        <section className="mt-14 grid gap-4 md:grid-cols-3">
          {panels.map(([title, body]) => (
            <GlassPanel className="min-h-36 p-5" key={title}>
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-[color:var(--spirit-accent)]">
                {title}
              </p>
              <p className="mt-4 text-sm leading-6 text-[color:var(--spirit-secondary-mix)]">
                {body}
              </p>
            </GlassPanel>
          ))}
        </section>
      </div>
    </main>
  );
}
