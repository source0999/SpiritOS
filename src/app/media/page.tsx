import { MediaExperience } from "@/components/media/MediaExperience";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

export default function MediaPage() {
  return (
    <div className="dashboard-demo-v4-route-shell dashboard-demo-v4-route-shell-media">
      <div className="dashboard-demo-v4-route-main">
        <MediaExperience />
      </div>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
