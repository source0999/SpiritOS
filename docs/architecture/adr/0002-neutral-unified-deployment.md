# ADR 0002: Serve unified Next from a neutral integration worktree

Decision: 3000/3002 must be owned by a neutral integration/campaign worktree, never by either product branch.
Reason: prevents stale SpiritFlix snapshots from replacing the approved current implementation.
Consequences: exact source, branch, HEAD, build, artifact, CWD, and port provenance is required before cutover.
Campaign 2 dependency: final deployment ownership after layout migration.
Revision condition: a verified deployment model supplies equivalent non-product ownership and provenance.