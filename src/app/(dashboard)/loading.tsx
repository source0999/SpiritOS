// ── Dashboard loading - zero Tailwind (PostCSS can’t block first paint) ──────
import { bootSplashOuterStyle } from "@/lib/boot-splash";

export default function DashboardLoading() {
  return (
    <div style={bootSplashOuterStyle} aria-busy="true">
      Booting Spirit OS…
    </div>
  );
}
