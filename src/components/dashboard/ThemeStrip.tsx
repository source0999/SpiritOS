"use client";

// ── ThemeStrip - palette toggles from registry (client leaf) ────────────────────
// > Header uses md+ compact sizing; mobile / narrow keeps 44px touch floor.
import { useSpiritTheme } from "@/theme/useSpiritTheme";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";
import { cn } from "@/lib/cn";

export function ThemeStrip() {
  const { theme, setTheme } = useSpiritTheme();

  return (
    <div
      aria-label="Theme palette"
      className="glass flex shrink-0 flex-wrap gap-px rounded-lg p-[3px] sm:rounded-lg"
    >
      {SPIRIT_PALETTES.map((palette) => {
        const active = theme === palette.id;
        const stripe = palette.colors.map((c) => c.hex).join(", ");

        return (
          <button
            key={palette.id}
            type="button"
            title={palette.label}
            onClick={() => setTheme(palette.id)}
            aria-pressed={active}
            aria-label={`${palette.label} palette`}
            className={cn(
              "relative touch-manipulation overflow-hidden rounded-md font-mono text-[10px] font-semibold uppercase tracking-wide transition",
              "flex min-h-[44px] min-w-[44px] max-w-[5.5rem] flex-col items-center justify-center gap-0.5 max-md:px-2 max-md:py-2",
              "md:min-h-0 md:h-auto md:min-w-[2.75rem] md:max-w-none md:px-2 md:py-1.5",
              active
                ? "bg-[color:color-mix(in_oklab,var(--spirit-accent)_18%,transparent)] text-[color:var(--spirit-accent-strong)]"
                : "text-chalk/45 hover:bg-white/[0.04] hover:text-chalk/80",
            )}
          >
            <span className="relative z-[1] leading-none">{palette.shortLabel}</span>
            {active ? (
              <span
                aria-hidden
                className="h-0.5 w-[92%] max-w-[2.75rem] shrink-0 rounded-full opacity-90 md:w-full"
                style={{
                  background: `linear-gradient(90deg, ${stripe})`,
                }}
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
