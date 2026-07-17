from __future__ import annotations

from source_proxy.cartographer.lane_registry import (
    AUTHORITY_CLASSES,
    CORE_CODING_LANE_IDS,
    DEFAULT_LANE_IDS,
    DIRTY_OVERLAP_STATUSES,
    FALSE_LANE_AUTHORITY,
    LANE_RECORD_STATUSES,
    LANE_REGISTRY_MODEL_PHASE,
    OWNERSHIP_LOCK_PROPOSAL_PHASE,
    OWNERSHIP_LOCK_PROPOSAL_STATUSES,
    REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS,
    REQUIRED_LANE_RECORD_FIELDS,
    LaneRegistryRecord,
    OwnershipLockProposal,
    build_default_lane_registry,
    build_canonical_coding_lane_registry,
    build_lane_registry_model_status,
    build_ownership_lock_proposal_status,
    classify_lane_dirty_overlap,
    validate_ownership_lock_proposal,
    validate_lane_registry_record,
)


def test_lane_registry_status_is_authority_bearing_but_not_an_approval() -> None:
    status = build_lane_registry_model_status()

    assert status["phase"] == LANE_REGISTRY_MODEL_PHASE
    assert status["status"] == "authority-bearing"
    assert status["lane_ids"] == DEFAULT_LANE_IDS
    assert status["lane_record_statuses"] == LANE_RECORD_STATUSES
    assert status["dirty_overlap_statuses"] == DIRTY_OVERLAP_STATUSES
    assert status["required_lane_record_fields"] == REQUIRED_LANE_RECORD_FIELDS
    assert status["authority_classes"] == AUTHORITY_CLASSES
    assert status["proposal_only"] is False
    assert status["advisory_only"] is False
    assert status["authority"] == FALSE_LANE_AUTHORITY
    assert all(value is False for value in status["authority"].values())
    assert "task-scoped approval" in status["safe_next_action"]


def test_default_registry_has_one_active_cartographer_lane() -> None:
    registry = build_default_lane_registry()
    active_lanes = [lane for lane in registry if lane.active]
    cartographer_lane = next(lane for lane in registry if lane.lane_id == "cartographer")

    assert tuple(lane.lane_id for lane in registry) == DEFAULT_LANE_IDS
    assert [lane.lane_id for lane in active_lanes] == ["cartographer"]
    assert cartographer_lane.owner == "cartographer"
    assert cartographer_lane.status == "active"
    assert "source_proxy/cartographer/" in cartographer_lane.allowed_path_prefixes
    assert "source_proxy/tests/test_cartographer_" in cartographer_lane.allowed_path_prefixes
    assert "src/app/map/" in cartographer_lane.allowed_path_prefixes
    assert "src/app/coding/" in cartographer_lane.forbidden_path_prefixes
    assert "public/media/" in cartographer_lane.protected_path_prefixes
    assert cartographer_lane.proposal_only is True
    assert cartographer_lane.advisory_only is True
    assert cartographer_lane.authority_granted is False
    assert cartographer_lane.write_actions_enabled is False
    assert cartographer_lane.can_mutate is False


def test_valid_lane_registry_records_are_accepted_without_authority() -> None:
    for lane in build_default_lane_registry():
        result = validate_lane_registry_record(lane)

        assert result.accepted is True
        assert result.blocked is False
        assert result.status == "accepted"
        assert result.reason_codes == ()
        assert result.lane_id == lane.lane_id
        assert result.owner == lane.owner
        assert result.active is lane.active
        assert result.proposal_only is True
        assert result.advisory_only is True
        assert all(value is False for value in result.authority.values())


def test_required_lane_record_fields_fail_closed() -> None:
    lane = _cartographer_lane()

    for field in REQUIRED_LANE_RECORD_FIELDS:
        payload = lane.to_dict()
        payload.pop(field)

        result = validate_lane_registry_record(payload)

        assert result.accepted is False
        assert result.blocked is True
        assert f"missing_required_field:{field}" in result.reason_codes


def test_lane_vocabulary_active_state_and_path_rules_fail_closed() -> None:
    cases = [
        ({"lane_id": "unknown"}, "unknown_lane_id"),
        ({"owner": ""}, "missing_lane_owner"),
        ({"status": "running"}, "unknown_lane_status"),
        ({"status": "active", "active": False}, "active_status_requires_active_true"),
        ({"status": "inactive", "active": True}, "active_true_requires_active_status"),
        ({"allowed_path_prefixes": ()}, "missing_allowed_path_prefixes"),
        ({"forbidden_path_prefixes": ()}, "missing_forbidden_path_prefixes"),
        ({"protected_path_prefixes": ()}, "missing_protected_path_prefixes"),
        ({"allowed_path_prefixes": ("src/**",)}, "unsafe_allowed_path_prefixes:src/**"),
        ({"allowed_path_prefixes": ("/tmp/file.py",)}, "unsafe_allowed_path_prefixes:/tmp/file.py"),
        ({"allowed_path_prefixes": ("../outside",)}, "unsafe_allowed_path_prefixes:../outside"),
        (
            {
                "allowed_path_prefixes": ("source_proxy/cartographer/",),
                "forbidden_path_prefixes": ("source_proxy/cartographer/",),
            },
            "allowed_forbidden_path_overlap",
        ),
        ({"contract_name": ""}, "missing_lane_contract_name"),
        ({"contract_version": ""}, "missing_lane_contract_version"),
        ({"authority_class": "unbounded"}, "unknown_lane_authority_class"),
        ({"compatible_consumer_versions": ()}, "missing_compatible_consumer_versions"),
        ({"authority_granted": True}, "authority_must_be_false:authority_granted"),
        ({"can_mutate": True}, "authority_must_be_false:can_mutate"),
    ]

    for override, reason in cases:
        result = validate_lane_registry_record({**_cartographer_lane().to_dict(), **override})

        assert result.accepted is False
        assert result.blocked is True
        assert reason in result.reason_codes


def test_alternate_active_lane_is_explicit_and_one_at_a_time() -> None:
    registry = build_default_lane_registry(active_lane_id="docs")
    active_lanes = [lane for lane in registry if lane.active]
    docs_lane = next(lane for lane in registry if lane.lane_id == "docs")
    cartographer_lane = next(lane for lane in registry if lane.lane_id == "cartographer")

    assert [lane.lane_id for lane in active_lanes] == ["docs"]
    assert docs_lane.status == "active"
    assert cartographer_lane.status == "inactive"
    assert validate_lane_registry_record(docs_lane).accepted is True
    assert validate_lane_registry_record(cartographer_lane).accepted is True


def test_canonical_coding_registry_binds_every_contract_without_granting_authority() -> None:
    registry = build_canonical_coding_lane_registry()

    assert tuple(lane.lane_id for lane in registry) == CORE_CODING_LANE_IDS
    assert all(lane.active and lane.status == "active" for lane in registry)
    assert all(lane.contract_name == "coding/lane-contract" for lane in registry)
    assert all(lane.contract_version == "coding.lane-contract/v1.0.0" for lane in registry)
    assert all(lane.authority_class in AUTHORITY_CLASSES for lane in registry)
    assert all(lane.compatible_consumer_versions for lane in registry)
    assert all(lane.proposal_only is False and lane.advisory_only is False for lane in registry)
    assert all(validate_lane_registry_record(lane).accepted for lane in registry)
    assert all(lane.can_mutate is False and lane.authority_granted is False for lane in registry)


def test_ownership_lock_proposal_status_is_data_only() -> None:
    status = build_ownership_lock_proposal_status()

    assert status["phase"] == OWNERSHIP_LOCK_PROPOSAL_PHASE
    assert status["status"] == "proposal-only"
    assert status["ownership_lock_statuses"] == OWNERSHIP_LOCK_PROPOSAL_STATUSES
    assert (
        status["required_ownership_lock_proposal_fields"]
        == REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS
    )
    assert status["proposal_only"] is True
    assert status["advisory_only"] is True
    assert status["authority"] == FALSE_LANE_AUTHORITY
    assert all(value is False for value in status["authority"].values())
    assert "storing locks" in status["safe_next_action"]


def test_dirty_overlap_is_clear_for_active_lane_paths() -> None:
    lane = _cartographer_lane()
    result = classify_lane_dirty_overlap(
        _truth_packet(
            status="caution",
            dirty_paths=(
                "source_proxy/cartographer/lane_registry.py",
                "source_proxy/tests/test_cartographer_lane_registry.py",
                "src/app/map/page.tsx",
            ),
        ),
        lane,
    )

    assert result.status == "clear"
    assert result.blocked is False
    assert result.reason_codes == ()
    assert result.active_lane_id == "cartographer"
    assert result.allowed_dirty_paths == (
        "source_proxy/cartographer/lane_registry.py",
        "source_proxy/tests/test_cartographer_lane_registry.py",
        "src/app/map/page.tsx",
    )
    assert result.outside_lane_dirty_paths == ()
    assert result.forbidden_dirty_paths == ()
    assert result.protected_dirty_paths == ()
    assert all(value is False for value in result.authority.values())


def test_dirty_overlap_cautions_for_paths_outside_active_lane() -> None:
    result = classify_lane_dirty_overlap(
        _truth_packet(
            status="caution",
            dirty_paths=("docs/cartographer-auto-roadmap-v0.2.md",),
        ),
        _cartographer_lane(),
    )

    assert result.status == "caution"
    assert result.blocked is False
    assert result.reason_codes == ("dirty_paths_outside_active_lane",)
    assert result.outside_lane_dirty_paths == ("docs/cartographer-auto-roadmap-v0.2.md",)
    assert result.forbidden_dirty_paths == ()
    assert result.protected_dirty_paths == ()


def test_dirty_overlap_blocks_for_forbidden_and_protected_zones() -> None:
    result = classify_lane_dirty_overlap(
        _truth_packet(
            status="blocked",
            dirty_paths=("src/app/coding/page.tsx", "package.json"),
            protected_matches=(
                {"path": "src/app/coding/page.tsx", "lane": "coding"},
                {"path": "package.json", "lane": "package_config_env"},
            ),
        ),
        _cartographer_lane(),
    )

    assert result.status == "blocked"
    assert result.blocked is True
    assert "dirty_forbidden_path_overlap" in result.reason_codes
    assert "dirty_protected_zone_overlap" in result.reason_codes
    assert "protected_lane_matches_present" in result.reason_codes
    assert result.forbidden_dirty_paths == ("src/app/coding/page.tsx", "package.json")
    assert result.protected_dirty_paths == ("src/app/coding/page.tsx", "package.json")
    assert result.protected_lane_count == 2
    assert all(value is False for value in result.authority.values())


def test_dirty_overlap_fails_closed_for_unknown_stale_or_missing_paths() -> None:
    cases = [
        (
            _truth_packet(status="stale", stale_fields=("recency.collected_at",)),
            "stale",
            "truth_packet_stale",
        ),
        (
            _truth_packet(status="no_go", unknown_fields=("facts.current_branch",)),
            "unknown",
            "truth_packet_unknown",
        ),
        (
            _truth_packet(status="caution", dirty_paths=(), total_dirty_count=2),
            "unknown",
            "dirty_paths_missing",
        ),
        (
            {"schema_version": "cartographer.truth-packet.v0.0"},
            "unknown",
            "truth_packet_malformed",
        ),
    ]

    for packet, status, reason in cases:
        result = classify_lane_dirty_overlap(packet, _cartographer_lane())

        assert result.status == status
        assert result.blocked is True
        assert reason in result.reason_codes
        assert all(value is False for value in result.authority.values())


def test_valid_ownership_lock_proposal_accepts_without_enforcement() -> None:
    lane = _cartographer_lane()
    overlap = classify_lane_dirty_overlap(
        _truth_packet(
            status="caution",
            dirty_paths=("source_proxy/cartographer/lane_registry.py",),
        ),
        lane,
    )

    result = validate_ownership_lock_proposal(
        _lock_proposal(),
        lane,
        overlap,
        now="2026-05-24T00:00:00Z",
    )

    assert result.accepted is True
    assert result.blocked is False
    assert result.status == "accepted"
    assert result.reason_codes == ()
    assert result.lock_id == "lock-cartographer-plan-3"
    assert result.lease_id == "lease-cartographer-plan-3"
    assert result.lane_id == "cartographer"
    assert result.owner == "cartographer"
    assert result.exact_paths == ("source_proxy/cartographer/lane_registry.py",)
    assert result.dirty_overlap_status == "clear"
    assert result.proposal_only is True
    assert result.advisory_only is True
    assert all(value is False for value in result.authority.values())


def test_ownership_lock_required_fields_fail_closed() -> None:
    lane = _cartographer_lane()
    overlap = classify_lane_dirty_overlap(
        _truth_packet(
            status="caution",
            dirty_paths=("source_proxy/cartographer/lane_registry.py",),
        ),
        lane,
    )

    for field in REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS:
        payload = _lock_proposal().to_dict()
        payload.pop(field)

        result = validate_ownership_lock_proposal(
            payload,
            lane,
            overlap,
            now="2026-05-24T00:00:00Z",
        )

        assert result.accepted is False
        assert result.blocked is True
        assert f"missing_required_field:{field}" in result.reason_codes


def test_ownership_lock_exact_paths_status_and_authority_fail_closed() -> None:
    lane = _cartographer_lane()
    clear_overlap = classify_lane_dirty_overlap(
        _truth_packet(
            status="caution",
            dirty_paths=("source_proxy/cartographer/lane_registry.py",),
        ),
        lane,
    )
    dirty_overlap = classify_lane_dirty_overlap(
        _truth_packet(status="caution", dirty_paths=("docs/note.md",)),
        lane,
    )
    cases = [
        ({"lane_id": "docs"}, clear_overlap, "lock_lane_mismatch"),
        ({"owner": "other"}, clear_overlap, "lock_owner_mismatch"),
        ({"status": "stale"}, clear_overlap, "lock_status_not_acquirable:stale"),
        ({"exact_paths": ()}, clear_overlap, "missing_exact_paths"),
        ({"exact_paths": ("source_proxy/cartographer/",)}, clear_overlap, "unsafe_exact_path:source_proxy/cartographer/"),
        ({"exact_paths": ("source_proxy/**/*.py",)}, clear_overlap, "unsafe_exact_path:source_proxy/**/*.py"),
        ({"exact_paths": ("docs/note.md",)}, clear_overlap, "path_outside_active_lane:docs/note.md"),
        ({"exact_paths": ("src/app/coding/page.tsx",)}, clear_overlap, "path_forbidden:src/app/coding/page.tsx"),
        ({"exact_paths": ("package.json",)}, clear_overlap, "path_protected:package.json"),
        ({"expires_at": "2026-05-23T23:59:59Z"}, clear_overlap, "lock_expired"),
        ({"proposal_only": False}, clear_overlap, "lock_must_be_proposal_only"),
        ({"can_mutate": True}, clear_overlap, "authority_must_be_false:can_mutate"),
        ({}, dirty_overlap, "dirty_overlap_not_clear"),
    ]

    for override, overlap, reason in cases:
        result = validate_ownership_lock_proposal(
            {**_lock_proposal().to_dict(), **override},
            lane,
            overlap,
            now="2026-05-24T00:00:00Z",
        )

        assert result.accepted is False
        assert result.blocked is True
        assert reason in result.reason_codes
        assert all(value is False for value in result.authority.values())


def _cartographer_lane() -> LaneRegistryRecord:
    return next(lane for lane in build_default_lane_registry() if lane.lane_id == "cartographer")


def _lock_proposal() -> OwnershipLockProposal:
    return OwnershipLockProposal(
        lock_id="lock-cartographer-plan-3",
        lease_id="lease-cartographer-plan-3",
        lane_id="cartographer",
        owner="cartographer",
        scope="Plan 3 lane registry work",
        exact_paths=("source_proxy/cartographer/lane_registry.py",),
        status="proposed",
        created_at="2026-05-24T00:00:00Z",
        expires_at="2026-05-24T01:00:00Z",
    )


def _truth_packet(
    *,
    status: str,
    dirty_paths: tuple[str, ...] = (),
    total_dirty_count: int | None = None,
    protected_matches: tuple[dict[str, str], ...] = (),
    unknown_fields: tuple[str, ...] = (),
    stale_fields: tuple[str, ...] = (),
) -> dict[str, object]:
    dirty_count = len(dirty_paths) if total_dirty_count is None else total_dirty_count
    return {
        "schema_version": "cartographer.truth-packet.v0.1",
        "status": status,
        "facts": {
            "total_dirty_count": dirty_count,
            "tracked_dirty_files": list(dirty_paths),
            "untracked_files": [],
            "protected_lane_count": len(protected_matches),
            "protected_lane_matches": list(protected_matches),
        },
        "unknown_fields": list(unknown_fields),
        "stale_fields": list(stale_fields),
        "authority": dict(FALSE_LANE_AUTHORITY),
    }
