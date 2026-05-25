from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import worker_contract
from source_proxy.cartographer.worker_contract import (
    MAX_WORKER_LOCK_RENEWALS,
    OWNERSHIP_ZONE_MODES,
    ONE_WORKER_FILE_ZONE_PROOF_PHASE,
    PROTECTED_WORKER_FILE_PREFIXES,
    REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS,
    REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS,
    REQUIRED_WORKER_HANDOFF_PACKET_FIELDS,
    REQUIRED_WORKER_CONTRACT_FIELDS,
    REQUIRED_WORKER_FILE_LOCK_FIELDS,
    REQUIRED_OWNERSHIP_ZONE_FIELDS,
    WORKER_LOCK_STATUSES,
    WORKER_CONFLICT_DETECTION_PHASE,
    WORKER_CONTRACT_MODEL_PHASE,
    WORKER_HANDOFF_PACKET_PHASE,
    STALE_WORKER_CLOSEOUT_PROPOSAL_PHASE,
    WORKER_OWNERSHIP_LOCK_PHASE,
    WORKER_ROLES,
    WORKER_STATUSES,
    WORKER_TRUST_TIER,
    WorkerContract,
    WorkerFileLock,
    WorkerHandoffPacket,
    OneWorkerFileZoneProof,
    WorkerOwnershipZone,
    build_one_worker_file_zone_proof_model_status,
    StaleWorkerCloseoutProposal,
    build_stale_worker_closeout_proposal_model_status,
    build_worker_conflict_detection_model_status,
    build_worker_contract_model_status,
    build_worker_handoff_packet_model_status,
    build_worker_ownership_lock_model_status,
    detect_worker_dispatch_conflicts,
    validate_worker_contract,
    validate_worker_handoff_packet,
    validate_one_worker_file_zone_proof,
    validate_stale_worker_closeout_proposal,
    validate_worker_ownership_lock,
)


class CartographerWorkerContractTests(unittest.TestCase):
    def test_status_is_model_only_and_grants_no_authority(self) -> None:
        status = build_worker_contract_model_status()

        self.assertEqual(status["plan"], "Cartographer Integrated Control Master Plan 8/10")
        self.assertEqual(status["phase"], WORKER_CONTRACT_MODEL_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(status["worker_roles"], WORKER_ROLES)
        self.assertEqual(status["worker_statuses"], WORKER_STATUSES)
        self.assertEqual(status["required_fields"], REQUIRED_WORKER_CONTRACT_FIELDS)
        self.assertEqual(status["required_trust_tier"], WORKER_TRUST_TIER)
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["worker_spawn_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["provider_call_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["background_loop_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])
        self.assertFalse(status["token_minting_available"])
        self.assertFalse(status["approval_storage_available"])

    def test_contract_captures_phase_8_1_fields_as_data(self) -> None:
        payload = self._contract().to_dict()

        self.assertEqual(payload["worker_id"], "worker-plan-8-1")
        self.assertEqual(payload["worker_name"], "Plan 8 Phase 1 Worker")
        self.assertEqual(payload["worker_role"], "codex")
        self.assertEqual(payload["assigned_task_id"], "task-plan-8-1")
        self.assertEqual(payload["allowed_files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(payload["forbidden_files"], ("source_proxy/api/cartographer.py",))
        self.assertEqual(payload["trust_tier"], WORKER_TRUST_TIER)
        self.assertEqual(payload["approval_token_id"], "approval-token-plan-8-phase-1")
        self.assertEqual(payload["status"], "active")
        self.assertTrue(payload["active"])
        self.assertFalse(payload["stale"])
        self.assertEqual(payload["current_step"], "model contract validation")
        self.assertEqual(payload["heartbeat_at"], "2026-05-23T12:00:00Z")
        self.assertEqual(payload["last_check_in_at"], "2026-05-23T12:00:00Z")
        self.assertIsNone(payload["blocked_reason"])
        self.assertEqual(payload["created_at"], "2026-05-23T11:55:00Z")
        self.assertEqual(payload["started_at"], "2026-05-23T11:59:00Z")
        self.assertIsNone(payload["completed_at"])
        self.assertTrue(payload["model_only"])
        self.assertFalse(payload["worker_spawn_available"])
        self.assertFalse(payload["worker_dispatch_available"])
        self.assertFalse(payload["provider_call_available"])
        self.assertFalse(payload["queue_execution_available"])
        self.assertFalse(payload["task_execution_available"])

    def test_valid_contract_accepts_without_dispatching_or_executing(self) -> None:
        result = validate_worker_contract(
            self._contract(),
            expected_approval_token_id="approval-token-plan-8-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.worker_id, "worker-plan-8-1")
        self.assertEqual(result.worker_name, "Plan 8 Phase 1 Worker")
        self.assertEqual(result.worker_role, "codex")
        self.assertEqual(result.assigned_task_id, "task-plan-8-1")
        self.assertEqual(result.worker_status, "active")
        self.assertEqual(result.trust_tier, WORKER_TRUST_TIER)
        self.assertEqual(result.approval_token_id, "approval-token-plan-8-phase-1")
        self.assertTrue(result.model_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.worker_spawn_available)
        self.assertFalse(result.worker_dispatch_available)
        self.assertFalse(result.provider_call_available)
        self.assertFalse(result.queue_execution_available)
        self.assertFalse(result.task_execution_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)
        self.assertFalse(result.token_minting_available)
        self.assertFalse(result.approval_storage_available)

    def test_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_WORKER_CONTRACT_FIELDS:
            payload = self._contract().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_worker_contract(
                    payload,
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertTrue(result.blocked)
                self.assertIn(f"missing_required_field:{field}", result.reasons)

    def test_role_trust_tier_and_approval_token_must_match_exactly(self) -> None:
        cases = [
            ({"worker_role": "autonomous_operator"}, "unknown_worker_role"),
            ({"trust_tier": "tier-2"}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, "wrong_approval_token"),
            ({}, "missing_expected_approval_token_id"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_contract(
                    {**self._contract().to_dict(), **override},
                    expected_approval_token_id="" if reason == "missing_expected_approval_token_id" else "approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_all_plan_8_1_roles_are_known_but_data_only(self) -> None:
        self.assertEqual(
            WORKER_ROLES,
            ("codex", "scout", "proxy", "designer", "blueprinter", "sub_cartographer"),
        )

        for role in WORKER_ROLES:
            with self.subTest(role=role):
                result = validate_worker_contract(
                    replace(self._contract(), worker_role=role),
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertTrue(result.accepted)
                self.assertEqual(result.worker_role, role)
                self.assertFalse(result.worker_dispatch_available)
                self.assertFalse(result.task_execution_available)
                self.assertFalse(result.write_authority_granted)

    def test_file_scope_must_be_exact_non_overlapping_and_nonempty(self) -> None:
        cases = [
            ({"allowed_files": ()}, "missing_allowed_files"),
            ({"forbidden_files": ()}, "missing_forbidden_files"),
            ({"allowed_files": ("docs/*.md",)}, "broad_allowed_files_entry"),
            ({"allowed_files": ("/tmp/example.md",)}, "broad_allowed_files_entry"),
            ({"allowed_files": ("docs/",)}, "broad_allowed_files_entry"),
            ({"forbidden_files": ("src/**",)}, "broad_forbidden_files_entry"),
            ({"allowed_files": ("docs/a.md", "docs/a.md")}, "duplicate_allowed_files_entry"),
            (
                {
                    "allowed_files": ("docs/cartographer-worker-registry.md",),
                    "forbidden_files": ("docs/cartographer-worker-registry.md",),
                },
                "allowed_file_forbidden",
            ),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_contract(
                    {**self._contract().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_active_stale_and_terminal_state_rules_fail_closed(self) -> None:
        cases = [
            ({"status": "active", "active": False}, "active_status_requires_active_state"),
            ({"status": "proposed", "active": True}, "active_state_status_mismatch"),
            ({"status": "stale", "stale": False}, "stale_status_requires_stale_state"),
            ({"status": "blocked", "active": False, "current_step": None}, "blocked_reason_required"),
            (
                {"status": "completed", "active": False, "current_step": None},
                "completed_at_required",
            ),
            ({"active": True, "stale": True}, "stale_state_status_mismatch"),
            ({"heartbeat_at": None}, "heartbeat_required"),
            ({"current_step": None}, "current_step_required"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_contract(
                    {**self._contract().to_dict(), **override},
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_ownership_lock_status_is_model_only_and_grants_no_authority(self) -> None:
        status = build_worker_ownership_lock_model_status()

        self.assertEqual(status["phase"], WORKER_OWNERSHIP_LOCK_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(status["ownership_zone_modes"], OWNERSHIP_ZONE_MODES)
        self.assertEqual(status["worker_lock_statuses"], WORKER_LOCK_STATUSES)
        self.assertEqual(status["max_lock_renewals"], MAX_WORKER_LOCK_RENEWALS)
        self.assertEqual(
            status["required_ownership_zone_fields"],
            REQUIRED_OWNERSHIP_ZONE_FIELDS,
        )
        self.assertEqual(
            status["required_worker_file_lock_fields"],
            REQUIRED_WORKER_FILE_LOCK_FIELDS,
        )
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["lock_storage_available"])
        self.assertFalse(status["conflict_detection_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["automatic_release_available"])
        self.assertFalse(status["lease_renewal_execution_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_ownership_zone_and_lock_capture_exact_file_zone_data(self) -> None:
        zone_payload = self._ownership_zone().to_dict()
        lock_payload = self._worker_lock().to_dict()

        self.assertEqual(zone_payload["zone_id"], "zone-plan-8-2")
        self.assertEqual(zone_payload["worker_id"], "worker-plan-8-1")
        self.assertEqual(zone_payload["assigned_task_id"], "task-plan-8-1")
        self.assertEqual(zone_payload["files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(zone_payload["mode"], "exclusive")
        self.assertEqual(zone_payload["trust_tier"], WORKER_TRUST_TIER)
        self.assertEqual(zone_payload["approval_token_id"], "approval-token-plan-8-phase-1")
        self.assertTrue(zone_payload["model_only"])
        self.assertFalse(zone_payload["lock_storage_available"])
        self.assertFalse(zone_payload["conflict_detection_available"])
        self.assertFalse(zone_payload["worker_dispatch_available"])

        self.assertEqual(lock_payload["lock_id"], "lock-plan-8-2")
        self.assertEqual(lock_payload["zone_id"], "zone-plan-8-2")
        self.assertEqual(lock_payload["worker_id"], "worker-plan-8-1")
        self.assertEqual(lock_payload["assigned_task_id"], "task-plan-8-1")
        self.assertEqual(lock_payload["files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(lock_payload["status"], "active")
        self.assertIsNone(lock_payload["renewed_at"])
        self.assertEqual(lock_payload["renewal_count"], 0)
        self.assertFalse(lock_payload["stale"])
        self.assertIsNone(lock_payload["released_at"])
        self.assertTrue(lock_payload["model_only"])
        self.assertFalse(lock_payload["automatic_release_available"])
        self.assertFalse(lock_payload["worker_dispatch_available"])

    def test_valid_ownership_lock_accepts_without_storage_dispatch_or_conflicts(self) -> None:
        result = validate_worker_ownership_lock(
            self._ownership_zone(),
            self._worker_lock(),
            expected_approval_token_id="approval-token-plan-8-phase-1",
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.zone_id, "zone-plan-8-2")
        self.assertEqual(result.lock_id, "lock-plan-8-2")
        self.assertEqual(result.worker_id, "worker-plan-8-1")
        self.assertEqual(result.assigned_task_id, "task-plan-8-1")
        self.assertEqual(result.files, ("docs/cartographer-worker-registry.md",))
        self.assertEqual(result.lock_status, "active")
        self.assertIsNone(result.renewed_at)
        self.assertEqual(result.renewal_count, 0)
        self.assertTrue(result.model_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.lock_storage_available)
        self.assertFalse(result.conflict_detection_available)
        self.assertFalse(result.worker_dispatch_available)
        self.assertFalse(result.queue_execution_available)
        self.assertFalse(result.task_execution_available)
        self.assertFalse(result.automatic_release_available)
        self.assertFalse(result.lease_renewal_execution_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_ownership_and_lock_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_OWNERSHIP_ZONE_FIELDS:
            zone_payload = self._ownership_zone().to_dict()
            zone_payload.pop(field)

            with self.subTest(zone_field=field):
                result = validate_worker_ownership_lock(
                    zone_payload,
                    self._worker_lock(),
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_ownership_zone_field:{field}", result.reasons)

        for field in REQUIRED_WORKER_FILE_LOCK_FIELDS:
            lock_payload = self._worker_lock().to_dict()
            lock_payload.pop(field)

            with self.subTest(lock_field=field):
                result = validate_worker_ownership_lock(
                    self._ownership_zone(),
                    lock_payload,
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_worker_file_lock_field:{field}", result.reasons)

    def test_ownership_lock_scope_must_be_exact_and_matching(self) -> None:
        cases = [
            ({"files": ()}, {}, "missing_ownership_zone_files"),
            ({"files": ("docs/*.md",)}, {}, "broad_files_entry"),
            ({"files": ("docs/a.md", "docs/a.md")}, {}, "duplicate_files_entry"),
            ({}, {"files": ()}, "missing_worker_file_lock_files"),
            ({}, {"files": ("docs/other.md",)}, "lock_files_must_match_ownership_zone"),
            ({}, {"zone_id": "other-zone"}, "lock_zone_mismatch"),
            ({}, {"worker_id": "other-worker"}, "lock_worker_mismatch"),
            ({}, {"assigned_task_id": "other-task"}, "lock_task_mismatch"),
        ]

        for zone_override, lock_override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_ownership_lock(
                    {**self._ownership_zone().to_dict(), **zone_override},
                    {**self._worker_lock().to_dict(), **lock_override},
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_ownership_lock_trust_token_and_state_rules_fail_closed(self) -> None:
        cases = [
            ({"mode": "shared"}, {}, "unknown_ownership_zone_mode"),
            ({"trust_tier": "tier-2"}, {}, "wrong_trust_tier"),
            ({"approval_token_id": "other-token"}, {}, "wrong_approval_token"),
            ({}, {"status": "held"}, "unknown_worker_file_lock_status"),
            ({}, {"status": "active", "stale": True}, "active_lock_cannot_be_stale"),
            (
                {},
                {"status": "active", "released_at": "2026-05-23T12:01:00Z"},
                "active_lock_cannot_be_released",
            ),
            ({}, {"status": "released"}, "released_lock_requires_released_at"),
            ({}, {"status": "stale"}, "stale_lock_requires_stale_flag"),
            (
                {},
                {"status": "stale", "stale": True},
                "stale_lock_requires_blocked_reason",
            ),
            ({}, {"expires_at": "2026-05-23T11:59:00Z"}, "lock_expires_at_not_after_acquired_at"),
            ({}, {"renewal_count": -1}, "renewal_count_out_of_bounds"),
            ({}, {"renewal_count": MAX_WORKER_LOCK_RENEWALS + 1}, "renewal_count_out_of_bounds"),
            ({}, {"renewal_count": True}, "invalid_renewal_count"),
            ({}, {"renewal_count": 1, "renewed_at": None}, "renewed_at_required"),
            (
                {},
                {"renewal_count": 0, "renewed_at": "2026-05-23T12:05:00Z"},
                "renewal_count_required",
            ),
            (
                {},
                {"renewal_count": 1, "renewed_at": "2026-05-23T11:59:00Z"},
                "renewed_at_before_acquired_at",
            ),
            (
                {},
                {"renewal_count": 1, "renewed_at": "2026-05-23T12:15:00Z"},
                "renewed_at_not_before_expires_at",
            ),
        ]

        for zone_override, lock_override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_ownership_lock(
                    {**self._ownership_zone().to_dict(), **zone_override},
                    {**self._worker_lock().to_dict(), **lock_override},
                    expected_approval_token_id="approval-token-plan-8-phase-1",
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_conflict_detection_status_blocks_dispatch_and_grants_no_authority(self) -> None:
        status = build_worker_conflict_detection_model_status()

        self.assertEqual(status["phase"], WORKER_CONFLICT_DETECTION_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertTrue(status["conflict_detection_available"])
        self.assertEqual(status["protected_file_prefixes"], PROTECTED_WORKER_FILE_PREFIXES)
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["conflict_resolution_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["automatic_cleanup_available"])
        self.assertFalse(status["automatic_lock_release_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_clean_conflict_report_is_preview_only_and_does_not_dispatch(self) -> None:
        report = detect_worker_dispatch_conflicts(
            candidate_files=("docs/new-worker-zone.md",),
            ownership_zones=(self._ownership_zone(),),
            worker_locks=(self._worker_lock(),),
            dirty_files=(),
            now=self._now(),
        )

        self.assertEqual(report.status, "clear")
        self.assertTrue(report.conflict_free)
        self.assertFalse(report.blocked)
        self.assertEqual(report.reasons, ())
        self.assertEqual(report.candidate_files, ("docs/new-worker-zone.md",))
        self.assertEqual(report.dirty_conflicts, ())
        self.assertEqual(report.ownership_conflicts, ())
        self.assertEqual(report.protected_lane_conflicts, ())
        self.assertEqual(report.stale_lock_conflicts, ())
        self.assertTrue(report.model_only)
        self.assertTrue(report.preview_only)
        self.assertFalse(report.conflict_resolution_available)
        self.assertFalse(report.worker_dispatch_available)
        self.assertFalse(report.automatic_cleanup_available)
        self.assertFalse(report.automatic_lock_release_available)
        self.assertFalse(report.write_authority_granted)

    def test_conflict_detection_blocks_dirty_overlapping_protected_and_stale_files(self) -> None:
        stale_lock = replace(
            self._worker_lock(),
            lock_id="lock-plan-8-2-stale",
            zone_id="zone-plan-8-2-stale",
            files=("docs/stale.md",),
            status="stale",
            stale=True,
            blocked_reason="heartbeat expired",
        )
        overlapping_zone = replace(
            self._ownership_zone(),
            zone_id="zone-plan-8-2-overlap",
            files=("docs/cartographer-worker-registry.md",),
        )

        report = detect_worker_dispatch_conflicts(
            candidate_files=(
                "docs/dirty.md",
                "docs/cartographer-worker-registry.md",
                "src/app/coding/page.tsx",
                "docs/stale.md",
            ),
            ownership_zones=(self._ownership_zone(), overlapping_zone),
            worker_locks=(self._worker_lock(), stale_lock),
            dirty_files=("docs/dirty.md",),
            now=self._now(),
        )

        self.assertEqual(report.status, "blocked")
        self.assertFalse(report.conflict_free)
        self.assertTrue(report.blocked)
        self.assertIn("dirty_file_conflict", report.reasons)
        self.assertIn("overlapping_file_ownership", report.reasons)
        self.assertIn("protected_lane_conflict", report.reasons)
        self.assertIn("stale_lock_ambiguity", report.reasons)
        self.assertEqual(report.dirty_conflicts, ("docs/dirty.md",))
        self.assertIn("docs/cartographer-worker-registry.md", report.ownership_conflicts)
        self.assertEqual(report.protected_lane_conflicts, ("src/app/coding/page.tsx",))
        self.assertEqual(report.stale_lock_conflicts, ("docs/stale.md",))
        self.assertFalse(report.worker_dispatch_available)
        self.assertFalse(report.conflict_resolution_available)
        self.assertFalse(report.automatic_cleanup_available)
        self.assertFalse(report.automatic_lock_release_available)

    def test_conflict_detection_fails_closed_on_malformed_or_broad_inputs(self) -> None:
        cases = [
            (
                {"candidate_files": "docs/a.md"},
                "invalid_candidate_files",
            ),
            (
                {"candidate_files": ("docs/*.md",)},
                "broad_candidate_files_entry",
            ),
            (
                {"dirty_files": "docs/a.md"},
                "invalid_dirty_files",
            ),
            (
                {"ownership_zones": "not-zones"},
                "malformed_ownership_zones",
            ),
            (
                {"worker_locks": "not-locks"},
                "malformed_worker_locks",
            ),
        ]

        for override, reason in cases:
            kwargs = {
                "candidate_files": ("docs/new-worker-zone.md",),
                "ownership_zones": (self._ownership_zone(),),
                "worker_locks": (self._worker_lock(),),
                "dirty_files": (),
                "now": self._now(),
            }
            kwargs.update(override)

            with self.subTest(reason=reason):
                report = detect_worker_dispatch_conflicts(**kwargs)

                self.assertTrue(report.blocked)
                self.assertIn(reason, report.reasons)
                self.assertFalse(report.worker_dispatch_available)
                self.assertFalse(report.write_authority_granted)

    def test_handoff_packet_status_is_model_only_and_grants_no_authority(self) -> None:
        status = build_worker_handoff_packet_model_status()

        self.assertEqual(status["phase"], WORKER_HANDOFF_PACKET_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(
            status["required_handoff_packet_fields"],
            REQUIRED_WORKER_HANDOFF_PACKET_FIELDS,
        )
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["worker_reassignment_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_handoff_packet_captures_task_scope_checks_receipts_and_closeout(self) -> None:
        payload = self._handoff_packet().to_dict()

        self.assertEqual(payload["handoff_id"], "handoff-plan-8-4")
        self.assertEqual(payload["task_id"], "task-plan-8-1")
        self.assertEqual(payload["source_worker_id"], "worker-plan-8-1")
        self.assertEqual(payload["target_worker_id"], "worker-plan-8-4")
        self.assertEqual(payload["assigned_files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(payload["scope"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(payload["expected_files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(payload["ownership_zone_id"], "zone-plan-8-2")
        self.assertEqual(payload["lock_id"], "lock-plan-8-2")
        self.assertEqual(payload["lock_status"], "active")
        self.assertEqual(payload["conflict_report_status"], "clear")
        self.assertEqual(payload["allowed_actions"], ("review", "handoff_closeout"))
        self.assertEqual(
            payload["forbidden_actions"],
            ("dispatch_worker", "execute_task", "write_files", "release_lock"),
        )
        self.assertEqual(payload["evidence_requirements"], ("clear_conflict_report", "active_lock"))
        self.assertEqual(payload["required_checks"], ("pytest:worker_contract",))
        self.assertEqual(payload["receipt_refs"], ("receipt:plan-8-phase-3",))
        self.assertEqual(payload["closeout_expectations"], ("human_review_required",))
        self.assertEqual(payload["closeout_summary"], "handoff packet format ready for review")
        self.assertTrue(payload["model_only"])
        self.assertTrue(payload["preview_only"])
        self.assertFalse(payload["worker_reassignment_available"])
        self.assertFalse(payload["worker_dispatch_available"])
        self.assertFalse(payload["task_execution_available"])

    def test_valid_handoff_packet_accepts_without_reassignment_or_dispatch(self) -> None:
        result = validate_worker_handoff_packet(
            self._handoff_packet(),
            expected_task_id="task-plan-8-1",
            expected_files=("docs/cartographer-worker-registry.md",),
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.handoff_id, "handoff-plan-8-4")
        self.assertEqual(result.task_id, "task-plan-8-1")
        self.assertEqual(result.source_worker_id, "worker-plan-8-1")
        self.assertEqual(result.target_worker_id, "worker-plan-8-4")
        self.assertEqual(result.expected_files, ("docs/cartographer-worker-registry.md",))
        self.assertTrue(result.model_only)
        self.assertTrue(result.preview_only)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.worker_reassignment_available)
        self.assertFalse(result.worker_dispatch_available)
        self.assertFalse(result.queue_execution_available)
        self.assertFalse(result.task_execution_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_handoff_packet_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_WORKER_HANDOFF_PACKET_FIELDS:
            payload = self._handoff_packet().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_worker_handoff_packet(
                    payload,
                    expected_task_id="task-plan-8-1",
                    expected_files=("docs/cartographer-worker-registry.md",),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_handoff_packet_field:{field}", result.reasons)

    def test_handoff_packet_scope_task_and_conflict_rules_fail_closed(self) -> None:
        cases = [
            ({"task_id": "other-task"}, "handoff_task_mismatch"),
            ({"source_worker_id": "worker-plan-8-4"}, "handoff_requires_distinct_workers"),
            ({"assigned_files": ()}, "missing_assigned_files"),
            ({"assigned_files": ("docs/other.md",)}, "handoff_assigned_files_mismatch"),
            ({"expected_files": ("docs/other.md",)}, "handoff_expected_files_mismatch"),
            (
                {"scope": ("docs/other.md",)},
                "handoff_scope_missing_expected_files",
            ),
            ({"lock_status": "stale"}, "handoff_requires_active_lock"),
            ({"allowed_actions": ()}, "missing_allowed_actions"),
            ({"forbidden_actions": ()}, "missing_forbidden_actions"),
            ({"evidence_requirements": ()}, "missing_evidence_requirements"),
            ({"required_checks": ()}, "missing_required_checks"),
            ({"receipt_refs": ()}, "missing_receipt_refs"),
            ({"closeout_expectations": ()}, "missing_closeout_expectations"),
            ({"closeout_summary": "pending"}, "closeout_summary_must_be_specific"),
            ({"conflict_report_status": "blocked"}, "handoff_requires_clear_conflict_report"),
            ({"expected_files": ("docs/*.md",)}, "broad_expected_files_entry"),
        ]

        for override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_worker_handoff_packet(
                    {**self._handoff_packet().to_dict(), **override},
                    expected_task_id="task-plan-8-1",
                    expected_files=("docs/cartographer-worker-registry.md",),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)

    def test_stale_worker_closeout_proposal_status_is_proposal_only(self) -> None:
        status = build_stale_worker_closeout_proposal_model_status()

        self.assertEqual(status["phase"], STALE_WORKER_CLOSEOUT_PROPOSAL_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(
            status["required_stale_worker_closeout_proposal_fields"],
            REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS,
        )
        self.assertTrue(status["proposal_only"])
        self.assertTrue(status["operator_review_required"])
        self.assertFalse(status["durable_storage_available"])
        self.assertFalse(status["automatic_cleanup_available"])
        self.assertFalse(status["automatic_lock_release_available"])
        self.assertFalse(status["worker_reassignment_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_stale_worker_closeout_proposal_captures_review_data_only(self) -> None:
        payload = self._stale_worker_closeout_proposal().to_dict()

        self.assertEqual(payload["proposal_id"], "stale-closeout-plan-8-5")
        self.assertEqual(payload["worker_id"], "worker-plan-8-1")
        self.assertEqual(payload["assigned_task_id"], "task-plan-8-1")
        self.assertEqual(payload["stale_reason"], "heartbeat expired before closeout")
        self.assertEqual(payload["affected_files"], ("docs/cartographer-worker-registry.md",))
        self.assertEqual(payload["recommended_operator_actions"], ("review stale lock and close worker manually",))
        self.assertEqual(payload["required_checks"], ("pytest:worker_contract",))
        self.assertEqual(payload["receipt_refs"], ("receipt:plan-8-phase-4",))
        self.assertTrue(payload["proposal_only"])
        self.assertTrue(payload["operator_review_required"])
        self.assertFalse(payload["automatic_cleanup_available"])
        self.assertFalse(payload["automatic_lock_release_available"])
        self.assertFalse(payload["worker_reassignment_available"])
        self.assertFalse(payload["worker_dispatch_available"])

    def test_valid_stale_worker_closeout_proposal_accepts_without_cleanup(self) -> None:
        result = validate_stale_worker_closeout_proposal(
            self._stale_worker_closeout_proposal(),
            stale_worker=self._stale_contract(),
            stale_locks=(self._stale_worker_lock(),),
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proposal_id, "stale-closeout-plan-8-5")
        self.assertEqual(result.worker_id, "worker-plan-8-1")
        self.assertEqual(result.assigned_task_id, "task-plan-8-1")
        self.assertEqual(result.affected_files, ("docs/cartographer-worker-registry.md",))
        self.assertTrue(result.stale_heartbeat_detected)
        self.assertFalse(result.blocked_worker_detected)
        self.assertTrue(result.expired_lease_detected)
        self.assertTrue(result.model_only)
        self.assertTrue(result.proposal_only)
        self.assertTrue(result.operator_review_required)
        self.assertFalse(result.durable_storage_available)
        self.assertFalse(result.automatic_cleanup_available)
        self.assertFalse(result.automatic_lock_release_available)
        self.assertFalse(result.worker_reassignment_available)
        self.assertFalse(result.worker_dispatch_available)
        self.assertFalse(result.queue_execution_available)
        self.assertFalse(result.task_execution_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_stale_worker_closeout_detects_blocked_worker_and_expired_lease(self) -> None:
        blocked_worker = replace(
            self._stale_contract(),
            status="blocked",
            stale=False,
            blocked_reason="manual operator review required",
        )
        expired_lock = replace(
            self._worker_lock(),
            expires_at="2026-05-23T12:01:00Z",
        )

        result = validate_stale_worker_closeout_proposal(
            self._stale_worker_closeout_proposal(),
            stale_worker=blocked_worker,
            stale_locks=(expired_lock,),
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertFalse(result.stale_heartbeat_detected)
        self.assertTrue(result.blocked_worker_detected)
        self.assertTrue(result.expired_lease_detected)
        self.assertFalse(result.automatic_cleanup_available)
        self.assertFalse(result.automatic_lock_release_available)
        self.assertFalse(result.worker_dispatch_available)

    def test_stale_worker_closeout_proposal_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS:
            payload = self._stale_worker_closeout_proposal().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_stale_worker_closeout_proposal(
                    payload,
                    stale_worker=self._stale_contract(),
                    stale_locks=(self._stale_worker_lock(),),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_stale_worker_closeout_proposal_field:{field}", result.reasons)

    def test_stale_worker_closeout_proposal_rules_fail_closed(self) -> None:
        cases = [
            ({}, self._contract(), (self._stale_worker_lock(),), "worker_not_stale"),
            ({"worker_id": "other-worker"}, self._stale_contract(), (self._stale_worker_lock(),), "proposal_worker_mismatch"),
            ({"assigned_task_id": "other-task"}, self._stale_contract(), (self._stale_worker_lock(),), "proposal_task_mismatch"),
            ({"affected_files": ("docs/other.md",)}, self._stale_contract(), (self._stale_worker_lock(),), "affected_files_lack_stale_lock_evidence"),
            ({"affected_files": ()}, self._stale_contract(), (self._stale_worker_lock(),), "missing_affected_files"),
            ({"stale_reason": "stale"}, self._stale_contract(), (self._stale_worker_lock(),), "stale_reason_must_be_specific"),
            ({"recommended_operator_actions": ()}, self._stale_contract(), (self._stale_worker_lock(),), "missing_recommended_operator_actions"),
            (
                {"recommended_operator_actions": ("kill process and reset stale files",)},
                self._stale_contract(),
                (self._stale_worker_lock(),),
                "unsafe_closeout_action",
            ),
            ({"required_checks": ()}, self._stale_contract(), (self._stale_worker_lock(),), "missing_required_checks"),
            ({"receipt_refs": ()}, self._stale_contract(), (self._stale_worker_lock(),), "missing_receipt_refs"),
            ({}, self._stale_contract(), (), "missing_stale_lock_evidence"),
        ]

        for override, stale_worker, stale_locks, reason in cases:
            with self.subTest(reason=reason):
                result = validate_stale_worker_closeout_proposal(
                    {**self._stale_worker_closeout_proposal().to_dict(), **override},
                    stale_worker=stale_worker,
                    stale_locks=stale_locks,
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.automatic_cleanup_available)
                self.assertFalse(result.automatic_lock_release_available)
                self.assertFalse(result.worker_reassignment_available)

    def test_one_worker_file_zone_proof_status_is_proof_only(self) -> None:
        status = build_one_worker_file_zone_proof_model_status()

        self.assertEqual(status["phase"], ONE_WORKER_FILE_ZONE_PROOF_PHASE)
        self.assertEqual(status["status"], "model-only")
        self.assertEqual(
            status["required_one_worker_file_zone_proof_fields"],
            REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS,
        )
        self.assertTrue(status["proof_only"])
        self.assertTrue(status["coordination_receipt_available"])
        self.assertFalse(status["worker_dispatch_available"])
        self.assertFalse(status["queue_execution_available"])
        self.assertFalse(status["task_execution_available"])
        self.assertFalse(status["command_authority_granted"])
        self.assertFalse(status["write_authority_granted"])
        self.assertFalse(status["git_mutation_authority_granted"])

    def test_one_worker_file_zone_proof_accepts_exact_single_worker_task_and_zone(self) -> None:
        result = validate_one_worker_file_zone_proof(
            self._one_worker_file_zone_proof(),
            worker=self._contract(),
            ownership_zone=self._ownership_zone(),
            worker_lock=self._worker_lock(),
            conflict_report=self._clear_conflict_report(),
            handoff_packet=self._handoff_packet(),
            now=self._now(),
        )

        self.assertTrue(result.accepted)
        self.assertFalse(result.blocked)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.proof_id, "proof-plan-8-6")
        self.assertEqual(result.worker_id, "worker-plan-8-1")
        self.assertEqual(result.assigned_task_id, "task-plan-8-1")
        self.assertEqual(result.file_zone, ("docs/cartographer-worker-registry.md",))
        self.assertIsNotNone(result.coordination_receipt)
        self.assertEqual(
            result.coordination_receipt["schema_version"],
            "cartographer.one_worker_file_zone_coordination_receipt.v1",
        )
        self.assertEqual(result.coordination_receipt["proof_id"], "proof-plan-8-6")
        self.assertEqual(result.coordination_receipt["worker_id"], "worker-plan-8-1")
        self.assertEqual(result.coordination_receipt["assigned_task_id"], "task-plan-8-1")
        self.assertEqual(
            result.coordination_receipt["file_zone"],
            ("docs/cartographer-worker-registry.md",),
        )
        self.assertEqual(result.coordination_receipt["worker_count"], 1)
        self.assertEqual(result.coordination_receipt["task_count"], 1)
        self.assertEqual(result.coordination_receipt["file_zone_count"], 1)
        self.assertFalse(result.coordination_receipt["worker_dispatch_performed"])
        self.assertFalse(result.coordination_receipt["queue_execution_performed"])
        self.assertFalse(result.coordination_receipt["task_execution_performed"])
        self.assertFalse(result.coordination_receipt["command_execution_performed"])
        self.assertFalse(result.coordination_receipt["safe_write_performed"])
        self.assertFalse(result.coordination_receipt["git_mutation_performed"])
        self.assertFalse(result.coordination_receipt["branch_or_worktree_created"])
        self.assertFalse(result.coordination_receipt["provider_call_performed"])
        self.assertFalse(result.coordination_receipt["durable_storage_performed"])
        self.assertTrue(result.model_only)
        self.assertTrue(result.proof_only)
        self.assertFalse(result.worker_dispatch_available)
        self.assertFalse(result.queue_execution_available)
        self.assertFalse(result.task_execution_available)
        self.assertFalse(result.command_authority_granted)
        self.assertFalse(result.write_authority_granted)
        self.assertFalse(result.git_mutation_authority_granted)

    def test_one_worker_file_zone_proof_required_fields_fail_closed(self) -> None:
        for field in REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS:
            payload = self._one_worker_file_zone_proof().to_dict()
            payload.pop(field)

            with self.subTest(field=field):
                result = validate_one_worker_file_zone_proof(
                    payload,
                    worker=self._contract(),
                    ownership_zone=self._ownership_zone(),
                    worker_lock=self._worker_lock(),
                    conflict_report=self._clear_conflict_report(),
                    handoff_packet=self._handoff_packet(),
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIn(f"missing_one_worker_file_zone_proof_field:{field}", result.reasons)

    def test_one_worker_file_zone_proof_blocks_any_mismatch_or_unclear_conflict(self) -> None:
        cases = [
            ({"worker_id": "other-worker"}, {}, {}, {}, {}, "proof_worker_mismatch"),
            ({"assigned_task_id": "other-task"}, {}, {}, {}, {}, "proof_task_mismatch"),
            ({"file_zone": ("docs/other.md",)}, {}, {}, {}, {}, "proof_file_zone_must_match_worker_allowed_files"),
            ({}, {"worker_id": "other-worker"}, {}, {}, {}, "proof_zone_worker_mismatch"),
            ({}, {}, {"status": "stale", "stale": True}, {}, {}, "proof_requires_active_lock"),
            ({}, {}, {}, {"status": "blocked", "conflict_free": False}, {}, "proof_requires_clear_conflict_report"),
            ({}, {}, {}, {}, {"conflict_report_status": "blocked"}, "proof_handoff_requires_clear_conflict_report"),
            ({"conflict_report_status": "blocked"}, {}, {}, {}, {}, "proof_requires_clear_conflict_status"),
        ]

        for proof_override, zone_override, lock_override, conflict_override, handoff_override, reason in cases:
            with self.subTest(reason=reason):
                result = validate_one_worker_file_zone_proof(
                    {**self._one_worker_file_zone_proof().to_dict(), **proof_override},
                    worker=self._contract(),
                    ownership_zone={**self._ownership_zone().to_dict(), **zone_override},
                    worker_lock={**self._worker_lock().to_dict(), **lock_override},
                    conflict_report={**self._clear_conflict_report().to_dict(), **conflict_override},
                    handoff_packet={**self._handoff_packet().to_dict(), **handoff_override},
                    now=self._now(),
                )

                self.assertFalse(result.accepted)
                self.assertIsNone(result.coordination_receipt)
                self.assertIn(reason, result.reasons)
                self.assertFalse(result.worker_dispatch_available)
                self.assertFalse(result.task_execution_available)
                self.assertFalse(result.write_authority_granted)

    def test_module_exposes_no_spawn_execution_write_storage_or_git_surface(self) -> None:
        source = inspect.getsource(worker_contract)
        forbidden_fragments = (
            "subprocess",
            "os.system",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "requests",
            "urllib",
            "socket",
            "source_proxy.api",
            "source_proxy.codex",
            "source_proxy.tasks",
            "source_proxy.testing.runner",
            "source_proxy.verification",
            "git add",
            "git branch",
            "git worktree",
            "git commit",
            "git push",
            "git merge",
            "git checkout",
            "git stash",
            "git clean",
            "git reset",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _contract() -> WorkerContract:
        return WorkerContract(
            worker_id="worker-plan-8-1",
            worker_name="Plan 8 Phase 1 Worker",
            worker_role="codex",
            assigned_task_id="task-plan-8-1",
            allowed_files=("docs/cartographer-worker-registry.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            trust_tier=WORKER_TRUST_TIER,
            approval_token_id="approval-token-plan-8-phase-1",
            status="active",
            active=True,
            stale=False,
            current_step="model contract validation",
            heartbeat_at="2026-05-23T12:00:00Z",
            last_check_in_at="2026-05-23T12:00:00Z",
            blocked_reason=None,
            created_at="2026-05-23T11:55:00Z",
            started_at="2026-05-23T11:59:00Z",
            completed_at=None,
        )

    @staticmethod
    def _stale_contract() -> WorkerContract:
        return WorkerContract(
            worker_id="worker-plan-8-1",
            worker_name="Plan 8 Phase 1 Worker",
            worker_role="codex",
            assigned_task_id="task-plan-8-1",
            allowed_files=("docs/cartographer-worker-registry.md",),
            forbidden_files=("source_proxy/api/cartographer.py",),
            trust_tier=WORKER_TRUST_TIER,
            approval_token_id="approval-token-plan-8-phase-1",
            status="stale",
            active=False,
            stale=True,
            current_step="waiting for manual closeout",
            heartbeat_at="2026-05-23T11:55:00Z",
            last_check_in_at="2026-05-23T11:55:00Z",
            blocked_reason="heartbeat expired",
            created_at="2026-05-23T11:50:00Z",
            started_at="2026-05-23T11:51:00Z",
            completed_at=None,
        )

    @staticmethod
    def _ownership_zone() -> WorkerOwnershipZone:
        return WorkerOwnershipZone(
            zone_id="zone-plan-8-2",
            worker_id="worker-plan-8-1",
            assigned_task_id="task-plan-8-1",
            files=("docs/cartographer-worker-registry.md",),
            mode="exclusive",
            trust_tier=WORKER_TRUST_TIER,
            approval_token_id="approval-token-plan-8-phase-1",
            created_at="2026-05-23T11:58:00Z",
        )

    @staticmethod
    def _worker_lock() -> WorkerFileLock:
        return WorkerFileLock(
            lock_id="lock-plan-8-2",
            zone_id="zone-plan-8-2",
            worker_id="worker-plan-8-1",
            assigned_task_id="task-plan-8-1",
            files=("docs/cartographer-worker-registry.md",),
            status="active",
            acquired_at="2026-05-23T12:00:00Z",
            expires_at="2026-05-23T12:15:00Z",
            released_at=None,
            stale=False,
            blocked_reason=None,
        )

    @staticmethod
    def _stale_worker_lock() -> WorkerFileLock:
        return WorkerFileLock(
            lock_id="lock-plan-8-2-stale",
            zone_id="zone-plan-8-2",
            worker_id="worker-plan-8-1",
            assigned_task_id="task-plan-8-1",
            files=("docs/cartographer-worker-registry.md",),
            status="stale",
            acquired_at="2026-05-23T12:00:00Z",
            expires_at="2026-05-23T12:01:00Z",
            released_at=None,
            stale=True,
            blocked_reason="heartbeat expired",
        )

    @staticmethod
    def _handoff_packet() -> WorkerHandoffPacket:
        return WorkerHandoffPacket(
            handoff_id="handoff-plan-8-4",
            task_id="task-plan-8-1",
            source_worker_id="worker-plan-8-1",
            target_worker_id="worker-plan-8-4",
            assigned_files=("docs/cartographer-worker-registry.md",),
            scope=("docs/cartographer-worker-registry.md",),
            expected_files=("docs/cartographer-worker-registry.md",),
            ownership_zone_id="zone-plan-8-2",
            lock_id="lock-plan-8-2",
            lock_status="active",
            conflict_report_status="clear",
            allowed_actions=("review", "handoff_closeout"),
            forbidden_actions=("dispatch_worker", "execute_task", "write_files", "release_lock"),
            evidence_requirements=("clear_conflict_report", "active_lock"),
            required_checks=("pytest:worker_contract",),
            receipt_refs=("receipt:plan-8-phase-3",),
            closeout_expectations=("human_review_required",),
            closeout_summary="handoff packet format ready for review",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _stale_worker_closeout_proposal() -> StaleWorkerCloseoutProposal:
        return StaleWorkerCloseoutProposal(
            proposal_id="stale-closeout-plan-8-5",
            worker_id="worker-plan-8-1",
            assigned_task_id="task-plan-8-1",
            stale_reason="heartbeat expired before closeout",
            affected_files=("docs/cartographer-worker-registry.md",),
            recommended_operator_actions=("review stale lock and close worker manually",),
            required_checks=("pytest:worker_contract",),
            receipt_refs=("receipt:plan-8-phase-4",),
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _clear_conflict_report():
        return detect_worker_dispatch_conflicts(
            candidate_files=("docs/cartographer-worker-registry.md",),
            ownership_zones=(),
            worker_locks=(),
            dirty_files=(),
            now=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        )

    @staticmethod
    def _one_worker_file_zone_proof() -> OneWorkerFileZoneProof:
        return OneWorkerFileZoneProof(
            proof_id="proof-plan-8-6",
            worker_id="worker-plan-8-1",
            assigned_task_id="task-plan-8-1",
            file_zone=("docs/cartographer-worker-registry.md",),
            ownership_zone_id="zone-plan-8-2",
            lock_id="lock-plan-8-2",
            handoff_id="handoff-plan-8-4",
            conflict_report_status="clear",
            created_at="2026-05-23T12:00:00Z",
        )

    @staticmethod
    def _now() -> datetime:
        return datetime(2026, 5, 23, 12, 5, tzinfo=UTC)


if __name__ == "__main__":
    unittest.main()
