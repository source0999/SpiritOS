# Cartographer v1 Evidence Artifacts

Cartographer v1 readiness reads proof and freeze-marker artifacts as evidence only. These files may be recorded by a human or an external tool after review, but Cartographer must not create, edit, delete, commit, push, or approve them by itself.

## Authority Boundary

- `write_actions_enabled` remains `false`.
- `authority_granted` remains `false`.
- `actions_taken` remains `false`.
- Passing tests or recorded artifacts do not grant apply, commit, push, cleanup, or promotion authority.
- Dry-run endpoints are previews only; they do not satisfy readiness until real artifacts exist and validate.

## Proof Gate Artifact

Accepted paths:

- `data/cartographer-v1-proof-gates/*.json`
- `data/*.json`
- `source_proxy/cartographer/soak-logs/*.json`

Contract version:

- `cartographer.v1.proof_artifact.v1`

Minimum shape:

```json
{
  "profile": "cartographer-v1-proof-gates",
  "result": "pass",
  "generated_at": "2026-05-18T00:00:00Z",
  "head_sha": "example-head-sha",
  "branch": "main",
  "checks": [
    { "id": "typecheck", "status": "passed", "summary": "tsc --noEmit passed" },
    { "id": "lint", "status": "warnings_only", "summary": "eslint completed with warnings only" },
    { "id": "blueprint_metadata_validation", "status": "passed" },
    { "id": "git_diff_check", "status": "passed" },
    { "id": "targeted_vitest", "status": "passed" }
  ]
}
```

Validation endpoint:

```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-proof-validation | jq .
```

## Freeze Marker Artifact

Accepted path:

- `data/cartographer-v1-freeze/freeze-marker.json`

Marker version:

- `cartographer.v1.freeze_marker.v1`

Minimum shape:

```json
{
  "marker_version": "cartographer.v1.freeze_marker.v1",
  "created_at": "2026-05-18T00:00:00Z",
  "head_sha": "example-head-sha",
  "branch": "main",
  "readiness": "ready",
  "v1_ready": true,
  "evidence_summary": {
    "current_missing_count": 0,
    "current_missing_evidence": [],
    "remaining_after_dry_run": []
  },
  "authority_boundary": {
    "write_actions_enabled": false,
    "authority_granted": false,
    "actions_taken": false,
    "passing_tests_grant_authority": false
  }
}
```

Validation endpoint:

```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
```

## Closeout Status

Use the dashboard rollup to see the current state without stitching endpoints together:

```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
```

Expected safety invariants:

- `dashboard_mode` is `read_only_v1_closeout_surface`.
- `write_actions_enabled` is `false`.
- `authority_granted` is `false`.
- `actions_taken` is `false`.
- The authority card remains locked.

## Closeout Surfaces

Use these read-only surfaces during final review:

```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-audit-summary | jq .
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-endpoints | jq .
```

Surface purposes:

- `/v1/cartographer/v1-closeout-dashboard` provides the compact UI-ready rollup.
- `/v1/cartographer/v1-closeout-audit-summary` summarizes blockers, docs, surfaces, and safety invariants.
- `/v1/cartographer/v1-closeout-endpoints` lists v1 closeout endpoints and confirms each listed endpoint is read-only.

Expected endpoint index invariants:

- `index_mode` is `read_only_v1_closeout_endpoint_index`.
- Every endpoint entry has `read_only: true`.
- `docs_path` is `docs/cartographer-v1-evidence-artifacts.md`.
- `audit_endpoint` is `/v1/cartographer/v1-closeout-audit-summary`.
- `dashboard_endpoint` is `/v1/cartographer/v1-closeout-dashboard`.
