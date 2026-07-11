from __future__ import annotations

import unittest

from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
    extend_context_broker_sources,
    render_context_broker_prompt,
)


def _source(**overrides: object) -> dict[str, object]:
    source: dict[str, object] = {
        "source": "cartographer",
        "considered": True,
        "status": "used",
        "reason": "repo_map_ready",
        "required": True,
        "selected": True,
        "included": True,
        "consumed": False,
        "packet": {"files_indexed": 12},
    }
    source.update(overrides)
    return source


def _ack(*sources: str, evidence: str = "prompt_hash:abc123") -> dict[str, object]:
    return {
        "applicable": True,
        "acknowledged": True,
        "sources": list(sources),
        "evidence": evidence,
        "reason": "consumer_used_canonical_packet",
    }


class CanonicalContextBrokerTests(unittest.TestCase):
    def test_optional_skipped_source_is_explicit_and_does_not_block(self) -> None:
        report = build_context_broker_report(
            [
                _source(
                    source="obsidian",
                    status="skipped",
                    reason="no_relevant_notes",
                    required=False,
                    selected=False,
                    included=False,
                )
            ]
        )

        source = report["sources_considered"][0]
        self.assertTrue(report["go_eligible"])
        self.assertEqual(report["verdict"], "GO_ELIGIBLE")
        self.assertTrue(source["considered"])
        self.assertEqual(source["requirement"], "optional")
        self.assertFalse(source["selected"])
        self.assertFalse(source["included"])
        self.assertFalse(source["consumed"])
        self.assertEqual(source["skipped_or_blocked_reason"], "no_relevant_notes")

    def test_required_unavailable_source_fails_closed(self) -> None:
        report = build_context_broker_report(
            [
                _source(
                    source="mac_worker",
                    status="unavailable",
                    reason="worker_not_configured",
                    selected=False,
                    included=False,
                )
            ]
        )

        self.assertFalse(report["go_eligible"])
        self.assertEqual(report["verdict"], "NO_GO_REQUIRED_CONTEXT")
        self.assertIn(
            "required_context_unavailable:mac_worker",
            report["required_context_blockers"],
        )

    def test_selected_source_without_applicable_consumer_cannot_fake_go(self) -> None:
        report = build_context_broker_report([_source(required=False, consumed=True)])

        source = report["sources_considered"][0]
        self.assertFalse(report["go_eligible"])
        self.assertFalse(source["consumed"])
        self.assertTrue(source["consumed_claimed"])
        self.assertIn(
            "selected_context_no_applicable_consumer:cartographer",
            report["required_context_blockers"],
        )
        self.assertIn(
            "context_consumption_claim_unproven:cartographer",
            report["required_context_blockers"],
        )

    def test_every_applicable_v2_consumer_must_acknowledge_selected_sources(self) -> None:
        report = build_context_broker_report(
            [_source()],
            downstream_consumers={"planner": _ack("cartographer")},
            applicable_consumers=("planner", "reviewer"),
        )

        source = report["sources_considered"][0]
        self.assertFalse(report["go_eligible"])
        self.assertFalse(source["consumed"])
        self.assertEqual(source["acknowledged_by"], ["planner"])
        self.assertEqual(source["missing_acknowledgements"], ["reviewer"])
        self.assertIn(
            "required_context_unacknowledged:cartographer:reviewer",
            report["required_context_blockers"],
        )
        report["task_id"] = "task-7"
        report["trace_id"] = "context-task-7"

        updated = acknowledge_context_consumer(
            report,
            consumer="reviewer",
            evidence="review_receipt:review-7",
        )

        self.assertTrue(updated["go_eligible"])
        self.assertEqual(updated["consumed_sources"], ["cartographer"])
        self.assertEqual(
            updated["sources_considered"][0]["acknowledged_by"],
            ["planner", "reviewer"],
        )
        self.assertEqual(updated["task_id"], "task-7")
        self.assertEqual(updated["trace_id"], "context-task-7")

    def test_acknowledgement_claim_without_evidence_is_not_truth(self) -> None:
        report = build_context_broker_report(
            [_source()],
            downstream_consumers={
                "planner": _ack("cartographer", evidence=""),
            },
            applicable_consumers=("planner",),
        )

        acknowledgement = report["downstream_acknowledgements"]["planner"]
        self.assertTrue(acknowledgement["acknowledged_claimed"])
        self.assertFalse(acknowledgement["acknowledged"])
        self.assertFalse(report["sources_considered"][0]["consumed"])
        self.assertIn(
            "context_acknowledgement_missing_evidence:planner",
            report["required_context_blockers"],
        )

    def test_duplicate_sources_and_unknown_acknowledged_source_fail_closed(self) -> None:
        report = build_context_broker_report(
            [_source(required=False), _source(required=False)],
            downstream_consumers={"planner": _ack("missing_source")},
            applicable_consumers=("planner",),
        )

        self.assertFalse(report["go_eligible"])
        self.assertIn(
            "duplicate_context_source:cartographer",
            report["required_context_blockers"],
        )
        self.assertIn(
            "context_acknowledges_unknown_source:planner:missing_source",
            report["required_context_blockers"],
        )

    def test_unsupported_consumer_name_fails_closed(self) -> None:
        report = build_context_broker_report(
            [_source(required=False, selected=False, included=False)],
            applicable_consumers=("renderer",),
        )

        self.assertFalse(report["go_eligible"])
        self.assertEqual(report["applicable_consumers"], [])
        self.assertIn(
            "unsupported_context_consumer:renderer",
            report["required_context_blockers"],
        )

    def test_late_bound_architect_context_is_added_to_the_same_broker(self) -> None:
        report = build_context_broker_report(
            [_source()],
            downstream_consumers={"planner": _ack("cartographer")},
            applicable_consumers=("planner",),
        )

        updated = extend_context_broker_sources(
            report,
            [
                _source(
                    source="architect_context_slices",
                    packet={"slices": [{"path": "app.py", "safe_excerpt": "print('ok')"}]},
                ),
                _source(
                    source="repomix_bundle_context",
                    status="skipped",
                    reason="architect_plan_has_no_repomix_bundle_snapshot",
                    required=False,
                    selected=False,
                    included=False,
                    packet={},
                ),
            ],
            planner_evidence="architect_packet_selected_before_coder",
        )

        self.assertTrue(updated["go_eligible"])
        self.assertIn("architect_context_slices", updated["selected_sources"])
        self.assertIn("architect_context_slices", updated["consumed_sources"])
        self.assertIn("architect_context_slices", render_context_broker_prompt(updated))
        self.assertIn("print('ok')", render_context_broker_prompt(updated))

    def test_late_bound_required_repomix_failure_blocks_before_coder(self) -> None:
        report = build_context_broker_report(
            [_source()],
            downstream_consumers={"planner": _ack("cartographer")},
            applicable_consumers=("planner",),
        )

        updated = extend_context_broker_sources(
            report,
            [
                _source(
                    source="repomix_bundle_context",
                    status="blocked",
                    reason="repomix_bundle_snapshot_hash_mismatch",
                    selected=False,
                    included=False,
                    packet={"expected_sha256": "a", "actual_sha256": "b"},
                )
            ],
            planner_evidence="architect_packet_selected_before_coder",
        )

        self.assertFalse(updated["go_eligible"])
        self.assertIn(
            "required_context_blocked:repomix_bundle_context",
            updated["required_context_blockers"],
        )


if __name__ == "__main__":
    unittest.main()
