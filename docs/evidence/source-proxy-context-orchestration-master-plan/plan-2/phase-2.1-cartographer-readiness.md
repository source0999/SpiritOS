# Plan 2 Phase 2.1 - Cartographer Readiness

Status: GO

## Increment 2.1.1 - Repo map packet shape

Implemented `build_cartographer_context_packet` in `source_proxy/context/source_readiness.py`.

Packet includes:

- `repo_map`
- bounded `files` and `unmapped_paths`
- `files_indexed`
- `symbols_indexed`
- `key_directories`
- `api_routes`
- `tests`
- `blueprints`

Test:

`test_cartographer_packet_includes_repo_component_dirty_and_blueprint_truth`

Result:

`source_proxy/tests/test_context_source_readiness.py`: `6 passed in 0.19s`

Decision: GO.

## Increment 2.1.2 - Component map packet shape

Packet includes `component_map` from existing Cartographer component mapping rules.

The test fixture maps `src/components/dashboard/Widget.tsx` through the existing component rules instead of inventing a separate ownership model.

Decision: GO.

## Increment 2.1.3 - Dirty-tree status

Packet includes:

- `available`
- `dirty`
- `branch`
- `head_sha`
- `changed_files`
- `changed_file_count`

The temp fixture reports clean state as `no_dirty_tree_conflict_detected`.

Decision: GO.

## Increment 2.1.4 - Ownership/conflict status

Packet includes `ownership_conflict_status`:

- `dirty_tree_present_review_required`
- `no_dirty_tree_conflict_detected`

This is advisory only and does not claim ownership, apply, branch, commit, or queue authority.

Decision: GO.

## Increment 2.1.5 - Architecture/blueprint truth

Packet includes `architecture_blueprint_truth` with count, paths, and status. It uses existing blueprint registry when available and falls back to `_blueprints/*.md` path truth.

Decision: GO.

## Increment 2.1.6 - Context packet adapter shape

Packet includes `context_packet_adapter` with emitted fields and schema version. Authority is read-only:

- `can_apply: false`
- `can_commit: false`
- `can_push: false`
- `can_start_worker: false`

Live read-only check against `/home/source/SpiritOS`:

- `cartographer`: `used`
- reason: `cartographer_packet_ready`
- files indexed: `180`

## Phase Closeout

Phase 2.1 GO. Cartographer can produce a real Source Proxy-readable packet with repo map, component map, dirty tree, ownership/conflict status, and blueprint truth. No route-exists acceptance was used.

