from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import level_13_worker_runtime
from source_proxy.cartographer.level_13_worker_runtime import (
    CartographerLevel13OwnershipZone,
    CartographerLevel13WorkerLease,
    CartographerLevel13WorkerRecord,
    build_level_13_branch_worktree_proposal_dry_run,
    build_level_13_closeout_level_14_access_check,
    build_level_13_conflict_detection_dry_run_packet,
    build_level_13_handoff_packet_dry_run,
    build_level_13_stale_worker_handling_dry_run,
    build_level_13_worker_closeout_packet_dry_run,
    validate_level_13_ownership_zone_dry_run,
    validate_level_13_worker_lease_dry_run,
    validate_level_13_worker_registry_dry_run,
)


class CartographerLevel13WorkerRuntimeTests(unittest.TestCase):
    def test_13_1_worker_registry_validates_without_dispatch_authority(self) -> None:
        result = validate_level_13_worker_registry_dry_run((self._worker(),))

        self.assertEqual(result.level, "13.1")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.worker_dispatch_authority_granted)
        self.assertFalse(result.branch_worktree_authority_granted)
        self.assertFalse(result.write_authority_granted)

    def test_13_1_registry_presence_never_grants_authority(self) -> None:
        result = validate_level_13_worker_registry_dry_run(
            (replace(self._worker(), allowed_files=("src/app/coding/page.tsx",)),)
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("protected_path_in_scope", result.blocked_reasons)
        self.assertFalse(result.worker_dispatch_authority_granted)

    def test_13_2_worker_lease_is_scope_only_and_fails_closed(self) -> None:
        result = validate_level_13_worker_lease_dry_run(self._worker(), self._lease())

        self.assertEqual(result.level, "13.2")
        self.assertTrue(result.valid_for_dry_run)
        self.assertFalse(result.worker_dispatch_authority_granted)

        broad = validate_level_13_worker_lease_dry_run(
            self._worker(),
            replace(self._lease(), files=("docs/worker.md", "docs/other.md")),
        )
        self.assertFalse(broad.valid_for_dry_run)
        self.assertIn("lease_scope_exceeds_worker_scope", broad.blocked_reasons)

    def test_13_3_ownership_zone_blocks_overlap_and_protected_lanes(self) -> None:
        result = validate_level_13_ownership_zone_dry_run(
            (
                self._zone("zone-1", ("docs/worker.md",)),
                self._zone("zone-2", ("docs/worker.md",)),
                self._zone("zone-3", ("src/app/coding/page.tsx",), lane="coding_ui_implementation_wiring"),
            )
        )

        self.assertFalse(result.valid_for_dry_run)
        self.assertIn("overlapping_ownership_zone:zone-2", result.blocked_reasons)
        self.assertIn("protected_lane_or_zone:zone-3", result.blocked_reasons)

    def test_13_4_conflict_detection_observes_without_resolving(self) -> None:
        packet = build_level_13_conflict_detection_dry_run_packet(
            workers=(self._worker(),),
            dirty_files=("docs/worker.md",),
            proposed_files=("docs/worker.md",),
        )

        self.assertEqual(packet.level, "13.4")
        self.assertTrue(packet.blocked)
        self.assertIn("active_worker_file_conflict", packet.blocked_reasons)
        self.assertIn("dirty_worktree_conflict_observed_only", packet.blocked_reasons)
        self.assertFalse(packet.would_write_files)
        self.assertFalse(packet.would_dispatch_worker)

    def test_13_5_handoff_packet_cannot_reassign_worker(self) -> None:
        packet = build_level_13_handoff_packet_dry_run(
            source_worker=self._worker(worker_id="worker-a"),
            target_worker=self._worker(worker_id="worker-b"),
            conflict_report_ref=None,
            unresolved_files=("docs/open.md",),
        )

        self.assertEqual(packet.level, "13.5")
        self.assertTrue(packet.blocked)
        self.assertIn("missing_conflict_report_ref", packet.blocked_reasons)
        self.assertIn("handoff_has_unresolved_files", packet.blocked_reasons)
        self.assertFalse(packet.would_reassign_worker)

    def test_13_6_branch_worktree_proposal_never_creates_branch_or_worktree(self) -> None:
        packet = build_level_13_branch_worktree_proposal_dry_run(
            worker=self._worker(),
            branch_name="worker/demo",
            worktree_path="../SpiritOS-worker-demo",
            existing_names=("worker/demo",),
            dirty_files=("docs/worker.md",),
        )

        self.assertEqual(packet.level, "13.6")
        self.assertTrue(packet.blocked)
        self.assertIn("branch_or_worktree_name_collision", packet.blocked_reasons)
        self.assertIn("dirty_worktree_blocks_branch_worktree_proposal", packet.blocked_reasons)
        self.assertFalse(packet.would_create_branch)
        self.assertFalse(packet.would_create_worktree)

    def test_13_7_worker_closeout_cannot_release_locks_automatically(self) -> None:
        packet = build_level_13_worker_closeout_packet_dry_run(
            worker=replace(self._worker(), status="stale"),
            verification_summary=None,
            conflicted=True,
        )

        self.assertEqual(packet.level, "13.7")
        self.assertTrue(packet.blocked)
        self.assertIn("missing_verification_summary", packet.blocked_reasons)
        self.assertIn("conflicted_worker_requires_review", packet.blocked_reasons)
        self.assertIn("stale_worker_cannot_close_cleanly", packet.blocked_reasons)
        self.assertFalse(packet.would_release_lease)
        self.assertFalse(packet.would_release_lock)

    def test_13_8_stale_worker_handling_requires_operator_review(self) -> None:
        packet = build_level_13_stale_worker_handling_dry_run(
            replace(self._worker(), status="stale")
        )

        self.assertEqual(packet.level, "13.8")
        self.assertTrue(packet.blocked)
        self.assertIn("operator_review_required_for_stale_worker", packet.blocked_reasons)
        self.assertFalse(packet.would_reassign_worker)
        self.assertFalse(packet.would_write_files)

    def test_13_9_closeout_keeps_level_14_human_gated(self) -> None:
        payload = build_level_13_closeout_level_14_access_check()

        self.assertEqual(payload["level"], "13.9")
        self.assertEqual(payload["level_14_access"], "requires_explicit_human_verification")
        self.assertFalse(payload["worker_dispatch_authority_granted"])
        self.assertFalse(payload["worker_orchestration_authority_granted"])
        self.assertFalse(payload["branch_worktree_authority_granted"])
        self.assertFalse(payload["write_authority_granted"])
        self.assertFalse(payload["local_execution_authority_granted"])
        self.assertFalse(payload["autonomy_granted"])

    def test_module_exposes_no_write_execution_branch_or_git_surface(self) -> None:
        source = inspect.getsource(level_13_worker_runtime)
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
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _worker(worker_id: str = "worker-13") -> CartographerLevel13WorkerRecord:
        return CartographerLevel13WorkerRecord(
            worker_id=worker_id,
            worker_type="codex_dry_run",
            owner="operator",
            task="review docs coordination",
            run_id="run-13",
            lane="cartographer_runtime_dry_run",
            allowed_files=("docs/worker.md",),
            forbidden_files=("src/**",),
            status="active",
            lease_id="lease-13",
            stale_after_seconds=600,
            closeout_ref=None,
        )

    @staticmethod
    def _lease() -> CartographerLevel13WorkerLease:
        return CartographerLevel13WorkerLease(
            lease_id="lease-13",
            worker_id="worker-13",
            run_id="run-13",
            lane="cartographer_runtime_dry_run",
            files=("docs/worker.md",),
            status="active",
            expires_at="2026-05-23T00:00:00Z",
            revoked=False,
        )

    @staticmethod
    def _zone(
        zone_id: str,
        files: tuple[str, ...],
        *,
        lane: str = "cartographer_runtime_dry_run",
    ) -> CartographerLevel13OwnershipZone:
        return CartographerLevel13OwnershipZone(
            zone_id=zone_id,
            owner_worker_id="worker-13",
            lane=lane,
            files=files,
            mode="dry_run",
            protected=False,
        )


if __name__ == "__main__":
    unittest.main()
