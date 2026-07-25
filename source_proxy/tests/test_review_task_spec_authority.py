from __future__ import annotations

import hashlib
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from source_proxy.planning.plan import (
    PLAN_SCHEMA_VERSION,
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    PlanBudget,
    TargetFile,
    TaskClassification,
    VerificationPlan,
    bind_requested_artifacts_to_plan,
    fixed_literal_callable_shape_check,
    fixed_literal_zero_arg_callable_names,
    optional_integer_callable_contract,
    optional_integer_callable_shape_check,
    review_intent_paths_from_plan,
    review_task_spec_from_plan,
    task_spec_from_plan,
    task_requests_shared_helper_artifact,
    task_requests_test_artifact,
    validate_task_spec_for_plan,
)


PRIMARY = "src/app.py"
SECONDARY = "tests/test_app.py"


def _optional_integer_task() -> str:
    return (
        "Add pagination to `list_records` with optional `offset` and `limit` "
        "arguments. Defaults should still return all records, both values "
        "must be non-negative integers (with `limit` at least 1 when "
        "provided), and the function must never mutate the module's stored "
        "records. Raise `ValueError` for invalid pagination values."
    )


def _snapshot(path: str, content: str, *, exists: bool = True) -> dict[str, object]:
    return {
        "schema_version": "coding.review-artifact-snapshot/v1",
        "path": path,
        "exists": exists,
        "content": content if exists else "",
        "content_sha256": hashlib.sha256(
            (content if exists else "").encode("utf-8")
        ).hexdigest(),
    }


def _plan(
    source_task: str,
    *,
    acceptance_criteria: list[AcceptanceCriterion] | None = None,
    target: str = PRIMARY,
) -> ArchitectPlan:
    return ArchitectPlan(
        plan_id="plan-review-authority",
        task_id="task-review-authority",
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-07-22T00:00:00Z",
        source_task=source_task,
        bundle_snapshot=BundleSnapshot(
            bundle_path="/workspace/repomix-output.xml",
            bundle_sha256="0" * 64,
            workspace_root="/workspace",
            generated_at="2026-07-22T00:00:00Z",
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="small",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=target,
                exists=True,
                sha256_before="1" * 64,
            ),
            operation="edit",
            acceptance_criteria=acceptance_criteria or [],
            constraints=ContentConstraints(
                must_contain=[],
                must_not_contain=[],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=None,
                max_removed_lines=None,
            ),
            context_slices=[],
            forbidden_paths=[],
            style_directives=[],
        ),
        verification_plan=VerificationPlan(
            required_checks=[],
            designer_review_required=False,
            architect_review_required=True,
        ),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=300,
            cloud_escalation_allowed=False,
        ),
    )


def _tracked_test_candidate_plan(
    tmp_path: Path,
    *,
    target: str,
    test_path: str,
    test_content: str,
    forbidden_paths: tuple[str, ...] = (),
) -> tuple[Path, ArchitectPlan]:
    root = tmp_path / "workspace"
    target_file = root / target
    test_file = root / test_path
    target_file.parent.mkdir(parents=True)
    test_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(
        (
            "def existing() -> bool:\n    return True\n"
            if target.endswith(".py")
            else "export const value = 1;\n"
        ),
        encoding="utf-8",
    )
    test_file.write_text(test_content, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "add", "--", target, test_path],
        cwd=root,
        check=True,
    )
    plan = _plan(
        f"Target file: {target}\n"
        "Add focused tests for the updated module while preserving behavior.",
        target=target,
    )
    return root, replace(
        plan,
        bundle_snapshot=BundleSnapshot(
            bundle_path="",
            bundle_sha256="",
            workspace_root=str(root.resolve()),
            generated_at="2026-07-22T00:00:00Z",
        ),
        coder_packet=replace(
            plan.coder_packet,
            forbidden_paths=list(forbidden_paths),
        ),
    )


def test_coarse_scope_does_not_authorize_unrequested_secondary_file() -> None:
    plan = _plan("Target file: src/app.py\nUpdate the greeting.")

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, "src/model_selected_decoy.py"],
            authorized_paths=["src/"],
        )


def test_exact_server_authority_can_bind_create_bundle_before_review() -> None:
    extra = "src/bootstrap.py"
    plan = _plan("Target file: src/app.py\nCreate the requested starter bundle.")

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, extra],
        authorized_paths=[PRIMARY, extra],
    )

    assert spec.task_type == "create_file_bundle"
    assert spec.target == PRIMARY
    assert spec.allowed_files == [PRIMARY, extra]


def test_exact_server_authority_still_rejects_unlisted_artifact() -> None:
    plan = _plan("Target file: src/app.py\nCreate the requested starter bundle.")

    with pytest.raises(ValueError, match="review_task_spec_missing_primary_target"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, "src/model_selected_extra.py"],
            authorized_paths=[PRIMARY],
        )


def test_forbidden_path_cannot_become_canonical_allowed_authority() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Update file tests/test_app.py with focused tests for the new function."
    )
    plan = replace(
        plan,
        coder_packet=replace(
            plan.coder_packet,
            forbidden_paths=["tests/"],
        ),
    )

    spec = task_spec_from_plan(plan)
    tampered = replace(
        spec,
        allowed_files=[PRIMARY, SECONDARY],
        task_type="create_file_bundle",
    )

    assert spec.allowed_files == [PRIMARY]
    assert validate_task_spec_for_plan(spec, plan) == []
    assert validate_task_spec_for_plan(tampered, plan) == [
        "allowed_files",
        "allowed_files_forbidden",
        "task_type",
    ]


def test_plan_task_spec_validator_rejects_noncanonical_allowed_file_shape() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Update file tests/test_app.py with focused tests for the new function."
    )
    spec = task_spec_from_plan(plan)
    tampered = replace(
        spec,
        allowed_files=[SECONDARY, PRIMARY, SECONDARY],
    )

    errors = validate_task_spec_for_plan(tampered, plan)

    assert "target_first" in errors
    assert "allowed_files_deduplicated" in errors
    assert "allowed_files" in errors


def test_explicit_task_bound_secondary_file_remains_authorized() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Add the greeting behavior and focused tests. "
        'File "tests/test_app.py" must contain "test_greeting".'
    )

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, SECONDARY],
        authorized_paths=["src/", "tests/"],
    )

    assert spec.task_type == "create_file_bundle"
    assert spec.allowed_files == [PRIMARY, SECONDARY]
    assert review_intent_paths_from_plan(plan) == [PRIMARY, SECONDARY]


def test_deterministic_acceptance_criterion_can_bind_unquoted_secondary_file() -> None:
    plan = _plan(
        "Target file: src/app.py\nAdd the greeting behavior and focused tests.",
        acceptance_criteria=[
            AcceptanceCriterion(
                id="secondary-test",
                description=(
                    'File tests/test_app.py must contain "test_greeting".'
                ),
                kind="literal",
            )
        ],
    )

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, SECONDARY],
        authorized_paths=["src/", "tests/"],
    )

    assert spec.allowed_files == [PRIMARY, SECONDARY]
    assert spec == task_spec_from_plan(plan)
    assert validate_task_spec_for_plan(spec, plan) == []


def test_implicit_focused_test_request_does_not_fabricate_write_authority() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Add a small greeting function and add focused tests for the new function."
    )

    assert task_spec_from_plan(plan).allowed_files == [PRIMARY]
    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, SECONDARY],
            authorized_paths=["src/", "tests/"],
            artifact_snapshots={
                PRIMARY: _snapshot(PRIMARY, "def existing():\n    return True\n"),
                SECONDARY: _snapshot(SECONDARY, "", exists=False),
            },
        )


def test_unique_tracked_bound_test_is_persisted_as_exact_predispatch_authority(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / PRIMARY).write_text(
        "def existing() -> bool:\n    return True\n",
        encoding="utf-8",
    )
    (root / SECONDARY).write_text(
        "from src.app import existing\n\n"
        "def test_existing():\n"
        "    assert existing()\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", PRIMARY, SECONDARY], cwd=root, check=True)
    plan = replace(
        _plan(
            "Please add a small greeting function to src/app.py. "
            "Keep existing behavior and add focused tests for the new function."
        ),
        bundle_snapshot=BundleSnapshot(
            bundle_path="",
            bundle_sha256="",
            workspace_root=str(root.resolve()),
            generated_at="2026-07-22T00:00:00Z",
        ),
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )
    restored = ArchitectPlan.from_dict(bound.to_dict())
    spec = task_spec_from_plan(restored)

    assert spec.allowed_files == [PRIMARY, SECONDARY]
    assert spec.task_type == "create_file_bundle"
    assert validate_task_spec_for_plan(spec, restored) == []
    assert restored.coder_packet.acceptance_criteria[-1] == AcceptanceCriterion(
        id="server-bound-focused-test-artifact",
        description=(
            "Update existing focused test artifact tests/test_app.py "
            "for the requested behavior."
        ),
        kind="behavioral",
    )
    assert review_task_spec_from_plan(
        restored,
        [PRIMARY, SECONDARY],
        authorized_paths=["src/", "tests/"],
    ) == spec
    with pytest.raises(
        ValueError,
        match="review_task_spec_unrequested_changed_file",
    ):
        review_task_spec_from_plan(
            restored,
            [PRIMARY, SECONDARY, "src/model_selected_decoy.py"],
            authorized_paths=["src/", "tests/"],
        )


def test_implicit_test_binding_fails_closed_when_tracked_matches_are_ambiguous(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / PRIMARY).write_text(
        "def existing() -> bool:\n    return True\n",
        encoding="utf-8",
    )
    for path in (SECONDARY, "tests/app_test.py"):
        (root / path).write_text(
            "from src.app import existing\n\n"
            "def test_existing():\n"
            "    assert existing()\n",
            encoding="utf-8",
        )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    plan = replace(
        _plan(
            "Please add a small greeting function to src/app.py. "
            "Keep existing behavior and add focused tests for the new function."
        ),
        bundle_snapshot=BundleSnapshot(
            bundle_path="",
            bundle_sha256="",
            workspace_root=str(root.resolve()),
            generated_at="2026-07-22T00:00:00Z",
        ),
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )

    assert bound == plan
    assert task_spec_from_plan(bound).allowed_files == [PRIMARY]


@pytest.mark.parametrize(
    ("candidate_mode", "authorized_paths"),
    [
        ("untracked", ("src/", "tests/")),
        ("symlink", ("src/", "tests/")),
        ("scope_excluded", ("src/",)),
    ],
)
def test_implicit_test_binding_requires_tracked_regular_in_scope_artifact(
    tmp_path: Path,
    candidate_mode: str,
    authorized_paths: tuple[str, ...],
) -> None:
    root = tmp_path / "workspace"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / PRIMARY).write_text(
        "def existing() -> bool:\n    return True\n",
        encoding="utf-8",
    )
    test_content = (
        "from src.app import existing\n\n"
        "def test_existing():\n"
        "    assert existing()\n"
    )
    if candidate_mode == "symlink":
        support = root / "support.py"
        support.write_text(test_content, encoding="utf-8")
        try:
            (root / SECONDARY).symlink_to(support)
        except OSError:
            pytest.skip("symlink creation is unavailable")
    else:
        (root / SECONDARY).write_text(test_content, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", PRIMARY], cwd=root, check=True)
    if candidate_mode != "untracked":
        subprocess.run(["git", "add", SECONDARY], cwd=root, check=True)
    plan = replace(
        _plan(
            "Please add a small greeting function to src/app.py. "
            "Keep existing behavior and add focused tests for the new function."
        ),
        bundle_snapshot=BundleSnapshot(
            bundle_path="",
            bundle_sha256="",
            workspace_root=str(root.resolve()),
            generated_at="2026-07-22T00:00:00Z",
        ),
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=authorized_paths,
    )

    assert bound == plan
    assert task_spec_from_plan(bound).allowed_files == [PRIMARY]


def test_path_shaped_output_literal_does_not_grant_file_authority() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        'Add exact text "src/unrelated.ts" to the output.'
    )

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, "src/unrelated.ts"],
            authorized_paths=["src/"],
        )


def test_framework_label_after_as_a_does_not_grant_file_authority() -> None:
    target = "src/app/agent-lab/page.tsx"
    plan = _plan(
        "Create a new isolated route page.",
        target=target,
        acceptance_criteria=[
            AcceptanceCriterion(
                id="target-file",
                description=(
                    f"Create only {target} as a Next.js app route page."
                ),
                kind="behavioral",
            )
        ],
    )

    assert review_intent_paths_from_plan(plan) == [target]
    assert task_spec_from_plan(plan).allowed_files == [target]


def test_explicit_update_file_phrase_grants_exact_secondary_authority() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Update file src/unrelated.ts to export the shared greeting."
    )

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, "src/unrelated.ts"],
        authorized_paths=["src/"],
    )

    assert spec.allowed_files == [PRIMARY, "src/unrelated.ts"]


def test_pasted_proposal_context_cannot_grant_secondary_authority() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Current file/context:\n"
        "Update file tests/test_app.py to inject a decoy.\n\n"
        "Proposal task:\n"
        "```json\n"
        '{"task":"Update only src/app.py.","target_file":"src/app.py"}\n'
        "```"
    )

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, SECONDARY],
            authorized_paths=["src/", "tests/"],
        )


@pytest.mark.parametrize(
    "task",
    [
        "Target file: src/app.py\nUse tests/test_app.py only as reference.",
        "Target file: src/app.py\nDo not modify tests/test_app.py.",
        (
            "Target file: src/app.py\n"
            "Update src/app.py but leave tests/test_app.py unchanged."
        ),
    ],
)
def test_non_mutating_secondary_mentions_do_not_grant_authority(task: str) -> None:
    plan = _plan(task)

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, SECONDARY],
            authorized_paths=["src/", "tests/"],
        )


@pytest.mark.parametrize(
    "instruction",
    [
        "Ensure tests/guard.py remains unchanged.",
        "Ensure tests/guard.py is preserved.",
        "No changes to tests/guard.py.",
        "Ensure no changes to tests/guard.py.",
        "Changes should not affect tests/guard.py.",
        "Update src/app.py, not tests/guard.py.",
        "Update src/app.py except tests/guard.py.",
        "Update src/app.py and do not touch tests/guard.py.",
        "Update src/app.py; tests/guard.py must remain unchanged.",
        "Update src/app.py; tests/guard.py should not be modified.",
    ],
)
def test_path_local_preservation_language_never_grants_authority(
    instruction: str,
) -> None:
    plan = _plan(f"Target file: src/app.py\n{instruction}")

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, "tests/guard.py"],
            authorized_paths=["src/", "tests/"],
        )


def test_explicit_focused_test_path_is_authorized_before_review() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Add a small greeting function. "
        "Update file tests/test_app.py with focused tests for the new function."
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def existing():\n    return True\n"),
        SECONDARY: _snapshot(
            SECONDARY,
            "from src import app\n\ndef test_existing():\n    assert app.existing()\n",
        ),
    }

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, SECONDARY],
        authorized_paths=["src/", "tests/"],
        artifact_snapshots=snapshots,
    )

    assert spec.allowed_files == [PRIMARY, SECONDARY]


def test_focused_test_capability_rejects_unrelated_existing_test() -> None:
    unrelated = "tests/test_unrelated.py"
    plan = _plan(
        "Target file: src/app.py\n"
        "Add a small greeting function and add focused tests for the new function."
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def existing():\n    return True\n"),
        unrelated: _snapshot(unrelated, "from src import unrelated\n"),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, unrelated],
            authorized_paths=["src/", "tests/"],
            artifact_snapshots=snapshots,
        )


@pytest.mark.parametrize(
    "instruction",
    [
        "Do not add tests.",
        "Never create tests.",
        "Don't add tests.",
        "You shouldn't add tests.",
        "You mustn't add tests.",
        "You won't add tests.",
        "You wouldn't add tests.",
        "You couldn't add tests.",
        "You needn't add tests.",
        "It isn't required to add tests.",
        "We should not add tests.",
        "You should not add tests.",
        "Cannot add tests.",
        "Do anything except add tests.",
        "No need to add tests.",
        "There is no requirement to add tests.",
        "It is forbidden to add tests.",
        "Do everything other than add tests.",
        "Do anything but add tests.",
        "Update behavior but not add tests.",
        "Update code rather than add tests.",
        "Remember not to add tests.",
        "Be sure not to create tests.",
        "Under no circumstances add tests.",
        "You are not allowed to add tests.",
        "Add zero tests.",
        "Add 0 tests.",
        "Discuss whether to add tests.",
        "Explain how to add tests.",
        "Consider whether to add tests.",
        "Evaluate whether to add tests.",
        "Document how to add tests.",
        "Write about the tests in the report.",
        "Include existing tests in the documentation.",
    ],
)
def test_non_affirmative_test_language_cannot_enable_test_capability(
    instruction: str,
) -> None:
    plan = _plan(f"Target file: src/app.py\nUpdate the greeting. {instruction}")
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def existing():\n    return True\n"),
        SECONDARY: _snapshot(SECONDARY, "", exists=False),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, SECONDARY],
            authorized_paths=["src/", "tests/"],
            artifact_snapshots=snapshots,
        )


@pytest.mark.parametrize(
    "instruction",
    [
        "Add focused tests without network access.",
        "Write tests without mocks.",
        "Add tests that document the expected behavior.",
        "Avoid unrelated work but add focused tests.",
        "Can you add focused tests?",
        "Update the focused tests.",
        "Modify the tests.",
    ],
)
def test_test_capability_preserves_non_authority_modifiers(
    instruction: str,
) -> None:
    assert task_requests_test_artifact(instruction) is True


@pytest.mark.parametrize(
    ("test_path", "decoy_content"),
    [
        ("tests/test_app.py", '"""from src import app\n"""\n'),
        ("tests/test_app.py", "# from src import app\n"),
        ("tests/app.test.js", '/* import app from "../src/app"; */\n'),
        ("tests/app.test.js", '// import app from "../src/app";\n'),
        ("tests/app.test.js", 'const note = `require("../src/app")`;\n'),
    ],
)
def test_inert_import_text_cannot_bind_existing_test_capability(
    tmp_path: Path,
    test_path: str,
    decoy_content: str,
) -> None:
    target = "src/app.py" if test_path.endswith(".py") else "src/app.js"
    root, plan = _tracked_test_candidate_plan(
        tmp_path,
        target=target,
        test_path=test_path,
        test_content=decoy_content,
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )

    assert bound == plan
    assert task_spec_from_plan(bound).allowed_files == [target]


@pytest.mark.parametrize(
    "decoy_content",
    [
        '/* import app from "../src/admin/app"; */\n',
        '// import app from "../src/admin/app";\n',
        'const note = `require("../src/admin/app")`;\n',
        'const decoy = "require(\'../src/admin/app\')";\n',
        '/require("../src/admin/app")/.test(value);\n',
        'function f() { return /require("../src/admin/app")/; }\n',
        'const f = () => /require("../src/admin/app")/;\n',
        'function* f() { yield /require("../src/admin/app")/; }\n',
        'async function f() { await /require("../src/admin/app")/; }\n',
        'const p = 0 + /require("../src/admin/app")/;\n',
        'if (false) { new /require("../src/admin/app")/; }\n',
        'class Child extends /require("../src/admin/app")/ {}\n',
        'export default /require("../src/admin/app")/;\n',
        'if (ready) /require("../src/admin/app")/.test(value);\n',
        'import other from "../src/other/app";\n',
        'const other = require("app");\n',
        'import card from "../shared/app";\n',
        'import app from "./src/admin/app";\n',
    ],
)
def test_script_test_capability_rejects_inert_or_same_basename_modules(
    tmp_path: Path,
    decoy_content: str,
) -> None:
    target = "src/admin/app.js"
    test_path = "tests/app.test.js"
    root, plan = _tracked_test_candidate_plan(
        tmp_path,
        target=target,
        test_path=test_path,
        test_content=decoy_content,
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )

    assert bound == plan
    assert task_spec_from_plan(bound).allowed_files == [target]


def test_structurally_bound_test_under_forbidden_path_is_not_bound(
    tmp_path: Path,
) -> None:
    root, plan = _tracked_test_candidate_plan(
        tmp_path,
        target=PRIMARY,
        test_path=SECONDARY,
        test_content=(
            "from src.app import existing\n\n"
            "def test_existing():\n"
            "    assert existing()\n"
        ),
        forbidden_paths=("tests/",),
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )

    assert bound == plan
    assert task_spec_from_plan(bound).allowed_files == [PRIMARY]


def test_explicit_script_test_path_is_authorized_before_review() -> None:
    target = "src/admin/app.js"
    test_path = "tests/app.test.js"
    plan = _plan(
        f"Target file: {target}\n"
        f"Update file {test_path} with focused tests for the updated module.",
        target=target,
    )
    snapshots = {
        target: _snapshot(target, "export const value = 1;\n"),
        test_path: _snapshot(
            test_path,
            'import app from "../src/admin/app";\n',
        ),
    }

    spec = review_task_spec_from_plan(
        plan,
        [target, test_path],
        authorized_paths=["src/", "tests/"],
        artifact_snapshots=snapshots,
    )

    assert spec.allowed_files == [target, test_path]


def test_active_relative_script_import_is_bound_before_review(
    tmp_path: Path,
) -> None:
    target = "src/admin/app.js"
    test_path = "tests/app.test.js"
    root, plan = _tracked_test_candidate_plan(
        tmp_path,
        target=target,
        test_path=test_path,
        test_content='import app from "../src/admin/app";\n',
    )

    bound = bind_requested_artifacts_to_plan(
        plan,
        root,
        authorized_paths=("src/", "tests/"),
    )
    restored = ArchitectPlan.from_dict(bound.to_dict())

    assert bound != plan
    assert task_spec_from_plan(restored).allowed_files == [target, test_path]
    assert restored.coder_packet.acceptance_criteria[-1] == AcceptanceCriterion(
        id="server-bound-focused-test-artifact",
        description=(
            "Update existing focused test artifact tests/app.test.js "
            "for the requested behavior."
        ),
        kind="behavioral",
    )


def test_explicit_shared_helper_path_is_authorized_before_review() -> None:
    contacts = "src/contacts.py"
    helper = "src/normalization.py"
    plan = _plan(
        "`normalize_username` in `src/app.py` and `normalize_email` in "
        "`src/contacts.py` repeat the same cleanup. Refactor that duplicated "
        "logic into one small shared helper. "
        "Create file src/normalization.py as that shared helper.",
        acceptance_criteria=[
            AcceptanceCriterion(
                id="contacts",
                description='File "src/contacts.py" must contain "normalize_email".',
                kind="literal",
            )
        ],
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def normalize_username(value):\n    return value\n"),
        contacts: _snapshot(
            contacts,
            "def normalize_email(value):\n    return value\n",
        ),
        helper: _snapshot(helper, "", exists=False),
    }

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, contacts, helper],
        authorized_paths=["src/"],
        artifact_snapshots=snapshots,
    )

    assert spec.allowed_files[0] == PRIMARY
    assert set(spec.allowed_files) == {PRIMARY, contacts, helper}
    assert spec == task_spec_from_plan(plan)


def test_shared_helper_capability_never_authorizes_overwriting_existing_extra() -> None:
    contacts = "src/contacts.py"
    helper = "src/unrelated.py"
    plan = _plan(
        "`normalize_username` in `src/app.py` and `normalize_email` in "
        "`src/contacts.py` repeat the same cleanup. Refactor that duplicated "
        "logic into one small shared helper.",
        acceptance_criteria=[
            AcceptanceCriterion(
                id="contacts",
                description='File "src/contacts.py" must contain "normalize_email".',
                kind="literal",
            )
        ],
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def normalize_username(value):\n    return value\n"),
        contacts: _snapshot(
            contacts,
            "def normalize_email(value):\n    return value\n",
        ),
        helper: _snapshot(helper, "do_not_overwrite = True\n", exists=True),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, contacts, helper],
            authorized_paths=["src/"],
            artifact_snapshots=snapshots,
        )


@pytest.mark.parametrize(
    "instruction",
    [
        "Do not refactor the duplicated logic into a shared helper.",
        "Never refactor repeated logic into a common helper.",
        "Don't refactor duplicated logic into a shared helper.",
        "You shouldn't refactor repeated logic into a common helper.",
        "You mustn't refactor duplicated logic into a shared helper.",
        "No refactor of duplicated logic into a shared helper.",
        "There must be no refactor of repeated logic into a common helper.",
        "Avoid a refactor of duplicated logic into a shared helper.",
        "Refrain from refactor of duplicated logic into a shared helper.",
        "Refactor of duplicated logic into a shared helper is prohibited.",
        "It is forbidden to refactor duplicated logic into a shared helper.",
        "There is no requirement to refactor duplicated logic into a shared helper.",
        "Do everything other than refactor duplicated logic into a shared helper.",
        "Do anything but refactor duplicated logic into a shared helper.",
        "Update code rather than refactor duplicated logic into a shared helper.",
        "Remember not to refactor duplicated logic into a shared helper.",
        "Under no circumstances refactor duplicated logic into a shared helper.",
        "You are not allowed to refactor duplicated logic into a shared helper.",
        "Discuss whether to refactor duplicated logic into a shared helper.",
        "Explain how to refactor duplicated logic into a shared helper.",
        "Consider whether to refactor duplicated logic into a shared helper.",
        "Evaluate whether to refactor duplicated logic into a shared helper.",
        "Document how to refactor duplicated logic into a shared helper.",
    ],
)
def test_negated_shared_helper_language_cannot_enable_helper_capability(
    instruction: str,
) -> None:
    contacts = "src/contacts.py"
    helper = "src/normalization.py"
    plan = _plan(
        "Target file: src/app.py\n"
        "Update src/contacts.py with the matching behavior. "
        f"{instruction}",
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def normalize_username(value):\n    return value\n"),
        contacts: _snapshot(
            contacts,
            "def normalize_email(value):\n    return value\n",
        ),
        helper: _snapshot(helper, "", exists=False),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, contacts, helper],
            authorized_paths=["src/"],
            artifact_snapshots=snapshots,
        )


@pytest.mark.parametrize(
    "instruction",
    [
        (
            "Refactor duplicated logic into a shared helper without changing "
            "behavior."
        ),
        (
            "Refactor repeated logic into a common helper with no behavior "
            "changes."
        ),
        "Extract duplicated logic into a shared helper.",
        "Refactor duplicated logic into a helper shared by both files.",
        "Avoid unrelated edits but refactor duplicated logic into a shared helper.",
    ],
)
def test_shared_helper_capability_preserves_behavior_modifiers(
    instruction: str,
) -> None:
    assert task_requests_shared_helper_artifact(instruction) is True


@pytest.mark.parametrize(
    "instruction",
    [
        "Cannot update src/secondary.py.",
        "Don't update src/secondary.py.",
        "You shouldn't modify src/secondary.py.",
        "You mustn't change src/secondary.py.",
        "This doesn't update src/secondary.py.",
        "Refrain from updating src/secondary.py.",
        "Updating src/secondary.py is prohibited.",
        "Do anything except update src/secondary.py.",
        "Refuse to update src/secondary.py.",
        "It is forbidden to update src/secondary.py.",
        "There is no requirement to update src/secondary.py.",
        "Do everything other than update src/secondary.py.",
        "Work without updating src/secondary.py.",
        "Updating src/secondary.py is not allowed.",
        "Updating src/secondary.py is out of scope.",
        "Updating src/secondary.py cannot be done.",
        "Updating src/secondary.py isn't allowed.",
        "Not update src/secondary.py.",
        "Please not update src/secondary.py.",
        "Update neither src/app.py nor src/secondary.py.",
        "Neither update src/app.py nor src/secondary.py.",
        "Update src/app.py instead of src/secondary.py.",
        "Update src/app.py rather than src/secondary.py.",
        "Should we update src/secondary.py?",
        "Change the displayed filename to src/secondary.py.",
        "Update docs/readme.md to mention src/secondary.py.",
        "Discuss whether to update src/secondary.py.",
        "Explain how to update src/secondary.py.",
        "Consider whether to update src/secondary.py.",
        "Evaluate whether to update src/secondary.py.",
        "Document how to update src/secondary.py.",
        "Maybe update src/secondary.py.",
    ],
)
def test_nonaffirmative_path_language_cannot_grant_exact_file_authority(
    instruction: str,
) -> None:
    secondary = "src/secondary.py"
    plan = _plan(f"Target file: src/app.py\n{instruction}")

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, secondary],
            authorized_paths=["src/"],
        )


def test_direct_path_mutation_with_preservation_modifier_remains_authorized() -> None:
    secondary = "src/secondary.py"
    plan = _plan(
        "Target file: src/app.py\n"
        "Update src/secondary.py without changing its public API."
    )

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, secondary],
        authorized_paths=["src/"],
    )

    assert spec.allowed_files == [PRIMARY, secondary]


@pytest.mark.parametrize(
    "instruction",
    [
        "Ensure src/secondary.py contains the greeting.",
        "Ensure literal GREETING is present in src/secondary.py.",
        "Make src/secondary.py contain the greeting.",
        "Ensure src/secondary.py is updated with the greeting.",
        "Set src/secondary.py to the requested content.",
        "Could you update src/secondary.py?",
    ],
)
def test_direct_positive_path_language_grants_exact_file_authority(
    instruction: str,
) -> None:
    secondary = "src/secondary.py"
    plan = _plan(f"Target file: src/app.py\n{instruction}")

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, secondary],
        authorized_paths=["src/"],
    )

    assert spec.allowed_files == [PRIMARY, secondary]


def test_optional_integer_callable_contract_derives_only_public_bounds() -> None:
    assert optional_integer_callable_contract(_optional_integer_task()) == {
        "ok": True,
        "skipped": False,
        "reason_code": "",
        "callable": "list_records",
        "parameters": [
            {"name": "offset", "minimum": 0},
            {"name": "limit", "minimum": 1},
        ],
        "invalid_exception": "ValueError",
    }


@pytest.mark.parametrize(
    "task",
    [
        (
            "Add pagination to `list_records` with optional `offset` and "
            "`limit` arguments. Both values must be non-negative integers."
        ),
        (
            "Add pagination to `list_records` with optional `offset` or "
            "`limit` arguments. Both values must be non-negative integers. "
            "Raise `ValueError` for invalid pagination values."
        ),
        (
            "Add pagination to `list_records` with optional `offset` and "
            "`limit` arguments. Values should be sensible integers. Raise "
            "`ValueError` for invalid pagination values."
        ),
        (
            "Add pagination to `list_records` with optional `offset`, "
            "`offset`, and `limit` arguments. All values must be "
            "non-negative integers. Raise `ValueError` for invalid values."
        ),
        (
            "Add pagination to `list_records` with optional `offset`, "
            "`limit`, and `window` arguments. Both values must be "
            "non-negative integers. Raise `ValueError` for invalid values."
        ),
        (
            "Add pagination to `list_records` with optional `offset` and "
            "`limit` arguments. Both values must be non-negative integers, "
            "with `offset` at least 1 and `offset` at least 2. Raise "
            "`ValueError` for invalid values."
        ),
        (
            "Add pagination to `list_records` with optional `offset` and "
            "`limit` arguments. Add paging to `fetch_records` with optional "
            "`start` and `count` arguments. All values must be non-negative "
            "integers. Raise `ValueError` for invalid values."
        ),
        (
            "Add pagination to list_records with optional `offset` and "
            "`limit` arguments. Both values must be non-negative integers. "
            "Raise `ValueError` for invalid pagination values."
        ),
    ],
)
def test_optional_integer_callable_contract_fails_partial_or_ambiguous_prose(
    task: str,
) -> None:
    result = optional_integer_callable_contract(task)

    assert result["skipped"] is False
    assert result["ok"] is False
    assert result["reason_code"] in {
        "optional_integer_contract_ambiguous",
        "optional_integer_contract_incomplete",
    }


def test_optional_integer_callable_contract_skips_truly_absent_anchor() -> None:
    result = optional_integer_callable_contract(
        "Refactor the record formatter without changing its public behavior."
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["reason_code"] == "optional_integer_contract_not_explicit"


def test_optional_integer_callable_contract_skips_nonnumeric_optional_args() -> None:
    result = optional_integer_callable_contract(
        "Add filtering to `list_records` with an optional `status` argument. "
        "The status value is a string."
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["reason_code"] == "optional_integer_contract_not_explicit"


@pytest.mark.parametrize(
    "request_text",
    [
        "It is unnecessary to update `list_records` with optional `offset` "
        "and `limit` arguments.",
        "There is no request to update `list_records` with optional `offset` "
        "and `limit` arguments.",
        "Should we update `list_records` with optional `offset` and `limit` "
        "arguments?",
        "Do we need to update `list_records` with optional `offset` and "
        "`limit` arguments?",
        "We discussed whether to update `list_records` with optional `offset` "
        "and `limit` arguments.",
        "The rejected old proposal was to update `list_records` with optional "
        "`offset` and `limit` arguments.",
        "Rather than update `list_records` with optional `offset` and `limit` "
        "arguments, keep the signature unchanged.",
    ],
)
def test_optional_integer_contract_skips_nonaffirmative_narratives(
    request_text: str,
) -> None:
    result = optional_integer_callable_contract(
        request_text
        + " Both values must be non-negative integers. "
        "Raise `ValueError` for invalid pagination values."
    )

    assert result["ok"] is True
    assert result["skipped"] is True


@pytest.mark.parametrize(
    "request_suffix",
    [
        ", but do not validate them",
        ", but keep its signature unchanged",
        ", not actually changing its signature",
        " without enforcing any bounds",
        "; however, do not implement that change",
    ],
)
def test_optional_integer_contract_rejects_request_suffix_contradictions(
    request_suffix: str,
) -> None:
    result = optional_integer_callable_contract(
        "Update `list_records` to accept optional `offset` and `limit` "
        f"arguments{request_suffix}. Both values must be non-negative "
        "integers (with `limit` at least 1 when provided). Raise `ValueError` "
        "for invalid pagination values."
    )

    assert not (
        result["ok"] is True and result["skipped"] is False
    )


@pytest.mark.parametrize(
    "feature",
    [
        "pagination accepting floats",
        "pagination without validation",
        "pagination where negative values are allowed",
        "pagination that coerces strings",
        "pagination with advisory bounds",
        "unchecked pagination",
        "noninteger pagination",
        "loosely typed pagination",
        "error-tolerant pagination",
        "lax unvalidated paging",
    ],
)
def test_optional_integer_contract_rejects_conflicted_feature_phrase(
    feature: str,
) -> None:
    result = optional_integer_callable_contract(
        f"Add {feature} to `list_records` with optional `offset` and `limit` "
        "arguments. Both values must be non-negative integers "
        "(with `limit` at least 1 when provided). Raise `ValueError` for "
        "invalid pagination values."
    )

    assert result["ok"] is False
    assert result["skipped"] is False


@pytest.mark.parametrize(
    "parameter_list",
    [
        "`offset` `limit`",
        "`offset`,, `limit`",
        "`offset` and and `limit`",
    ],
)
def test_optional_integer_contract_rejects_malformed_parameter_separators(
    parameter_list: str,
) -> None:
    result = optional_integer_callable_contract(
        "Add pagination to `list_records` with optional "
        f"{parameter_list} arguments. Both values must be non-negative "
        "integers. Raise `ValueError` for invalid pagination values."
    )

    assert result["ok"] is False
    assert result["skipped"] is False


@pytest.mark.parametrize(
    "request_text",
    [
        "Do not add pagination to `list_records` with optional `offset` and "
        "`limit` arguments.",
        "Do not update `list_records` with optional `offset` and `limit` "
        "arguments.",
        "Never modify `list_records` with optional `offset` and `limit` "
        "arguments.",
        "Do not ever add pagination to `list_records` with optional `offset` "
        "and `limit` arguments.",
        "Do not directly update `list_records` with optional `offset` and "
        "`limit` arguments.",
        "Never again modify `list_records` with optional `offset` and "
        "`limit` arguments.",
        "Add pagination elsewhere, not to `list_records` with optional "
        "`offset` and `limit` arguments.",
        "It is forbidden to add pagination to `list_records` with optional "
        "`offset` and `limit` arguments.",
        "Avoid this exact action: add pagination to `list_records` with "
        "optional `offset` and `limit` arguments.",
        "Decline to add pagination to `list_records` with optional `offset` "
        "and `limit` arguments.",
        "Do not "
        + ("absolutely " * 12)
        + "add pagination to `list_records` with optional `offset` and "
        "`limit` arguments.",
    ],
)
def test_optional_integer_callable_contract_rejects_negated_authority(
    request_text: str,
) -> None:
    result = optional_integer_callable_contract(
        request_text
        + " Both values must be non-negative integers. "
        "Raise `ValueError` for invalid pagination values."
    )

    assert result["ok"] is True
    assert result["skipped"] is True
    assert result["reason_code"] == "optional_integer_contract_negated"


def test_optional_integer_contract_does_not_bind_unrelated_integer_clause() -> None:
    tasks = [
        (
            "Update `render` with optional `theme` arguments. Separately, "
            "`retry_count` must be a positive integer."
        ),
        (
            "Update `render` with optional `theme` arguments. Separately, "
            "all parameters must be positive integers. Raise `ValueError` "
            "for invalid values."
        ),
        (
            "Update `render` with optional `theme` arguments. The retry "
            "scheduler requires all parameters must be positive integers. "
            "Raise `ValueError` for invalid values."
        ),
    ]

    for task in tasks:
        result = optional_integer_callable_contract(task)
        assert result["ok"] is True
        assert result["skipped"] is True


@pytest.mark.parametrize(
    "topic",
    [
        "setting",
        "optional configuration",
        "unrelated offset metadata",
        "limit display setting",
        "with configuration",
    ],
)
def test_optional_integer_contract_rejects_unrelated_exception_topic(
    topic: str,
) -> None:
    result = optional_integer_callable_contract(
        "Add pagination to `list_records` with optional `offset` and `limit` "
        "arguments. All values must be positive integers. Raise `ValueError` "
        f"for invalid {topic} values."
    )

    assert result["ok"] is False
    assert result["skipped"] is False
    assert result["reason_code"] == "optional_integer_contract_incomplete"


def test_optional_integer_contract_does_not_cross_parameter_names() -> None:
    result = optional_integer_callable_contract(
        "Add bounds to `select_items` with optional `a` and `b` arguments. "
        "`a`, `b` must be a positive integer, with `b` at least 5. Raise "
        "`ValueError` for invalid bounds values."
    )

    assert result["ok"] is False
    assert result["skipped"] is False


def test_optional_integer_contract_binds_unquoted_bound_to_its_subject() -> None:
    result = optional_integer_callable_contract(
        "Update `select_items` to accept optional `a` and `b` arguments. "
        "Both values must be non-negative integers. "
        "b must be at least 5. Raise `ValueError` for invalid argument values."
    )

    assert result["ok"] is True
    assert result["parameters"] == [
        {"name": "a", "minimum": 0},
        {"name": "b", "minimum": 5},
    ]


def test_optional_integer_contract_accepts_exact_four_sentence_roles() -> None:
    result = optional_integer_callable_contract(
        "Update `list_records` to accept optional `offset` and `limit` "
        "arguments. Both values must be integers. "
        "`offset` must be a non-negative integer and `limit` must be a "
        "positive integer. Raise `ValueError` for invalid argument values."
    )

    assert result == {
        "ok": True,
        "skipped": False,
        "reason_code": "",
        "callable": "list_records",
        "parameters": [
            {"name": "offset", "minimum": 0},
            {"name": "limit", "minimum": 1},
        ],
        "invalid_exception": "ValueError",
    }


@pytest.mark.parametrize(
    "error_sentence",
    [
        "Do not validate; raise ValueError for invalid values.",
        "Ignore invalid input; raise `ValueError` for invalid values.",
        "Accept floats; `list_records` must raise ValueError for invalid values.",
    ],
)
def test_optional_integer_contract_requires_whole_error_sentence(
    error_sentence: str,
) -> None:
    result = optional_integer_callable_contract(
        "Update `list_records` to accept optional `offset` and `limit` "
        "arguments. Both values must be non-negative integers. "
        + error_sentence
    )

    assert result["ok"] is False
    assert result["skipped"] is False


@pytest.mark.parametrize(
    "constraint_text",
    [
        (
            "Both values must be non-negative integers. `offset` does not "
            "need to be a non-negative integer. Raise `ValueError` for "
            "invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Do not raise "
            "`ValueError` for invalid argument values."
        ),
        (
            "Separately, `offset` must be a non-negative integer. "
            "`limit` must be a positive integer. Raise `ValueError` for "
            "invalid argument values."
        ),
        (
            "Both values must be non-negative integers. The parser must "
            "raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Either argument may "
            "be None. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Raise `ValueError` "
            "for invalid argument values. `limit` must be at most 50."
        ),
        (
            "Both values must be non-negative integers. `limit` must also "
            "be at least `offset`. Raise `ValueError` for invalid argument "
            "values."
        ),
        (
            "`offset` must be a non-negative integer. `limit` must be an odd "
            "positive integer except 3. Raise `ValueError` for invalid "
            "argument values."
        ),
        (
            "Both values must be non-negative integers. `offset` must instead "
            "be positive. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. `offset` must be at "
            "least 5 and `limit` must be at least `offset`. Raise "
            "`ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. `limit` "
            + ("indisputably " * 10)
            + "must be at least `offset`. Raise `ValueError` for invalid "
            "argument values."
        ),
        (
            "Both values must be non-negative integers. For the reporting "
            "helper, `offset` must be at least 5. Raise `ValueError` for "
            "invalid argument values."
        ),
        (
            "`offset` must be a non-negative integer, except in compatibility "
            "mode. `limit` must be a positive integer. Raise `ValueError` for "
            "invalid argument values."
        ),
        (
            "`offset` must be a non-negative integer, but negative values are "
            "allowed. `limit` must be a positive integer. Raise `ValueError` "
            "for invalid argument values."
        ),
        (
            "`offset` must be a non-negative integer, although -1 is allowed. "
            "`limit` must be a positive integer. Raise `ValueError` for "
            "invalid argument values."
        ),
        (
            "`offset` must be a non-negative integer. `limit` must be a "
            "positive integer, or zero. Raise `ValueError` for invalid "
            "argument values."
        ),
        (
            "Both values must be non-negative integers. Negative values are "
            "allowed. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Values may also be "
            "floats. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Booleans are "
            "acceptable. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Strings should be "
            "coerced. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Do not reject invalid "
            "values. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Invalid values should "
            "not raise errors. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Validation is "
            "optional. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. The bounds are "
            "advisory. Raise `ValueError` for invalid argument values."
        ),
        (
            "Both values must be non-negative integers. Raise `ValueError` "
            "for invalid values in parse_config, not list_records."
        ),
        (
            "Both values must be non-negative integers. Raise `ValueError` "
            "for invalid values, but only in the reporting validator."
        ),
        (
            "Both values must be non-negative integers. Raise `ValueError` "
            "for invalid values elsewhere."
        ),
        (
            "Both values must be non-negative integers. The function must "
            "raise `ValueError` for invalid values in another callable."
        ),
        (
            "Defaults allow floats and strings, both values must be "
            "non-negative integers. Raise `ValueError` for invalid values."
        ),
        (
            "Defaults permit negative values, both values must be "
            "non-negative integers. Raise `ValueError` for invalid values."
        ),
        (
            "Both values must be non-negative integers, and the function must "
            "not mutate inputs but negative values are allowed. Raise "
            "`ValueError` for invalid values."
        ),
        (
            "Both values must be non-negative integers, and the function must "
            "never modify records; floats are accepted. Raise `ValueError` "
            "for invalid values."
        ),
        (
            "`offset` must be a non-negative integer,, `limit` must be a "
            "positive integer. Raise `ValueError` for invalid argument values."
        ),
    ],
)
def test_optional_integer_contract_fails_closed_on_residual_constraints(
    constraint_text: str,
) -> None:
    result = optional_integer_callable_contract(
        "Update `list_records` to accept optional `offset` and `limit` "
        f"arguments. {constraint_text}"
    )

    assert not (
        result["ok"] is True and result["skipped"] is False
    )


@pytest.mark.parametrize(
    "prefix",
    [
        "The `limit` argument must be at most 1. ",
        "The `limit` argument must be odd. ",
        "The `limit` argument may be None. ",
        "The `offset` argument must be positive. ",
        "The minimum is -1 for offset. ",
        "Zero is allowed for limit. ",
        "limit may be zero. ",
        "Legacy calls allow -1 for offset. ",
        "An upper cap of 100 applies to limit. ",
        "Floats and strings are allowed. ",
        "Invalid values should not raise errors. ",
        "Negative values are acceptable. ",
        "The bounds are advisory. ",
        "Validation is optional. ",
    ],
)
def test_optional_integer_contract_rejects_pre_request_constraints(
    prefix: str,
) -> None:
    result = optional_integer_callable_contract(
        prefix
        + "Add pagination to `list_records` with optional `offset` and "
        "`limit` arguments. Both values must be non-negative integers "
        "(with `limit` at least 1 when provided). Raise `ValueError` for "
        "invalid pagination values."
    )

    assert result["ok"] is False
    assert result["skipped"] is False


@pytest.mark.parametrize(
    "upper_bound",
    [
        "at most 100",
        "must not exceed 100",
        "cannot exceed 100",
        "no greater than 100",
        "up to 100",
        "less than 101",
        "below 101",
        "<= 100",
        "no higher than 100",
        "100 or less",
        "bounded above by 100",
        "does not exceed 100",
        "at or below 100",
        "no bigger than 100",
        "< 101",
    ],
)
def test_optional_integer_contract_rejects_unsupported_upper_bound(
    upper_bound: str,
) -> None:
    result = optional_integer_callable_contract(
        "Add pagination to `list_records` with optional `offset` and `limit` "
        "arguments. Both values must be non-negative integers and "
        f"{upper_bound}. Raise `ValueError` for invalid pagination values."
    )

    assert result["ok"] is False
    assert result["reason_code"] == (
        "optional_integer_contract_unsupported_upper_bound"
    )


def test_optional_integer_callable_contract_fails_oversized_anchored_task() -> None:
    result = optional_integer_callable_contract(
        "Add pagination to `list_records` with optional `offset` argument. "
        "The value must be a non-negative integer. "
        + ("preserve behavior " * 1_000)
    )

    assert result["ok"] is False
    assert result["skipped"] is False
    assert result["reason_code"] == "optional_integer_contract_input_too_large"


def test_optional_integer_callable_shape_requires_explicit_optional_names() -> None:
    result = optional_integer_callable_shape_check(
        _optional_integer_task(),
        "\n".join(
            [
                "def list_records(offset, limit=None, records=None):",
                "    return []",
                "",
            ]
        ),
    )

    assert result["ok"] is False
    assert {
        (item.get("parameter"), item.get("reason"))
        for item in result["violations"]
    } == {
        ("offset", "parameter_is_not_optional"),
    }


def test_optional_integer_callable_shape_accepts_equivalent_helper_validation() -> None:
    result = optional_integer_callable_shape_check(
        _optional_integer_task(),
        "\n".join(
            [
                "def _validate(name, value, minimum):",
                "    if type(value) is not int or value < minimum:",
                "        raise ValueError(name)",
                "",
                "def list_records(offset=0, limit=None):",
                "    _validate('offset', offset, 0)",
                "    if limit is not None:",
                "        _validate('limit', limit, 1)",
                "    return []",
                "",
            ]
        ),
    )

    assert result["ok"] is True
    assert result["missing_parameters"] == []
    assert result["violations"] == []


def test_fixed_literal_count_callable_derives_zero_arg_public_contract() -> None:
    task = (
        "Please add a small `count_ready_orders` service function that returns "
        "the number of orders whose `status` exactly matches "
        "`ready_for_pickup`. Keep existing lookup behavior and add focused tests."
    )

    assert fixed_literal_zero_arg_callable_names(task) == [
        "count_ready_orders"
    ]


@pytest.mark.parametrize(
    "task",
    [
        (
            "Add a `count_ready_orders` service function that accepts a "
            "`status` argument and returns the number of orders whose `status` "
            "exactly matches `ready_for_pickup`."
        ),
        (
            "Add a `has_ready_orders` service function that returns whether "
            "any order has `status` equal to `ready_for_pickup`."
        ),
        (
            "Do not add a `count_ready_orders` service function that returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Must not add a `count_ready_orders` service function that returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Should not create a `count_ready_orders` service function that "
            "returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Shall not implement a `count_ready_orders` service function that "
            "returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Cannot add a `count_ready_orders` service function that returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Can't create a `count_ready_orders` service function that returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "There is no need to add a `count_ready_orders` service function "
            "that returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` service function with zero required "
            "positional arguments that returns the number of orders whose "
            "`status` exactly matches `ready_for_pickup`."
        ),
        (
            "Given a list of orders, add a `count_ready_orders` function that "
            "returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` function that, given orders, returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` function that returns the number from "
            "the supplied collection whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` function for caller-supplied input "
            "that returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
    ],
)
def test_fixed_literal_callable_contract_does_not_invent_ambiguous_shape(
    task: str,
) -> None:
    assert fixed_literal_zero_arg_callable_names(task) == []


def test_explicit_zero_arg_language_preserves_fixed_literal_contract() -> None:
    task = (
        "Create function `count_archived_records` with zero required "
        "arguments that returns the count of records whose `state` is equal to "
        "`archived`."
    )

    assert fixed_literal_zero_arg_callable_names(task) == [
        "count_archived_records"
    ]


def test_fixed_literal_callable_shape_check_rejects_required_input() -> None:
    task = (
        "Add a `count_ready_orders` service function that returns the number "
        "of orders whose `status` exactly matches `ready_for_pickup`."
    )
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "def count_ready_orders(status: str) -> int:",
                "    return sum(",
                "        1 for order in ORDERS",
                '        if order["status"] == "ready_for_pickup"',
                "    )",
            ]
        ),
    )

    assert result == {
        "ok": False,
        "skipped": False,
        "reason_code": "fixed_literal_callable_shape_mismatch",
        "required_zero_arg_callables": ["count_ready_orders"],
        "missing_callables": [],
        "violations": [
            {
                "callable": "count_ready_orders",
                "required_positional_parameters": 1,
                "required_keyword_only_parameters": 0,
                "required_parameters": 1,
            }
        ],
    }


@pytest.mark.parametrize(
    "task",
    [
        (
        "Add a `count_ready_orders` service function to `OrderService` that "
        "returns the number of orders whose `status` exactly matches "
        "`ready_for_pickup`."
        ),
        (
            "Add function `count_ready_orders` to `OrderService` that returns "
            "the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
        (
            "Add the callable `count_ready_orders` inside class "
            "`OrderService` that returns the number of orders whose `status` "
            "exactly matches `ready_for_pickup`."
        ),
        (
            "Add count_ready_orders service function to OrderService that "
            "returns the number of orders whose `status` exactly matches "
            "`ready_for_pickup`."
        ),
    ],
)
def test_fixed_literal_callable_shape_check_accepts_bound_service_method(
    task: str,
) -> None:
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "class OrderService:",
                "    def count_ready_orders(self) -> int:",
                "        return sum(",
                "            1 for order in self.orders",
                '            if order["status"] == "ready_for_pickup"',
                "        )",
                "",
            ]
        ),
    )

    assert fixed_literal_zero_arg_callable_names(task) == [
        "count_ready_orders"
    ]
    assert result["ok"] is True
    assert result["missing_callables"] == []
    assert result["violations"] == []


@pytest.mark.parametrize(
    "task",
    [
        (
            "Add a `count_ready_orders` service function that writes metrics "
            "to `OrderMetrics` and returns the number of orders whose `status` "
            "exactly matches `ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` service function that converts "
            "results to CountResponse and returns the number of orders whose "
            "`status` exactly matches `ready_for_pickup`."
        ),
        (
            "Add a `count_ready_orders` service function that returns the "
            "number of orders whose `status` exactly matches "
            "`ready_for_pickup` in OrderStore."
        ),
    ],
)
def test_fixed_literal_callable_owner_ignores_nonownership_destinations(
    task: str,
) -> None:
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "def count_ready_orders() -> int:",
                "    return 1",
                "",
            ]
        ),
    )

    assert result["ok"] is True
    assert result["missing_callables"] == []


def test_fixed_literal_callable_shape_check_rejects_bound_method_input() -> None:
    task = (
        "On OrderService, add a `count_ready_orders` service function that "
        "returns the number of orders whose `status` exactly matches "
        "`ready_for_pickup`."
    )
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "class OrderService:",
                "    def count_ready_orders(self, orders) -> int:",
                "        return len(orders)",
                "",
            ]
        ),
    )

    assert result["ok"] is False
    assert result["violations"][0]["required_parameters"] == 1


@pytest.mark.parametrize("module_first", [True, False])
def test_fixed_literal_callable_shape_prefers_unowned_module_definition(
    module_first: bool,
) -> None:
    task = (
        "Add a `count_ready_orders` service function that returns the number "
        "of orders whose `status` exactly matches `ready_for_pickup`."
    )
    module_definition = "\n".join(
        [
            "def count_ready_orders() -> int:",
            "    return 1",
            "",
        ]
    )
    unrelated_method = "\n".join(
        [
            "class Formatter:",
            "    def count_ready_orders(self, status):",
            "        return status",
            "",
        ]
    )
    source = (
        module_definition + unrelated_method
        if module_first
        else unrelated_method + module_definition
    )

    result = fixed_literal_callable_shape_check(task, source)

    assert result["ok"] is True
    assert result["missing_callables"] == []
    assert result["violations"] == []


def test_fixed_literal_callable_shape_rejects_method_without_receiver() -> None:
    task = (
        "Add a `count_ready_orders` service function to `OrderService` that "
        "returns the number of orders whose `status` exactly matches "
        "`ready_for_pickup`."
    )
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "class OrderService:",
                "    def count_ready_orders() -> int:",
                "        return 1",
                "",
            ]
        ),
    )

    assert result["ok"] is False
    assert result["violations"] == [
        {
            "callable": "count_ready_orders",
            "required_positional_parameters": 0,
            "required_keyword_only_parameters": 0,
            "required_parameters": 0,
            "invalid_bound_receiver": True,
        }
    ]


def test_fixed_literal_callable_shape_check_rejects_required_keyword_input() -> None:
    task = (
        "Add a `count_ready_orders` service function that returns the number "
        "of orders whose `status` exactly matches `ready_for_pickup`."
    )
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                "def count_ready_orders(*, status: str) -> int:",
                "    return sum(",
                "        1 for order in ORDERS",
                '        if order["status"] == "ready_for_pickup"',
                "    )",
            ]
        ),
    )

    assert result["ok"] is False
    assert result["violations"] == [
        {
            "callable": "count_ready_orders",
            "required_positional_parameters": 0,
            "required_keyword_only_parameters": 1,
            "required_parameters": 1,
        }
    ]


@pytest.mark.parametrize(
    "signature",
    [
        "def count_ready_orders() -> int:",
        'def count_ready_orders(status: str = "ready_for_pickup") -> int:',
    ],
)
def test_fixed_literal_callable_shape_check_accepts_no_required_input(
    signature: str,
) -> None:
    task = (
        "Add a `count_ready_orders` service function that returns the count "
        "of orders whose `status` matches `ready_for_pickup`."
    )
    result = fixed_literal_callable_shape_check(
        task,
        "\n".join(
            [
                signature,
                "    return sum(",
                "        1 for order in ORDERS",
                '        if order["status"] == "ready_for_pickup"',
                "    )",
            ]
        ),
    )

    assert result["ok"] is True
    assert result["skipped"] is False
    assert result["violations"] == []
