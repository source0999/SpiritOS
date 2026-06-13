from __future__ import annotations

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract


def test_behavior_contracts_cover_v0_2_prompt_categories() -> None:
    cases = [
        ("make a timer app", "timer-start-stop-freeze"),
        ("build me a snack break countdown", "timer-start-stop-freeze"),
        ("make a calculator app", "calculator-basic-arithmetic"),
        ("make dark theme switcher page", "theme-computed-color-change"),
        ("make a todo list app", "todo-add-and-change-item"),
        ("make a weather card demo", "weather-card-fields"),
        ("make a music player mockup", "music-player-control-state"),
        ("make a podcast episode player mock", "music-player-control-state"),
        ("make a tiny radio show player", "music-player-control-state"),
        ("make a habit tracker", "habit-state-change"),
        ("make a notes app", "notes-create-edit-visible-note"),
        ("make a password strength checker", "password-strength-feedback-change"),
        ("make a password safety meter", "password-strength-feedback-change"),
        ("make a login safety gauge", "password-strength-feedback-change"),
        ("make a simple drawing pad", "drawing-surface-changes"),
        ("make a doodle board", "drawing-surface-changes"),
        ("init a repo and make homepage for agent lab expermients", "homepage-visible-intent"),
    ]

    for prompt, probe_id in cases:
        contract = build_artifact_behavior_contract(
            prompt=prompt,
            artifact_class="static_ui_artifact",
            task_shape="disposable_small_file_bundle",
        )

        assert contract["behavior_required"] is True
        assert contract["contract_status"] == "ready"
        assert contract["probe_targets"][0]["probe_id"] == probe_id
        assert contract["probe_targets"][0]["minimum_proof_tier"] == 2
        assert "route_go" in contract["non_pass_signals"]
        assert "model_self_report" in contract["non_pass_signals"]
        assert "visible state mutation" in contract["generic_interactive_requirement"]


def test_behavior_contract_marks_unknown_behavior_unverified() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a tiny color swatch reference",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    assert contract["behavior_required"] is False
    assert contract["contract_status"] == "unverified_requirements"
    assert contract["probe_targets"] == []
    assert "UNVERIFIED" in contract["final_pass_rule"]


def test_behavior_contracts_cover_unseen_prompt_categories_without_exact_prompt_branches() -> None:
    cases = [
        ("make a tip calculator", "calculator-derived-total"),
        ("make a budget splitter", "calculator-derived-total"),
        ("build a lunch bill splittr", "calculator-derived-total"),
        ("make a flashcard app", "question-answer-state-change"),
        ("make a unit converter", "unit-converter-result"),
        ("make a mood tracker", "tracker-state-change"),
        ("make a quote generator", "generator-visible-change"),
        ("make a counter app", "counter-or-time-state-change"),
        ("make a simple calendar widget", "calendar-widget-visible-structure"),
        ("make a color palette picker", "palette-picker-state-change"),
        ("make a quiz app", "question-answer-state-change"),
        ("make a grocery list app", "list-or-ledger-state-change"),
        ("make a BMI calculator", "bmi-calculator-result"),
        ("make a random password generator", "password-generator-output"),
        ("make a markdown previewer", "markdown-preview-updates"),
        ("make a simple expense tracker", "list-or-ledger-state-change"),
        ("make a water intake tracker", "tracker-state-change"),
        ("make a workout set counter", "counter-or-time-state-change"),
        ("make a simple image gallery mockup", "gallery-navigation-or-selection"),
        ("make a tabs component demo", "tabs-active-panel-change"),
        ("make an accordion FAQ page", "accordion-expanded-state-change"),
        ("make a progress bar demo", "progress-bar-visible-value"),
        ("make a star rating widget", "star-rating-selection-change"),
        ("make a simple habit streak tracker", "tracker-state-change"),
        ("build a farmers market checklist app", "checklist-add-visible-item"),
        ("make a quick scratchpad notes pad", "notes-create-edit-visible-note"),
        ("make a day night mode swapper", "theme-computed-color-change"),
        ("make a sunrise midnight mode toggle", "theme-computed-color-change"),
        ("make an audio deck mock", "music-player-control-state"),
        ("make a road trip gas split tool", "calculator-derived-total"),
        ("make a pocket memo board app", "notes-create-edit-visible-note"),
        ("make a passphrase strength meter", "password-strength-feedback-change"),
        ("make a cost sharer", "calculator-derived-total"),
        ("make something that splits parking costs", "calculator-derived-total"),
        ("make a palette switch", "theme-computed-color-change"),
        ("make a dusk dawn switch", "theme-computed-color-change"),
        ("make the screen change when it gets dark", "theme-computed-color-change"),
        ("make a sunrise sunset mode switch", "theme-computed-color-change"),
        ("make a phrase strength gauge", "password-strength-feedback-change"),
        ("make a secret phrase meter", "password-strength-feedback-change"),
        ("show me how strong this passphrase is", "password-strength-feedback-change"),
        ("make a porch weather tile", "weather-card-fields"),
        ("make a weekend forecast tile", "weather-card-fields"),
        ("make a finger paint pad", "drawing-surface-changes"),
        ("make a paint doodle thing", "drawing-surface-changes"),
    ]

    for prompt, probe_id in cases:
        contract = build_artifact_behavior_contract(
            prompt=prompt,
            artifact_class="static_ui_artifact",
            task_shape="disposable_small_file_bundle",
        )

        assert contract["behavior_required"] is True, prompt
        assert contract["probe_targets"][0]["probe_id"] == probe_id, prompt


def test_static_mockup_without_interaction_can_remain_unverified_static() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a static profile card mockup",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    assert contract["behavior_required"] is False
    assert contract["probe_targets"] == []
    assert contract["generic_interactive_requirement"] == ""


def test_behavior_contract_summary_includes_generic_visible_mutation_requirement() -> None:
    from source_proxy.decision.artifact_behavior_contract import summarize_behavior_contract_for_prompt

    contract = build_artifact_behavior_contract(
        prompt="make a water tracker",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    summary = summarize_behavior_contract_for_prompt(contract)

    assert "visible state mutation" in summary
    assert "Do not treat route GO" in summary
