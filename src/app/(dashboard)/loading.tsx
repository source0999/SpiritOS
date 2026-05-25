// ── Dashboard loading - zero Tailwind (PostCSS can’t block first paint) ──────
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { bootSplashOuterStyle } from "@/lib/boot-splash";
import "@/styles/dashboard-demo-v4.css";

export default function DashboardLoading() {
  return (
    <div className="dashboard-demo-v4-route-shell">
      <div
        className="dashboard-demo-v4-route-main"
        style={bootSplashOuterStyle}
        aria-busy="true"
      >
        Booting Spirit OS…
      </div>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
