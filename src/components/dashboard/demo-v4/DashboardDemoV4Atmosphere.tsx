"use client";

// ── DashboardDemoV4Atmosphere - lightweight 4-layer atmosphere ──────────────
// > Visual concept ported from `_reference/dashboardDemo/src/App.tsx` (atmosphere)
// > and `_reference/dashboardDemo/src/index.css`. Motion stays in CSS so mobile
// > can turn decorative work off without loading animation JavaScript.

export function DashboardDemoV4Atmosphere() {
  return (
    <div className="dashboard-demo-v4-atmosphere" aria-hidden>
      <div className="dashboard-demo-v4-atmosphere-foundation" />
      <div className="dashboard-demo-v4-atmosphere-wash" />
      <div className="dashboard-demo-v4-atmosphere-tint" />

      <div className="dashboard-demo-v4-atmosphere-blob dashboard-demo-v4-atmosphere-blob-a" />
      <div className="dashboard-demo-v4-atmosphere-blob dashboard-demo-v4-atmosphere-blob-b" />
      <div className="dashboard-demo-v4-atmosphere-glow" />

      <div className="dashboard-demo-v4-atmosphere-veil" />
    </div>
  );
}
