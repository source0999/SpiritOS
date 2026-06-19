# Build Vs Adapt Comparison

Current source already contains long-running task state, Cartographer workflow state, workflow event ledger, central gate, worker protocols, Scout, SearXNG, Obsidian retrieval, model lanes, verifiers, and UI routes.

Initial planning conclusion: `REUSE_EXISTING_ORCHESTRATION` with targeted adaptation is the default Plan 0.5 recommendation unless Plan 0 proves a component is broken beyond repair. Build-new is allowed only when an existing path is explicitly superseded, no parallel orchestrator remains, and Britton approves.
