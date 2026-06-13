from __future__ import annotations

from pathlib import Path

from source_proxy.decision.task_spec_intake import build_task_spec_intake


LEVEL_3_TARGET = (
    "docs/evidence/source-proxy-remaining-levels-daily-driver-readiness-20260612/"
    "level-3/sandbox-approved-doc.md"
)


def test_blunt_make_calculator_resolves_to_disposable_artifact(tmp_path: Path) -> None:
    intake = build_task_spec_intake(
        "make a tip calculator",
        workspace_root=tmp_path,
        wants_implementation=True,
        allow_messy_homepage_helper=True,
    )

    assert intake.task_kind == "create_file_bundle"
    assert intake.workspace_mode == "disposable_workspace"
    assert intake.target_source == "model_authored_required"
    assert intake.artifact_class == "static_ui_artifact"
    assert ".html" in intake.allowed_extensions
    assert "target_missing" not in intake.reason_codes


def test_markdown_previewer_is_browser_ui_not_markdown_document(tmp_path: Path) -> None:
    intake = build_task_spec_intake(
        "make a markdown previewer",
        workspace_root=tmp_path,
        wants_implementation=True,
        allow_messy_homepage_helper=True,
    )

    assert intake.task_kind == "create_file_bundle"
    assert intake.workspace_mode == "disposable_workspace"
    assert intake.artifact_class == "static_ui_artifact"
    assert ".html" in intake.allowed_extensions
    assert ".md" not in intake.allowed_extensions


def test_messy_interactive_checklist_and_notes_resolve_to_static_ui(tmp_path: Path) -> None:
    for prompt in [
        "build a farmers market checklist app",
        "make a quick scratchpad notes app",
    ]:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.task_kind == "create_file_bundle", prompt
        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.artifact_class == "static_ui_artifact", prompt
        assert intake.allowed_extensions == [".html", ".css", ".js"], prompt
        assert intake.target_source == "model_authored_required", prompt
        assert intake.allowed_files == [], prompt


def test_messy_meter_doodle_and_splitter_resolve_to_static_ui(tmp_path: Path) -> None:
    for prompt in [
        "build a tiny bill splittr",
        "make a login password meter",
        "make a canvas doodle board",
    ]:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.task_kind == "create_file_bundle", prompt
        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.artifact_class == "static_ui_artifact", prompt
        assert ".html" in intake.allowed_extensions, prompt
        assert "target_missing" not in intake.reason_codes, prompt


def test_document_checklist_and_notes_still_resolve_to_markdown(tmp_path: Path) -> None:
    for prompt in [
        "make a markdown checklist for launch review",
        "create notes for the release guide document",
    ]:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.task_kind == "create_new_file", prompt
        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.artifact_class == "markdown_document", prompt
        assert intake.allowed_extensions == [".md"], prompt


def test_disposable_artifact_does_not_block_for_missing_repo_target(tmp_path: Path) -> None:
    for prompt in [
        "make a pomodoro timer",
        "make a unit converter",
        "make a quote generator",
        "make a color palette picker",
        "make a stopwatch",
        "make a random password generator",
        "make a workout set counter",
        "make a star rating widget",
    ]:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.clarification_state == "not_needed", prompt


def test_standalone_theme_toggle_words_resolve_to_disposable_static_ui(tmp_path: Path) -> None:
    for prompt in [
        "make a day night color flipper",
        "make a sunrise midnight mode toggle",
        "make a tiny theme switcher widget",
    ]:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.task_kind == "create_file_bundle", prompt
        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.artifact_class == "static_ui_artifact", prompt
        assert intake.target_source == "model_authored_required", prompt
        assert "target_missing" not in intake.reason_codes, prompt


def test_level_3_semantic_synonyms_resolve_to_disposable_static_ui(tmp_path: Path) -> None:
    prompts = [
        "make a cost sharer",
        "make a parking cost splitter",
        "make a garage cost sharer",
        "make a split parking fee tool",
        "make a share a garage bill widget",
        "make something that splits parking costs",
        "make a palette switch",
        "make a dusk dawn switch",
        "make a theme palette flipper",
        "make a sunrise sunset mode switch",
        "make the screen change when it gets dark",
        "make a color mood switcher",
        "make a phrase strength gauge",
        "make a secret phrase meter",
        "make a passphrase strength checker",
        "make a login phrase safety gauge",
        "show me how strong this passphrase is",
        "make a password safety meter",
    ]

    for prompt in prompts:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.task_kind == "create_file_bundle", prompt
        assert intake.workspace_mode == "disposable_workspace", prompt
        assert intake.task_shape == "disposable_small_file_bundle", prompt
        assert intake.artifact_class == "static_ui_artifact", prompt
        assert intake.target_source == "model_authored_required", prompt
        assert intake.allowed_extensions == [".html", ".css", ".js"], prompt
        assert "target_missing" not in intake.reason_codes, prompt
        assert "target_unresolved" not in intake.reason_codes, prompt


def test_level_3_real_repo_controls_do_not_force_disposable_static_ui(tmp_path: Path) -> None:
    prompts = [
        "add a parking cost sharer to the existing dashboard",
        "update the login safety gauge component in src",
        "modify the production theme switcher",
        "fix the existing drawing canvas bug in the repo",
        "change the real weather tile in the app",
        "edit src/components/ThemeSwitcher.tsx to use dawn colors",
        "update the existing password meter test file",
        "repair the dashboard's forecast tile component",
        "modify the app's real billing splitter route",
    ]

    for prompt in prompts:
        intake = build_task_spec_intake(
            prompt,
            workspace_root=tmp_path,
            wants_implementation=True,
            allow_messy_homepage_helper=True,
        )

        assert intake.workspace_mode != "disposable_workspace", prompt
        assert intake.task_shape != "disposable_small_file_bundle", prompt
        assert intake.target_source != "model_authored_required", prompt
        assert intake.clarification_state in {"required", "blocked"}, prompt


def test_level_3_supervised_new_evidence_file_is_ready(tmp_path: Path) -> None:
    intake = build_task_spec_intake(
        "\n".join(
            [
                "Update one approved markdown evidence note with a one-line Level 3 marker.",
                f"Target file: {LEVEL_3_TARGET}",
                f"Allowed files: {LEVEL_3_TARGET}",
            ]
        ),
        workspace_root=tmp_path,
        allowed_files=[LEVEL_3_TARGET],
        forbidden_files=[".env", ".env.*", "*.pem", "*.key", "certificates/*"],
        wants_implementation=True,
    )

    assert intake.task_kind == "create_new_file"
    assert intake.allowed_files == [LEVEL_3_TARGET]
    assert intake.workspace_mode == "real_repo_supervised"
    assert intake.approval_level == "manual_apply_required"
    assert intake.clarification_state == "not_needed"
    assert "target_missing" not in intake.reason_codes
    assert "real_repo_supervised_create" in intake.reason_codes


def test_level_3_missing_target_without_allowed_files_still_requires_clarification(tmp_path: Path) -> None:
    intake = build_task_spec_intake(
        f"Target file: {LEVEL_3_TARGET}\nUpdate the approved note.",
        workspace_root=tmp_path,
        wants_implementation=True,
    )

    assert intake.task_kind == "ask_clarification"
    assert intake.allowed_files == []
    assert intake.workspace_mode == "none"
    assert intake.clarification_state == "required"
    assert "target_missing" in intake.reason_codes


def test_level_3_target_outside_allowed_files_requires_clarification(tmp_path: Path) -> None:
    intake = build_task_spec_intake(
        f"Target file: {LEVEL_3_TARGET}\nUpdate the approved note.",
        workspace_root=tmp_path,
        allowed_files=["docs/evidence/other.md"],
        wants_implementation=True,
    )

    assert intake.clarification_state == "required"
    assert intake.allowed_files == []
    assert "target_missing" in intake.reason_codes


def test_level_3_env_and_path_traversal_do_not_become_supervised_create(tmp_path: Path) -> None:
    env_intake = build_task_spec_intake(
        "Target file: .env\nAllowed files: .env\nAdd TEST_VALUE=1",
        workspace_root=tmp_path,
        allowed_files=[".env"],
        forbidden_files=[".env", ".env.*", "*.pem", "*.key", "certificates/*"],
        wants_implementation=True,
    )
    traversal_intake = build_task_spec_intake(
        "Target file: ../outside.md\nAllowed files: ../outside.md\nAdd a marker.",
        workspace_root=tmp_path,
        allowed_files=["../outside.md"],
        wants_implementation=True,
    )

    assert env_intake.task_kind == "protected_path"
    assert env_intake.clarification_state == "blocked"
    assert "protected_path" in env_intake.reason_codes
    assert traversal_intake.task_kind == "path_escape"
    assert traversal_intake.clarification_state == "blocked"
