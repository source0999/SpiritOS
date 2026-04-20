// Server Component — no "use client".
// Reads README.md server-side (via ProjectWidgetServer → lib/readmeProgress.ts)
// and passes the rendered widget as a slot prop to the Client Component shell.
// This is the Next.js 15 "composition pattern": Server Components can be passed
// as children/props to Client Components without crossing the fs boundary.

import DashboardContent   from "@/components/DashboardContent";
import ProjectWidgetServer from "@/components/ProjectWidgetServer";
import { logDebugSession } from "@/lib/debugSessionLog";

export default function Page() {
  // #region agent log
  logDebugSession({
    hypothesisId: "C",
    location: "app/page.tsx:Page",
    message: "Home Page render (server)",
  });
  // #endregion
  return (
    <DashboardContent
      projectWidget={<ProjectWidgetServer />}
    />
  );
}
