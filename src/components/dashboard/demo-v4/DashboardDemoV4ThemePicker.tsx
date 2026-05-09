"use client";

import { useEffect } from "react";
import type { CSSProperties } from "react";
import { createPortal } from "react-dom";
import { Check, X } from "lucide-react";

import { cn } from "@/lib/cn";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";
import { useSpiritTheme } from "@/theme/useSpiritTheme";

interface DashboardDemoV4ThemePickerProps {
  open: boolean;
  onClose: () => void;
}

export function DashboardDemoV4ThemePicker({
  open,
  onClose,
}: DashboardDemoV4ThemePickerProps) {
  const { theme, setTheme } = useSpiritTheme();

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open || typeof document === "undefined") return null;

  const picker = (
    <div className="dashboard-demo-v4-interface-layer">
      <button
        type="button"
        className="dashboard-demo-v4-interface-backdrop"
        aria-label="Close interface theme picker"
        onClick={onClose}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Interface theme picker"
        className="dashboard-demo-v4-interface-panel"
      >
            <div className="dashboard-demo-v4-interface-header">
              <div>
                <p className="dashboard-demo-v4-interface-kicker">Visual system</p>
                <h2>Interface</h2>
                <p>Choose a visual system</p>
              </div>
              <button
                type="button"
                className="dashboard-demo-v4-interface-close"
                aria-label="Close interface theme picker"
                onClick={onClose}
              >
                <X className="h-4 w-4" aria-hidden />
              </button>
            </div>

            <div className="dashboard-demo-v4-interface-grid">
              {SPIRIT_PALETTES.map((palette) => {
                const active = theme === palette.id;
                const gradient = palette.colors.map((color) => color.hex).join(", ");

                return (
                  <button
                    key={palette.id}
                    type="button"
                    aria-pressed={active}
                    className={cn(
                      "dashboard-demo-v4-interface-card",
                      active && "dashboard-demo-v4-interface-card-active",
                    )}
                    onClick={() => {
                      setTheme(palette.id);
                      onClose();
                    }}
                  >
                    <span
                      className={cn(
                        "dashboard-demo-v4-interface-preview",
                        `dashboard-demo-v4-interface-preview-${palette.previewPattern ?? "none"}`,
                      )}
                      style={{
                        background: palette.previewSurface,
                        "--dashboard-demo-v4-preview-accent": palette.previewAccent,
                      } as CSSProperties}
                      aria-hidden
                    >
                      <span style={{ background: `linear-gradient(135deg, ${gradient})` }} />
                    </span>

                    <span
                      className="dashboard-demo-v4-interface-accent"
                      style={{
                        background: palette.previewAccent,
                        boxShadow: `0 0 18px 2px ${palette.previewAccent}66`,
                      }}
                      aria-hidden
                    />

                    <span className="dashboard-demo-v4-interface-card-copy">
                      <strong>{palette.label}</strong>
                      <span>{palette.toneLabel}</span>
                    </span>

                    {active ? (
                      <span className="dashboard-demo-v4-interface-check" aria-hidden>
                        <Check className="h-3.5 w-3.5" />
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
      </div>
    </div>
  );

  return createPortal(picker, document.body);
}
