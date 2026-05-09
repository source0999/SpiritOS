"use client";

// ── SpiritDesignDemo - orchestrating shell for the design demo ───────────────
// > Visual-only. Lives at /design-demo. Does NOT replace /, /chat, /oracle, or
// > /quarantine. All previews are scoped under .spirit-demo-root.
// > Mobile-first; bottom dock for ≤lg; side rail for lg+.
// > Reduced-motion is handled in CSS - see spirit-demo.animations.css.
import Link from "next/link";

import { DemoCommandCenter } from "./DemoCommandCenter";
import { DemoChatPreview } from "./DemoChatPreview";
import { DemoOraclePreview } from "./DemoOraclePreview";
import { DemoQuarantinePreview } from "./DemoQuarantinePreview";
import { DemoDiagnosticsPreview } from "./DemoDiagnosticsPreview";
import { DemoProfilePreview } from "./DemoProfilePreview";
import {
  DemoMobileDock,
  DEMO_SECTIONS,
} from "./DemoMobileDock";

function DesktopRail() {
  return (
    <aside
      className="demo-rail"
      aria-label="Design demo · desktop section rail"
    >
      <div className="demo-rail__brand" aria-hidden="true">
        S
      </div>
      {DEMO_SECTIONS.map((s) => (
        <a
          key={s.id}
          href={`#${s.id}`}
          className="demo-rail-btn"
          title={s.label}
          aria-label={`Jump to ${s.label}`}
        >
          <s.Icon size={16} />
        </a>
      ))}
    </aside>
  );
}

export function SpiritDesignDemo() {
  return (
    <div
      className="spirit-demo-root"
      data-testid="spirit-demo-root"
      data-demo="design-demo"
    >
      {/* - -  Atmospheric layer (decorative, not in tab order) - -  */}
      <div className="demo-atmos" aria-hidden="true">
        <span className="demo-atmos__aurora" />
        <span className="demo-atmos__grid" />
        <span className="demo-atmos__noise" />
        <span className="demo-atmos__vignette" />
      </div>

      {/* - -  Desktop-only rail (lg+) - -  */}
      <DesktopRail />

      {/* - -  Main shell - -  */}
      <div className="demo-shell">
        <header className="demo-topbar">
          <div className="demo-topbar__brand">
            <Link
              href="/"
              className="demo-btn demo-btn--ghost demo-btn--sm"
              aria-label="Back to dashboard"
            >
              ← Back
            </Link>
            <div>
              <p className="demo-topbar__title">Spirit OS · Design Demo</p>
              <p className="demo-topbar__sub">
                Visual rehearsal · not wired
              </p>
            </div>
          </div>
          <span className="demo-badge demo-badge--cyan">
            <span className="demo-pulse-dot" aria-hidden="true" />
            Demo · v0
          </span>
        </header>

        {/* - -  Top banner (visual-only label) - -  */}
        <div className="demo-banner" role="note" aria-label="Design demo banner">
          <span className="demo-banner__label">Visual-only</span>
          <span>
            Production lanes (/, /chat, /oracle, /quarantine) are untouched.
            Cards link only when a real route exists.
          </span>
        </div>

        <main aria-label="Design demo previews">
          <DemoCommandCenter />
          <DemoChatPreview />
          <DemoOraclePreview />
          <DemoQuarantinePreview />
          <DemoDiagnosticsPreview />
          <DemoProfilePreview />
        </main>

        <footer
          style={{
            paddingBlock: "2rem",
            borderTop: "1px solid var(--demo-border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <span className="demo-mock-tag">
            Spirit OS · Design Demo · /design-demo
          </span>
          <Link
            href="/"
            className="demo-btn demo-btn--ghost demo-btn--sm"
            aria-label="Return to dashboard"
          >
            ← Dashboard
          </Link>
        </footer>
      </div>

      {/* - -  Mobile dock (≤lg) - -  */}
      <DemoMobileDock />
    </div>
  );
}

export default SpiritDesignDemo;
