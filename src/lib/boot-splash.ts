// ── Shared inline paint for loading / error / client fail-safe ────────────────
// > No Tailwind here — if PostCSS detonates, this still paints.
import type { CSSProperties } from "react";

/** Dark Node void + chalk-muted label — matches blueprint `#090a0f` */
export const bootSplashOuterStyle: CSSProperties = {
  minHeight: "100dvh",
  backgroundColor: "#090a0f",
  color: "#94a3b8",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily:
    "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace",
  fontSize: 12,
  letterSpacing: "0.04em",
};
