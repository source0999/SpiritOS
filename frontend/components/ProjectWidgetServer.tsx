// Async Server Component — intentionally has no "use client" directive.
// Reads README.md on the server at request time (zero client-side cost) and
// passes completion overrides down to the existing Client Component.

import { PROJECTS }           from "@/lib/mockProjects";
import { getReadmeCompletion } from "@/lib/readmeProgress";
import { ProjectWidget }       from "./ProjectWidget";

export default async function ProjectWidgetServer() {
  // For each project, attempt a README-driven completion value.
  // Repos without a REPO_SCOPE entry return null → the Client Component
  // falls back to the hardcoded value in lib/mockProjects.ts.
  const completionOverrides: Record<string, number> = {};

  for (const proj of PROJECTS) {
    const pct = getReadmeCompletion(proj.repo);
    if (pct !== null) {
      completionOverrides[proj.repo] = pct;
    }
  }

  return <ProjectWidget completionOverrides={completionOverrides} />;
}
