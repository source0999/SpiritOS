import { AuthorizedMediaImporter } from "@/components/converter/AuthorizedMediaImporter";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

export default function ConverterPage() {
  return (
    <div className="dashboard-demo-v4-route-shell">
      <div className="dashboard-demo-v4-route-main">
        <AuthorizedMediaImporter />
      </div>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
