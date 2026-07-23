from __future__ import annotations

import hashlib

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
    review_intent_paths_from_plan,
    review_task_spec_from_plan,
    task_requests_shared_helper_artifact,
    task_requests_test_artifact,
)


PRIMARY = "src/app.py"
SECONDARY = "tests/test_app.py"


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


def test_coarse_scope_does_not_authorize_unrequested_secondary_file() -> None:
    plan = _plan("Target file: src/app.py\nUpdate the greeting.")

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, "src/model_selected_decoy.py"],
            authorized_paths=["src/"],
        )


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


def test_focused_test_capability_is_bound_to_primary_module_snapshot() -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Add a small greeting function and add focused tests for the new function."
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
        ("tests/app.test.js", '/* import app from "../src/app"; */\n'),
        ("tests/app.test.js", 'const note = `require("../src/app")`;\n'),
    ],
)
def test_inert_import_text_cannot_bind_existing_test_capability(
    test_path: str,
    decoy_content: str,
) -> None:
    plan = _plan(
        "Target file: src/app.py\n"
        "Add a small greeting function and add focused tests for the new function."
    )
    snapshots = {
        PRIMARY: _snapshot(PRIMARY, "def existing():\n    return True\n"),
        test_path: _snapshot(test_path, decoy_content),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [PRIMARY, test_path],
            authorized_paths=["src/", "tests/"],
            artifact_snapshots=snapshots,
        )


@pytest.mark.parametrize(
    "decoy_content",
    [
        'const decoy = "require(\'../src/admin/app\')";\n',
        'import other from "../src/other/app";\n',
        'const other = require("app");\n',
        'import card from "../shared/app";\n',
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
    ],
)
def test_script_test_capability_rejects_inert_or_same_basename_modules(
    decoy_content: str,
) -> None:
    target = "src/admin/app.js"
    test_path = "tests/app.test.js"
    plan = _plan(
        f"Target file: {target}\nAdd focused tests for the updated module.",
        target=target,
    )
    snapshots = {
        target: _snapshot(target, "export const value = 1;\n"),
        test_path: _snapshot(test_path, decoy_content),
    }

    with pytest.raises(ValueError, match="review_task_spec_unrequested_changed_file"):
        review_task_spec_from_plan(
            plan,
            [target, test_path],
            authorized_paths=["src/", "tests/"],
            artifact_snapshots=snapshots,
        )


def test_script_test_capability_resolves_exact_active_relative_import() -> None:
    target = "src/admin/app.js"
    test_path = "tests/app.test.js"
    plan = _plan(
        f"Target file: {target}\nAdd focused tests for the updated module.",
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


def test_shared_helper_capability_allows_one_new_bound_sibling_only() -> None:
    contacts = "src/contacts.py"
    helper = "src/normalization.py"
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
        helper: _snapshot(helper, "", exists=False),
    }

    spec = review_task_spec_from_plan(
        plan,
        [PRIMARY, contacts, helper],
        authorized_paths=["src/"],
        artifact_snapshots=snapshots,
    )

    assert spec.allowed_files == [PRIMARY, contacts, helper]


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
