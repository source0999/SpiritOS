from source_proxy.decision.campaign_3_conflicts import resolve_coding_lane_conflicts


def test_repository_truth_outranks_stale_obsidian_and_lowers_claim_ceiling() -> None:
    receipt = resolve_coding_lane_conflicts(task_id="task-1", claims=[
        {"lane_id": "repository_current", "subject": "api.contract", "value": "v2", "provenance": "git:abc"},
        {"lane_id": "obsidian_stale", "subject": "api.contract", "value": "v1", "provenance": "note:old", "freshness": "stale"},
    ])
    assert receipt["unresolved"] is False
    assert receipt["conflicts"][0]["selected"]["lane_id"] == "repository_current"
    assert receipt["claim_ceiling"] == "resolved_conflict_no_product_pass"


def test_equal_precedence_conflict_fails_closed() -> None:
    receipt = resolve_coding_lane_conflicts(task_id="task-2", claims=[
        {"lane_id": "scout_current", "subject": "provider.version", "value": "1", "provenance": "source:a"},
        {"lane_id": "scout_current", "subject": "provider.version", "value": "2", "provenance": "source:b"},
    ])
    assert receipt["unresolved"] is True
    assert receipt["claim_ceiling"] == "blocked_unresolved_conflict"
