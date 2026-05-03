"use client";

// ── ThemeStrip — ThemeEngine palette toggles (client leaf) ────────────────────
// > Header uses md+ compact sizing; mobile / narrow keeps 44px touch floor.
import { useSpiritTheme, type ThemeId } from "@/theme/useSpiritTheme";
import { cn } from "@/lib/cn";

const THEME_OPTIONS: { id: ThemeId; short: string }[] = [
  { id: "spirit-slate", short: "Slate" },
  { id: "dark-node", short: "Node" },
  { id: "legacy-violet", short: "Violet" },
];

export function ThemeStrip() {
  const { theme, setTheme } = useSpiritTheme();

  return (
    <div
      aria-label="Theme palette"
      className="glass flex shrink-0 flex-wrap gap-px rounded-lg p-[3px] sm:rounded-lg"
    >
      {THEME_OPTIONS.map(({ id, short }) => (
        <button
          key={id}
          type="button"
          onClick={() => setTheme(id)}
          aria-pressed={theme === id}
          className={cn(
            "touch-manipulation rounded-md font-mono text-[10px] font-semibold uppercase tracking-wide transition",
            /* Phone / chunky pointer: rails spec. md+: shave for density header. */
            "flex min-h-[44px] min-w-[44px] items-center justify-center max-md:px-3 max-md:py-2",
            "md:min-h-0 md:h-8 md:min-w-[2.75rem] md:px-2 md:py-1.5",
            theme === id
              ? "bg-[color:color-mix(in_oklab,var(--spirit-accent)_18%,transparent)] text-[color:var(--spirit-accent-strong)]"
              : "text-chalk/45 hover:bg-white/[0.04] hover:text-chalk/80",
          )}
        >
          {short}
        </button>
      ))}
    </div>
  );
}
