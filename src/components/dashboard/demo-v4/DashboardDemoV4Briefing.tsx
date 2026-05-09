import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/cn";

interface BriefingItem {
  category: string;
  headline: string;
}

const ITEMS: BriefingItem[] = [
  {
    category: "Local AI",
    headline: "Whisper STT routing stable, with Oracle text fallback ready.",
  },
  {
    category: "Homelab",
    headline: "Tesla P40 standby, PSU upgrade remains queued.",
  },
  {
    category: "Storage",
    headline: "Pool overview is telemetry-backed in the storage card.",
  },
  {
    category: "Energy",
    headline: "Energy notes are demo-only until live power telemetry lands.",
  },
];

const CATEGORY_STYLE: Record<string, string> = {
  "Local AI": "dashboard-demo-v4-briefing-category-ai",
  Homelab: "dashboard-demo-v4-briefing-category-homelab",
  Storage: "dashboard-demo-v4-briefing-category-storage",
  Energy: "dashboard-demo-v4-briefing-category-energy",
};

export function DashboardDemoV4Briefing() {
  return (
    <aside aria-label="Daily briefing" className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-briefing">
      <div className="dashboard-demo-v4-briefing-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Spirit briefing</p>
            <h2>Daily briefing</h2>
          </div>
        </div>
        <span className="dashboard-demo-v4-demo-label">Demo</span>
      </div>

      <ul className="dashboard-demo-v4-briefing-list">
        {ITEMS.map((item) => (
          <li key={item.category} className="dashboard-demo-v4-briefing-item">
            <span
              className={cn(
                "dashboard-demo-v4-briefing-category",
                CATEGORY_STYLE[item.category],
              )}
            >
              {item.category}
            </span>
            <p>{item.headline}</p>
          </li>
        ))}
      </ul>

      <p className="dashboard-demo-v4-briefing-footer">
        Static demo briefing. Live telemetry remains in System vitals and Storage pool.
      </p>
    </aside>
  );
}
