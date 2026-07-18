#!/usr/bin/env python3
"""Focused no-launch tests for the Foundation R1 lifecycle owner."""
from __future__ import annotations

import ast
import dataclasses
import importlib.util
import json
import os
import shutil
import socket
import ssl
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock


SCRIPT = Path(__file__).with_name("run-foundation-remediation-r1-lifecycle.py")


def load_script() -> ModuleType:
    name = "foundation_remediation_r1_lifecycle"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("lifecycle script could not be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LIFECYCLE = load_script()


def run(*command: str, cwd: Path) -> str:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


class TemporaryLinkedWorktree(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temporary.name).resolve()
        cls.repository = cls.base / "SpiritOS"
        cls.proof = cls.base / "proof"
        cls.repository.mkdir()
        run("git", "init", cwd=cls.repository)
        run("git", "config", "user.email", "lifecycle@example.invalid", cwd=cls.repository)
        run("git", "config", "user.name", "Lifecycle Test", cwd=cls.repository)
        files = {
            ".gitignore": (
                ".env.local\n"
                "tests/ui-agent-trials/fixtures/dummy-product-site/\n"
            ),
            "source_proxy/marker.py": "VALUE = 1\n",
            "source_proxy/api/decision.py": (
                "def _agent_debug_log(**values):\n"
                "    del values\n"
            ),
            "data/source-proxy/.gitkeep": "",
            "scripts/spiritflix-prod-https-proxy.mjs": (
                'const host = args.get("--host") ?? "127.0.0.1";\n'
                "server.listen(port, host, () => {});\n"
            ),
        }
        for relative, content in files.items():
            path = cls.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        run("git", "add", ".", cwd=cls.repository)
        run("git", "commit", "-m", "fixture", cwd=cls.repository)
        cls.head = run("git", "rev-parse", "HEAD", cwd=cls.repository)
        run(
            "git",
            "worktree",
            "add",
            "-b",
            "foundation-r1-proof",
            str(cls.proof),
            cls.head,
            cwd=cls.repository,
        )
        cls.task = cls.base / "task.txt"
        cls.task.write_text(
            "Implement the exact isolated Foundation R1 proving fixture.",
            encoding="utf-8",
        )
        cls.dependencies = cls.base / "dependencies"
        next_binary = cls.dependencies / "next" / "dist" / "bin" / "next"
        next_binary.parent.mkdir(parents=True)
        next_binary.write_text("next", encoding="utf-8")
        cls.certificate = cls.base / "certificate.pem"
        cls.private_key = cls.base / "private-key.pem"
        cls.certificate.write_text("certificate", encoding="utf-8")
        cls.private_key.write_text("private-key", encoding="utf-8")
        os.chmod(cls.private_key, 0o600)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            run(
                "git",
                "worktree",
                "remove",
                "--force",
                str(cls.proof),
                cwd=cls.repository,
            )
        finally:
            cls.temporary.cleanup()

    def config(self):
        return LIFECYCLE.LifecycleConfig(
            proof_worktree=self.proof,
            expected_source_head=self.head,
            expected_repository_id="SpiritOS",
            expected_worktree_id="b" * 24,
            expected_branch="foundation-r1-proof",
            proposal_id="proposal-foundation-r1",
            task_file=self.task,
            inner_receipt=self.base / "inner.json",
            output=self.base / "outer.json",
            python_executable=Path(sys.executable).absolute(),
            python_executable_resolved=Path(sys.executable).resolve(),
            expected_python_executable_sha256=LIFECYCLE._sha256_file(
                Path(sys.executable).resolve()
            ),
            expected_python_environment_sha256="c" * 64,
            node_executable=Path(sys.executable).absolute(),
            node_executable_resolved=Path(sys.executable).resolve(),
            expected_node_executable_sha256=LIFECYCLE._sha256_file(
                Path(sys.executable).resolve()
            ),
            node_modules_root=self.dependencies,
            expected_node_modules_sha256=LIFECYCLE._hash_directory(
                self.dependencies
            )[0],
            tls_certificate=self.certificate,
            tls_private_key=self.private_key,
            primary_model_alias=LIFECYCLE.R1_PRIMARY_MODEL_ALIAS,
            fallback_model_alias=LIFECYCLE.R1_CODER_ALIAS,
            expected_failed_provider=LIFECYCLE.R1_FAILED_PROVIDER,
            expected_failed_model=LIFECYCLE.R1_PRIMARY_MODEL_ALIAS,
            expected_fallback_provider=LIFECYCLE.R1_FALLBACK_PROVIDER,
            expected_fallback_model=LIFECYCLE.R1_FALLBACK_MODEL,
            source_port=0,
            next_port=0,
            https_port=0,
            startup_timeout_seconds=30,
            inner_http_timeout_seconds=30,
            inner_process_timeout_seconds=60,
        )

    def test_receipt_identity_uses_terminal_remediation_namespace(self) -> None:
        self.assertEqual(
            LIFECYCLE.REMEDIATION_ID,
            "spiritos-foundation-remediation-r1",
        )
        self.assertEqual(
            LIFECYCLE.LIFECYCLE_CLAIM_CEILING,
            "subordinate_clean_checkout_build_service_and_trusted_process_"
            "revocation_proof_only",
        )

    def test_outer_receipt_binds_the_full_inner_receipt(self) -> None:
        raw = {
            "schema_version": LIFECYCLE.INNER_RECEIPT_SCHEMA,
            "receipt_sha256": "sha256:" + "a" * 64,
            "runs": [{"task_id": "task-1"}, {"task_id": "task-2"}],
        }
        execution = {"receipt_sha256": raw["receipt_sha256"]}

        bound = LIFECYCLE._bind_full_inner_proving_receipt(raw, execution)
        embedded = dict(bound)
        self.assertEqual(embedded.pop("execution"), execution)
        self.assertIs(
            embedded.pop("published_only_after_lifecycle_teardown"),
            True,
        )
        self.assertEqual(embedded, raw)

    def cli(self) -> list[str]:
        config = self.config()
        return [
            "--proof-worktree",
            str(self.proof),
            "--expected-source-head",
            self.head,
            "--expected-repository-id",
            "SpiritOS",
            "--expected-worktree-id",
            config.expected_worktree_id,
            "--expected-branch",
            config.expected_branch,
            "--proposal-id",
            config.proposal_id,
            "--task-file",
            str(self.task),
            "--inner-receipt",
            str(config.inner_receipt),
            "--output",
            str(config.output),
            "--python-executable",
            sys.executable,
            "--expected-python-executable-sha256",
            config.expected_python_executable_sha256,
            "--expected-python-environment-sha256",
            config.expected_python_environment_sha256,
            "--node-executable",
            sys.executable,
            "--expected-node-executable-sha256",
            config.expected_node_executable_sha256,
            "--node-modules-root",
            str(self.dependencies),
            "--expected-node-modules-sha256",
            config.expected_node_modules_sha256,
            "--tls-certificate",
            str(self.certificate),
            "--tls-private-key",
            str(self.private_key),
            "--primary-model-alias",
            LIFECYCLE.R1_PRIMARY_MODEL_ALIAS,
            "--fallback-model-alias",
            LIFECYCLE.R1_CODER_ALIAS,
            "--expected-failed-provider",
            LIFECYCLE.R1_FAILED_PROVIDER,
            "--expected-failed-model",
            LIFECYCLE.R1_PRIMARY_MODEL_ALIAS,
            "--expected-fallback-provider",
            LIFECYCLE.R1_FALLBACK_PROVIDER,
            "--expected-fallback-model",
            LIFECYCLE.R1_FALLBACK_MODEL,
        ]

    def test_accepts_only_exact_clean_registered_linked_worktree(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PATH": "/untrusted/bin",
                "GIT_DIR": "/untrusted/git-dir",
                "GIT_INDEX_FILE": "/untrusted/index",
                "GIT_WORK_TREE": "/untrusted/worktree",
            },
        ):
            identity = LIFECYCLE._verify_clean_linked_worktree(self.config())
        self.assertEqual(identity.root, self.proof)
        self.assertEqual(identity.source_head, self.head)
        self.assertEqual(identity.repository_id, "SpiritOS")

        for field, value, reason in (
            ("expected_source_head", "a" * 40, "lifecycle_source_head_mismatch"),
            ("expected_branch", "wrong-branch", "lifecycle_branch_mismatch"),
            ("expected_repository_id", "Wrong", "lifecycle_repository_identity_mismatch"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(LIFECYCLE.LifecycleError, reason):
                    LIFECYCLE._verify_clean_linked_worktree(
                        dataclasses.replace(self.config(), **{field: value})
                    )

        dirty = self.proof / "dirty.txt"
        dirty.write_text("dirty", encoding="utf-8")
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_proof_worktree_not_clean",
            ):
                LIFECYCLE._verify_clean_linked_worktree(self.config())
        finally:
            dirty.unlink()

        ignored = self.proof / ".env.local"
        ignored.write_text("UNTRUSTED=value\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_proof_worktree_contains_ignored_files",
            ):
                LIFECYCLE._verify_clean_linked_worktree(self.config())
        finally:
            ignored.unlink()

        hidden = self.proof / "source_proxy" / "marker.py"
        run("git", "update-index", "--assume-unchanged", str(hidden), cwd=self.proof)
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_index_visibility_flag_forbidden",
            ):
                LIFECYCLE._verify_clean_linked_worktree(self.config())
        finally:
            run(
                "git",
                "update-index",
                "--no-assume-unchanged",
                str(hidden),
                cwd=self.proof,
            )

    def test_parser_requires_exact_profile_and_private_tls_key(self) -> None:
        parsed = LIFECYCLE._parse_config(self.cli())
        self.assertEqual(parsed.expected_source_head, self.head)
        self.assertEqual(parsed.expected_worktree_id, "b" * 24)

        wrong_profile = self.cli()
        index = wrong_profile.index("--expected-fallback-model") + 1
        wrong_profile[index] = "another/model"
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_model_identity_profile_mismatch",
        ):
            LIFECYCLE._parse_config(wrong_profile)

        os.chmod(self.private_key, 0o644)
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_tls_private_key_mode_invalid",
            ):
                LIFECYCLE._parse_config(self.cli())
        finally:
            os.chmod(self.private_key, 0o600)

    def test_runtime_executable_target_and_content_are_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "runtime-first"
            second = root / "runtime-second"
            link = root / "runtime-link"
            first.write_bytes(b"first-runtime")
            second.write_bytes(b"second-runtime")
            os.chmod(first, 0o700)
            os.chmod(second, 0o700)
            link.symlink_to(first)
            config = dataclasses.replace(
                self.config(),
                python_executable=link,
                python_executable_resolved=first.resolve(),
                expected_python_executable_sha256=LIFECYCLE._sha256_file(first),
                node_executable=first,
                node_executable_resolved=first.resolve(),
                expected_node_executable_sha256=LIFECYCLE._sha256_file(first),
            )
            LIFECYCLE._verify_python_executable(config)
            LIFECYCLE._verify_node_executable(config)
            link.unlink()
            link.symlink_to(second)
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_python_executable_identity_mismatch",
            ):
                LIFECYCLE._verify_python_executable(config)
            first.write_bytes(b"mutated-runtime")
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_node_executable_identity_mismatch",
            ):
                LIFECYCLE._verify_node_executable(config)

    def test_runtime_environment_isolates_authority_and_build_hides_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            with mock.patch.dict(
                os.environ,
                {
                    "NODE_OPTIONS": "--require=/untrusted/injection.js",
                    "GIT_INDEX_FILE": "/untrusted/index",
                    "PYTHONPATH": "/untrusted/python",
                    "SOURCE_PROXY_UNRELATED_STATE": "/untrusted/state",
                },
            ):
                environment = LIFECYCLE._runtime_environment(
                    self.config(),
                    state_root=state,
                    source_port=18787,
                    next_port=13080,
                    https_port=13443,
                    operator_secret="operator-secret-value",
                )
            for key in (
                "SPIRITOS_APPROVAL_STATE_DIR",
                "SOURCE_PROXY_LONG_RUNNING_TASKS_DB",
                "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG",
                "SOURCE_PROXY_BLOCKED_ACTION_AUDIT_LOG",
                "SOURCE_PROXY_CARTOGRAPHER_GIT_APPROVAL_LOG",
                "SOURCE_PROXY_GATE_STATE_PATH",
                "SOURCE_PROXY_FIP0_RECEIPT_DIR",
                "SOURCE_PROXY_DATA_DIR",
                "SPIRITOS_OPERATOR_E2E_STATE_PATH",
            ):
                Path(environment[key]).resolve().relative_to(state.resolve())
            self.assertEqual(
                environment["SPIRITOS_E2E_FRONTEND_ORIGIN"],
                "https://127.0.0.1:13443",
            )
            self.assertEqual(environment["SOURCE_PROXY_DATABASE_URL"], "disabled")
            self.assertEqual(environment["PYTHONPATH"], str(self.proof))
            self.assertEqual(environment["PATH"], LIFECYCLE.SAFE_PATH)
            self.assertNotIn("NODE_OPTIONS", environment)
            self.assertNotIn("GIT_INDEX_FILE", environment)
            self.assertNotIn("SOURCE_PROXY_UNRELATED_STATE", environment)
            self.assertEqual(environment["SOURCE_PROXY_GATE_INCREMENT"], "1.3")
            gate = json.loads((state / "gate.json").read_text(encoding="utf-8"))
            self.assertEqual(gate["status"], "APPROVED_INCREMENT")
            self.assertEqual(gate["approved_increment"], "1.3")

            build = LIFECYCLE._build_environment(environment)
            self.assertNotIn("SPIRITOS_OPERATOR_CREDENTIAL", build)
            self.assertNotIn("SPIRITOS_OPERATOR_E2E_SECRET", build)
            self.assertNotIn("operator-secret-value", json.dumps(build))

            service = LIFECYCLE._scoped_runtime_environment(
                environment,
                operator_credential=False,
                operator_e2e_secret=True,
            )
            self.assertNotIn("SPIRITOS_OPERATOR_CREDENTIAL", service)
            self.assertEqual(
                service["SPIRITOS_OPERATOR_E2E_SECRET"],
                "operator-secret-value",
            )
            inner = LIFECYCLE._scoped_runtime_environment(
                environment,
                operator_credential=True,
                operator_e2e_secret=False,
            )
            self.assertEqual(
                inner["SPIRITOS_OPERATOR_CREDENTIAL"],
                "operator-secret-value",
            )
            self.assertNotIn("SPIRITOS_OPERATOR_E2E_SECRET", inner)

    def test_build_rejects_unexpected_dependency_tree_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            (state / "logs").mkdir()
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_node_modules_identity_mismatch",
            ):
                LIFECYCLE._build_next(
                    dataclasses.replace(
                        self.config(),
                        expected_node_modules_sha256="a" * 64,
                    ),
                    environment={},
                    state_root=state,
                )

    def test_dependency_hash_rejects_symlinks_escaping_the_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "dependencies"
            root.mkdir()
            external = base / "external.js"
            external.write_text("first", encoding="utf-8")
            (root / "escape.js").symlink_to(external)
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_directory_symlink_escapes_root",
            ):
                LIFECYCLE._hash_directory(root)

    def test_runtime_cleanup_preserves_tracked_baseline(self) -> None:
        tracked = self.proof / "data" / "source-proxy" / ".gitkeep"
        runtime = tracked.parent / "runtime-receipt.json"
        nested = tracked.parent / "nested" / "state.json"
        nested.parent.mkdir()
        runtime.write_text("runtime", encoding="utf-8")
        nested.write_text("state", encoding="utf-8")
        LIFECYCLE._clean_data_source_proxy(self.proof)
        self.assertTrue(tracked.is_file())
        self.assertFalse(runtime.exists())
        self.assertFalse(nested.exists())
        self.assertFalse(nested.parent.exists())

    def test_runtime_cleanup_removes_only_the_owned_ignored_proving_fixture(self) -> None:
        config = self.config()
        identity = LIFECYCLE._verify_clean_linked_worktree(config)
        fixture = self.proof / LIFECYCLE.PROVING_FIXTURE_RELATIVE
        sentinel = self.base / "proving-fixture-external-sentinel.txt"
        sentinel.write_text("must survive cleanup\n", encoding="utf-8")
        (fixture / "src").mkdir(parents=True)
        (fixture / "package.json").write_text("{}\n", encoding="utf-8")
        (fixture / "src" / "external-sentinel-link").symlink_to(sentinel)

        try:
            cleanup = LIFECYCLE._cleanup_worktree_runtime(
                identity,
                config=config,
                dependency_link=None,
            )
            self.assertFalse(fixture.exists())
            self.assertFalse(fixture.is_symlink())
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"),
                "must survive cleanup\n",
            )
            self.assertTrue(cleanup["proving_fixture_removed"])
            self.assertTrue(cleanup["proving_fixture_was_present"])
            self.assertTrue(cleanup["proving_fixture_tracked_paths_absent"])
            self.assertTrue(cleanup["proving_fixture_symlinks_not_followed"])
            self.assertEqual(
                LIFECYCLE._verify_clean_linked_worktree(config),
                identity,
            )
        finally:
            if fixture.exists() or fixture.is_symlink():
                if fixture.is_symlink():
                    fixture.unlink()
                else:
                    shutil.rmtree(fixture)
            sentinel.unlink(missing_ok=True)

    def test_owned_proving_fixture_cleanup_refuses_tracked_paths(self) -> None:
        fixture = self.proof / LIFECYCLE.PROVING_FIXTURE_RELATIVE
        tracked = fixture / "tracked.txt"
        tracked.parent.mkdir(parents=True)
        tracked.write_text("preserve\n", encoding="utf-8")
        relative = tracked.relative_to(self.proof).as_posix()

        try:
            with (
                mock.patch.object(LIFECYCLE, "_git", return_value=f"{relative}\0"),
                self.assertRaisesRegex(
                    LIFECYCLE.LifecycleError,
                    "lifecycle_proving_fixture_contains_tracked_paths",
                ),
            ):
                LIFECYCLE._remove_owned_proving_fixture(self.proof)
            self.assertEqual(tracked.read_text(encoding="utf-8"), "preserve\n")
        finally:
            shutil.rmtree(fixture)

    def test_runtime_cleanup_revalidates_the_complete_worktree_identity(self) -> None:
        config = self.config()
        identity = LIFECYCLE._verify_clean_linked_worktree(config)
        changed = dataclasses.replace(identity, branch="substituted-after-run")
        with (
            mock.patch.object(
                LIFECYCLE,
                "_verify_clean_linked_worktree",
                return_value=changed,
            ),
            self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_worktree_identity_changed_during_proving",
            ),
        ):
            LIFECYCLE._cleanup_worktree_runtime(
                identity,
                config=config,
                dependency_link=None,
            )

    def test_source_guards_require_retired_debug_writer_and_loopback_proxy(self) -> None:
        LIFECYCLE._verify_external_debug_writer_retired(self.proof)
        LIFECYCLE._verify_loopback_tls_proxy_contract(self.proof)
        decision = self.proof / "source_proxy" / "api" / "decision.py"
        original = decision.read_text(encoding="utf-8")
        decision.write_text(original + '\n_DEBUG_LOG_PATH = "debug-9460b9.log"\n', encoding="utf-8")
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_external_debug_writer_not_retired",
            ):
                LIFECYCLE._verify_external_debug_writer_retired(self.proof)
        finally:
            decision.write_text(original, encoding="utf-8")

    def test_https_health_pins_the_exact_leaf_as_a_partial_chain(self) -> None:
        context = SimpleNamespace(verify_flags=0)

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return b'{"status":"unauthenticated"}'

        opener = SimpleNamespace(open=lambda *_args, **_kwargs: Response())
        service = SimpleNamespace(
            name="next_tls",
            port=443,
            process=SimpleNamespace(poll=lambda: None),
            health_response_sha256="",
        )
        with (
            mock.patch("ssl.create_default_context", return_value=context),
            mock.patch.object(
                LIFECYCLE.urllib.request,
                "build_opener",
                return_value=opener,
            ),
        ):
            payload = LIFECYCLE._wait_for_json_health(
                service,
                path="/v1/operator/session",
                timeout_seconds=1,
                scheme="https",
                ca_file=self.certificate,
            )

        self.assertEqual(payload, {"status": "unauthenticated"})
        self.assertTrue(context.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN)

    def test_state_root_is_removed_when_runtime_setup_fails(self) -> None:
        created: list[Path] = []
        original_new_state_root = LIFECYCLE._new_state_root

        def capture_state_root() -> Path:
            root = original_new_state_root()
            created.append(root)
            return root

        with (
            mock.patch.object(
                LIFECYCLE,
                "_approval_secret_baseline",
                return_value=("a" * 64, (1, 2, 3, 4)),
            ),
            mock.patch.object(
                LIFECYCLE,
                "_verify_approval_secret_unchanged",
                return_value=None,
            ),
            mock.patch.object(
                LIFECYCLE,
                "_new_state_root",
                side_effect=capture_state_root,
            ),
            mock.patch.object(
                LIFECYCLE,
                "_runtime_environment",
                side_effect=OSError("synthetic setup failure"),
            ),
        ):
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_internal_error",
            ):
                LIFECYCLE._run_lifecycle(self.config())
        self.assertEqual(len(created), 1)
        self.assertFalse(created[0].exists())

    def test_inner_terminal_receipt_is_not_published_when_teardown_fails(self) -> None:
        config = self.config()
        for path in (config.inner_receipt, config.output):
            if path.exists():
                path.unlink()
        fake_services = [
            SimpleNamespace(name=name) for name in ("source_proxy", "next", "next_tls")
        ]
        source_health = {
            "service": "source-proxy",
            "manifest_version": "2.7A-1",
            "configured_roots": [{"path": str(self.proof)}],
            "repo_metadata": {
                "root": str(self.proof),
                "git_directory_present": True,
            },
        }
        with (
            mock.patch.object(
                LIFECYCLE,
                "_approval_secret_baseline",
                return_value=("a" * 64, (1, 2, 3, 4)),
            ),
            mock.patch.object(
                LIFECYCLE,
                "_verify_approval_secret_unchanged",
                return_value=None,
            ),
            mock.patch.object(LIFECYCLE, "_approval_preflight", return_value={}),
            mock.patch.object(
                LIFECYCLE,
                "_python_environment_sha256",
                return_value="b" * 64,
            ),
            mock.patch.object(
                LIFECYCLE,
                "_python_site_packages_identity",
                return_value=("c" * 64, 1),
            ),
            mock.patch.object(LIFECYCLE, "_prepare_dependency_link", return_value=None),
            mock.patch.object(LIFECYCLE, "_build_next", return_value={}),
            mock.patch.object(
                LIFECYCLE,
                "_launch_service",
                side_effect=fake_services,
            ),
            mock.patch.object(
                LIFECYCLE,
                "_wait_for_json_health",
                side_effect=[
                    source_health,
                    {"status": "unauthenticated"},
                    {"status": "unauthenticated"},
                ],
            ),
            mock.patch.object(LIFECYCLE, "_require_process_cwd", return_value=None),
            mock.patch.object(LIFECYCLE, "_require_loopback_listener", return_value=None),
            mock.patch.object(
                LIFECYCLE,
                "_run_inner_client",
                return_value=({}, {}, {"terminal_proof_eligible": True}),
            ),
            mock.patch.object(
                LIFECYCLE,
                "_stop_service",
                side_effect=[
                    LIFECYCLE.LifecycleError("synthetic_teardown_failure"),
                    None,
                    None,
                ],
            ),
        ):
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_teardown_failed",
            ):
                LIFECYCLE._run_lifecycle(config)
        self.assertFalse(config.inner_receipt.exists())
        self.assertFalse(config.output.exists())

    def test_inner_receipt_is_bound_to_preflight_identity_and_https(self) -> None:
        config = self.config()
        unsigned = {
            "schema_version": LIFECYCLE.INNER_RECEIPT_SCHEMA,
            "receipt_type": "foundation_r1_black_box_production_proving",
            "remediation_id": LIFECYCLE.REMEDIATION_ID,
            "run_mode": "production_http",
            "source_commit": self.head,
            "terminal_proof_eligible": True,
            "claim_ceiling": "recovered_via_declared_fallback_only",
            "failures": [],
            "repository_identity": {
                "repository": "SpiritOS",
                "worktree": str(self.proof),
                "root": str(self.proof),
            },
            "expected_runtime_identity": {
                "source_head": self.head,
                "repository_id": "SpiritOS",
                "worktree_id": config.expected_worktree_id,
                "worktree_id_source": "approval_preflight.stateNamespace",
            },
            "target_plugin_identity": {
                "repository_id": "SpiritOS",
                "worktree_id": config.expected_worktree_id,
                "state_namespace": config.expected_worktree_id,
                "workspace_root": str(self.proof),
                "source_head": self.head,
            },
            "transport": {
                "kind": "production_http",
                "source_origin": "http://127.0.0.1:18787",
                "next_origin": "https://127.0.0.1:13443",
                "redirects_allowed": False,
                "services_started_by_harness": False,
                "application_modules_imported": False,
                "test_modules_imported": False,
            },
            "operator_session": {"authenticated": True, "revoked": True},
            "redaction": {"status": "passed"},
            "run_attestation": {
                "schema_version": "spiritos-production-http-run-attestation/v1",
                "transcript_sha256": "sha256:" + "a" * 64,
                "binding_sha256": "sha256:" + "b" * 64,
                "exchange_count": 27,
                "client_verified": True,
            },
            "http_exchanges": [
                {"ordinal": ordinal} for ordinal in range(1, 28)
            ],
            "runs": [
                {"task_id": "task-1", "orchestrator_run_id": "run-1"},
                {"task_id": "task-2", "orchestrator_run_id": "run-2"},
            ],
            "clean_rerun": {
                "completed": True,
                "source_commit_unchanged": True,
                "source_baseline_verified": True,
                "fixture_absent_before_each_run": True,
                "reset_was_idempotent_after_undo": True,
                "repository_identity_unchanged": True,
                "task_id_distinct": True,
                "run_id_distinct": True,
                "approval_id_distinct": True,
                "artifact_identity_distinct": True,
            },
        }
        receipt = {**unsigned, "receipt_sha256": LIFECYCLE._sha256_json(unsigned)}
        summary = LIFECYCLE._validate_inner_receipt(
            receipt,
            config,
            source_port=18787,
            next_port=13080,
            https_port=13443,
        )
        self.assertTrue(summary["terminal_proof_eligible"])

        tampered = dict(unsigned)
        tampered["source_commit"] = "a" * 40
        tampered["receipt_sha256"] = LIFECYCLE._sha256_json(tampered)
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_inner_receipt_source_commit_mismatch",
        ):
            LIFECYCLE._validate_inner_receipt(
                tampered,
                config,
                source_port=18787,
                next_port=13080,
                https_port=13443,
            )

        short_transcript = json.loads(json.dumps(unsigned))
        short_transcript["http_exchanges"].pop()
        short_transcript["run_attestation"]["exchange_count"] = 26
        short_transcript["receipt_sha256"] = LIFECYCLE._sha256_json(
            short_transcript
        )
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_inner_run_attestation_invalid",
        ):
            LIFECYCLE._validate_inner_receipt(
                short_transcript,
                config,
                source_port=18787,
                next_port=13080,
                https_port=13443,
            )


class StateAndReceiptTests(unittest.TestCase):
    def test_listener_identity_is_owned_by_the_expected_process_session(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind((LIFECYCLE.LOOPBACK, 0))
            listener.listen()
            service = SimpleNamespace(
                name="unit_listener",
                port=listener.getsockname()[1],
                process=SimpleNamespace(pid=os.getsid(0)),
                cgroup_path=Path("/unused-unit-cgroup"),
                loopback_bound=False,
                listener_identity_sha256="",
            )
            with mock.patch.object(
                LIFECYCLE,
                "_cgroup_process_ids",
                return_value={os.getpid()},
            ):
                LIFECYCLE._require_loopback_listener(service)
            self.assertTrue(service.loopback_bound)
            self.assertTrue(service.listener_identity_sha256)

            wrong_owner = SimpleNamespace(
                name="wrong_owner",
                port=listener.getsockname()[1],
                process=SimpleNamespace(pid=os.getpid()),
                cgroup_path=Path("/unused-wrong-cgroup"),
                loopback_bound=False,
                listener_identity_sha256="",
            )
            other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
            try:
                with (
                    mock.patch.object(
                        LIFECYCLE,
                        "_cgroup_process_ids",
                        return_value={other.pid},
                    ),
                    self.assertRaisesRegex(
                        LIFECYCLE.LifecycleError,
                        "lifecycle_wrong_owner_listener_not_process_owned",
                    ),
                ):
                    LIFECYCLE._require_loopback_listener(wrong_owner)
            finally:
                other.terminate()
                other.wait(timeout=5)

    def test_logged_command_timeout_revokes_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_pid_path = root / "child.pid"
            code = "\n".join(
                (
                    "import os, pathlib, subprocess, sys, time",
                    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)",
                    f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid))",
                    "time.sleep(60)",
                )
            )
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_test_timeout",
            ):
                LIFECYCLE._run_logged(
                    [sys.executable, "-c", code],
                    cwd=root,
                    environment=os.environ,
                    stdout_path=root / "stdout.log",
                    stderr_path=root / "stderr.log",
                    timeout_seconds=1,
                    reason="lifecycle_test_timeout",
                )
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            self.assertFalse(Path(f"/proc/{child_pid}").exists())

    def test_logged_command_rejects_and_revokes_reparented_success_path_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_pid_path = root / "child.pid"
            code = "\n".join(
                (
                    "import pathlib, subprocess, sys",
                    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)",
                    f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid))",
                )
            )
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_success_path_child_process_leak",
            ):
                LIFECYCLE._run_logged(
                    [sys.executable, "-c", code],
                    cwd=root,
                    environment=os.environ,
                    stdout_path=root / "stdout.log",
                    stderr_path=root / "stderr.log",
                    timeout_seconds=20,
                    reason="lifecycle_success_path",
                )
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            self.assertFalse(Path(f"/proc/{child_pid}").exists())

    def test_service_teardown_revokes_a_reparented_detached_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root = Path(temporary)
            (state_root / "logs").mkdir()
            child_pid_path = state_root / "child.pid"
            code = "\n".join(
                (
                    "import pathlib, subprocess, sys",
                    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)",
                    f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid))",
                )
            )
            port = LIFECYCLE._allocate_port(0, excluded=set())
            with (
                mock.patch.object(LIFECYCLE, "_verify_python_executable"),
                mock.patch.object(LIFECYCLE, "_verify_node_executable"),
            ):
                service = LIFECYCLE._launch_service(
                    name="detached_child_test",
                    command=[sys.executable, "-c", code],
                    config=SimpleNamespace(proof_worktree=state_root),
                    environment=os.environ,
                    port=port,
                    state_root=state_root,
                )
            service.process.wait(timeout=20)
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            self.assertTrue(Path(f"/proc/{child_pid}").exists())
            LIFECYCLE._stop_service(service, environment=os.environ)
            self.assertTrue(service.cgroup_empty)
            self.assertTrue(service.descendant_processes_absent)
            self.assertFalse(Path(f"/proc/{child_pid}").exists())

    def test_approval_state_must_have_only_retired_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "approvals.sqlite3"
            database = sqlite3.connect(path)
            database.execute("CREATE TABLE approval_records_v3 (state TEXT NOT NULL)")
            database.execute("CREATE TABLE approval_previews_v3 (state TEXT NOT NULL)")
            database.executemany(
                "INSERT INTO approval_records_v3 VALUES (?)",
                [("consumed",)] * 4,
            )
            database.executemany(
                "INSERT INTO approval_previews_v3 VALUES (?)",
                [("approved",)] * 4,
            )
            database.commit()
            database.close()
            summary = LIFECYCLE._approval_state_summary(path)
            self.assertEqual(summary["active_approval_count"], 0)
            database = sqlite3.connect(path)
            database.execute(
                "UPDATE approval_records_v3 SET state='approved' WHERE rowid=1"
            )
            database.commit()
            database.close()
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_temporary_approval_authority_still_active",
            ):
                LIFECYCLE._approval_state_summary(path)
            database = sqlite3.connect(path)
            database.execute("UPDATE approval_records_v3 SET state='consumed'")
            database.execute(
                "UPDATE approval_previews_v3 SET state='unknown-pending' WHERE rowid=1"
            )
            database.commit()
            database.close()
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_temporary_approval_authority_still_active",
            ):
                LIFECYCLE._approval_state_summary(path)

    def test_operator_state_requires_every_session_revoked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sessions.json"
            payload = {
                "sessions": {
                    "session-1": {"revoked_at": "2026-07-17T00:00:00+00:00"}
                }
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            summary = LIFECYCLE._operator_state_summary(path)
            self.assertTrue(summary["all_sessions_revoked"])
            payload["sessions"]["session-2"] = {}
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_operator_session_state_not_revoked",
            ):
                LIFECYCLE._operator_state_summary(path)
            target = Path(temporary) / "target.json"
            target.write_text(json.dumps(payload), encoding="utf-8")
            path.unlink()
            path.symlink_to(target)
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_operator_state_invalid",
            ):
                LIFECYCLE._operator_state_summary(path)

    def test_owned_state_root_is_deleted_and_unowned_root_is_rejected(self) -> None:
        owned = LIFECYCLE._new_state_root()
        LIFECYCLE._remove_state_root(owned)
        self.assertFalse(owned.exists())

        unowned = Path(tempfile.mkdtemp(prefix=LIFECYCLE.STATE_PREFIX)).resolve()
        (unowned / ".foundation-r1-owned").write_text("wrong\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_state_cleanup_marker_missing",
            ):
                LIFECYCLE._remove_state_root(unowned)
        finally:
            shutil.rmtree(unowned)

    def test_receipt_redaction_allows_explicit_safety_declarations_only(self) -> None:
        safe = {
            "credential_recorded": False,
            "session_token_recorded": False,
            "cookie_jar_cleared": True,
            "value": "safe",
        }
        LIFECYCLE._assert_redacted(safe, forbidden_values=["not-present-value"])
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_receipt_forbidden_key_present",
        ):
            LIFECYCLE._assert_redacted(
                {"cookie_jar_cleared": False},
                forbidden_values=[],
            )
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_receipt_forbidden_key_present",
        ):
            LIFECYCLE._assert_redacted(
                {"credential": "value"},
                forbidden_values=[],
            )
        with self.assertRaisesRegex(
            LIFECYCLE.LifecycleError,
            "lifecycle_receipt_sensitive_value_present",
        ):
            LIFECYCLE._assert_redacted(
                {"value": "not-present-value"},
                forbidden_values=["not-present-value"],
            )

    def test_receipt_creation_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt.json"
            LIFECYCLE._write_new_receipt(output, {"terminal_proof_eligible": False})
            with self.assertRaisesRegex(
                LIFECYCLE.LifecycleError,
                "lifecycle_receipt_output_exists",
            ):
                LIFECYCLE._write_new_receipt(output, {"replacement": True})

    def test_launcher_is_app_and_test_module_independent(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    self.assertNotEqual(keyword.arg, "shell")
        self.assertFalse(
            [
                name
                for name in imported
                if name.startswith(("source_proxy", "src", "tests"))
            ]
        )
        self.assertNotIn("0.0.0.0", source)
        self.assertIn('"terminal_proof_eligible": False', source)
        self.assertEqual(
            LIFECYCLE.INNER_IDENTITY_FLAGS,
            {
                "--expected-source-head",
                "--expected-repository-id",
                "--expected-worktree-id",
            },
        )


if __name__ == "__main__":
    unittest.main()
