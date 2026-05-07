"use client";

// ── ThemeStrip - palette toggles from registry (client leaf) ────────────────────
// > Dashboard v2: pill dock borrows dashboardDemo chrome; still owns ThemeEngine paint.
import { useSpiritTheme } from "@/theme/useSpiritTheme";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";
import { cn } from "@/lib/cn";

export function ThemeStrip() {
  const { theme, setTheme } = useSpiritTheme();

  return (
    <div
      aria-label="Theme palette"
      className={cn(
        "spirit-dashboard-v2-theme-shell flex max-w-full shrink-0 flex-wrap justify-end gap-0.5",
        "max-md:mx-auto max-md:w-full max-md:max-w-[min(100%,20rem)] max-md:justify-center",
      )}
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
              "relative touch-manipulation overflow-hidden rounded-full font-mono text-[10px] font-semibold uppercase tracking-wide transition",
              "flex min-h-[44px] min-w-[44px] max-w-[5.25rem] flex-col items-center justify-center gap-0.5 px-1.5 py-2",
              "md:min-h-0 md:h-8 md:min-w-[2.85rem] md:max-w-none md:rounded-lg md:px-2 md:py-1.5",
              active
                ? "text-[color:var(--spirit-accent-strong)] shadow-[var(--spirit-theme-chip-active-glow)] ring-1 ring-[color:color-mix(in_oklab,var(--spirit-accent-strong)_22%,transparent)]"
                : "text-chalk/48 hover:bg-[color:color-mix(in_oklab,var(--spirit-accent)_7%,transparent)] hover:text-chalk/88",
            )}
            style={
              active
                ? {
                    background: "var(--spirit-theme-chip-active-bg)",
                  }
                : undefined
            }
          >
            <span className="relative z-[1] leading-none">{palette.shortLabel}</span>
            {active ? (
              <span
                aria-hidden
                className="h-0.5 w-[88%] max-w-[3rem] shrink-0 rounded-full opacity-95 md:w-[92%]"
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
