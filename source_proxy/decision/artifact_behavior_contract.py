from __future__ import annotations

import re
from typing import Any


CONTRACT_VERSION = "source-proxy-artifact-behavior-contract-v0.2.phase-3"


def build_artifact_behavior_contract(
    *,
    prompt: str,
    artifact_class: str,
    task_shape: str,
) -> dict[str, Any]:
    normalized = (prompt or "").lower()
    criteria = _criteria_for_prompt(normalized)
    behavior_required = bool(criteria)

    return {
        "contract_version": CONTRACT_VERSION,
        "prompt": prompt,
        "artifact_class": artifact_class,
        "task_shape": task_shape,
        "behavior_required": behavior_required,
        "contract_status": "ready" if behavior_required else "unverified_requirements",
        "probe_targets": criteria,
        "preview_requirement": _preview_requirement(artifact_class, behavior_required),
        "generic_interactive_requirement": _generic_interactive_requirement(criteria),
        "generic_behavior_requirement_examples": _generic_behavior_requirement_examples(),
        "final_pass_rule": (
            "Final PASS requires every required behavior probe to pass against the generated artifact."
            if behavior_required
            else "Final PASS requires later verifier approval; product behavior remains UNVERIFIED before generation."
        ),
        "non_pass_signals": [
            "route_go",
            "artifact_exists",
            "preview_opens",
            "static_dom_presence",
            "model_self_report",
        ],
    }


def summarize_behavior_contract_for_prompt(contract: dict[str, Any]) -> str:
    targets = list(contract.get("probe_targets") or [])
    if not targets:
        return "No concrete behavior probe inferred yet; verifier must keep product behavior UNVERIFIED."
    lines = ["Behavior contract before generation:"]
    for target in targets:
        lines.append(
            "- "
            + str(target.get("probe_id") or "probe")
            + ": "
            + str(target.get("acceptance_criterion") or "")
            + " Expected observation: "
            + str(target.get("expected_observation") or "")
        )
    if contract.get("generic_interactive_requirement"):
        lines.append(str(contract["generic_interactive_requirement"]))
    lines.append("Do not treat route GO, file creation, preview open, static DOM, or self-report as product PASS.")
    return "\n".join(lines)


def _criteria_for_prompt(normalized: str) -> list[dict[str, Any]]:
    if _has_any(normalized, "timer", "countdown", "stopwatch"):
        return [
            _probe(
                "timer-start-stop-freeze",
                "Start runs local timer/count state with JavaScript interval or equivalent state mutation; Stop freezes elapsed time if present; Reset returns to the initial value if present.",
                ["click Start", "wait briefly", "confirm displayed time/count changes", "click Stop if present", "optionally click Reset"],
                "Displayed time/count text changes after Start and does not rely on a static label or inert button.",
            )
        ]
    if _has_any(normalized, "splitter", "splittr", "sharer") or (
        _has_any(normalized, "tip", "bill", "budget", "cost", "costs", "fee", "fees")
        and _has_any(normalized, "calculator", "calc", "split", "splits", "share", "sharer", "tool")
    ) or (
        _has_any(normalized, "split", "splits", "share") and _has_any(normalized, "tool", "money", "pizza", "gas", "cost", "costs", "fee", "fees", "bill", "tip")
    ):
        return [
            _probe(
                "calculator-derived-total",
                "Numeric inputs produce a visible calculated result.",
                ["enter small numeric values", "trigger calculation if required"],
                "The displayed total/share/result changes to the expected numeric value.",
            )
        ]
    if _has(normalized, "bmi"):
        return [
            _probe(
                "bmi-calculator-result",
                "BMI calculator computes a visible BMI from height and weight.",
                ["enter height and weight", "trigger calculation if required"],
                "A plausible BMI number appears.",
            )
        ]
    if _has(normalized, "calculator"):
        return [
            _probe(
                "calculator-basic-arithmetic",
                "Basic arithmetic computes correctly.",
                ["enter or click 2 + 3 ="],
                "The calculator displays 5 for 2 + 3.",
            )
        ]
    if _has(normalized, "converter"):
        return [
            _probe(
                "unit-converter-result",
                "Unit converter transforms a numeric input into a visible converted value.",
                ["enter a numeric value", "select or use an available conversion"],
                "A converted numeric value appears and differs from the input when units differ.",
            )
        ]
    if _has(normalized, "markdown") and _has(normalized, "previewer"):
        return [
            _probe(
                "markdown-preview-updates",
                "Markdown preview updates when source text changes.",
                ["type markdown text into the editor"],
                "Rendered preview shows formatted content from the entered markdown.",
            )
        ]
    if _has(normalized, "password") and _has_any(normalized, "generator", "random"):
        return [
            _probe(
                "password-generator-output",
                "Password generator creates a visible password value on demand.",
                ["click generate or adjust available controls"],
                "A generated password appears and can change on a later generation.",
            )
        ]
    if _has_any(normalized, "counter", "stopwatch") or (_has(normalized, "pomodoro") and _has(normalized, "timer")):
        return [
            _probe(
                "counter-or-time-state-change",
                "Counter or timer controls visibly change numeric/time state.",
                ["activate the primary start/increment control", "activate reset/decrement if present"],
                "Displayed numeric or time state changes after interaction.",
            )
        ]
    if _has_any(normalized, "flashcard", "quiz"):
        return [
            _probe(
                "question-answer-state-change",
                "Question/answer app changes visible state after answer/reveal/next interaction.",
                ["activate answer, reveal, or next controls"],
                "Visible question, answer, score, or feedback changes.",
            )
        ]
    if _has(normalized, "quote") and _has(normalized, "generator"):
        return [
            _probe(
                "generator-visible-change",
                "Generator control changes visible generated content.",
                ["click generate/new/next control"],
                "Visible generated text changes or a generated item appears.",
            )
        ]
    if _has_any(normalized, "mood", "water", "workout") or (_has(normalized, "habit") and _has(normalized, "streak")):
        return [
            _probe(
                "tracker-state-change",
                "Tracker UI records or changes a visible item/count/completion state.",
                ["add, toggle, increment, or select a tracker item"],
                "A count, selected state, streak, or tracked item changes visibly.",
            )
        ]
    if _has_any(normalized, "budget", "expense", "grocery") or (
        _has(normalized, "list") and not _has_any(normalized, "todo", "to-do")
    ):
        return [
            _probe(
                "list-or-ledger-state-change",
                "List or ledger app accepts a new item and shows it or updates totals.",
                ["enter a new item or amount", "click add/save/calculate if present"],
                "The entered item appears or a total changes visibly.",
            )
        ]
    if _has(normalized, "calendar"):
        return [
            _probe(
                "calendar-widget-visible-structure",
                "Calendar widget renders a recognizable month/day grid or date structure.",
                ["open generated widget", "inspect visible dates"],
                "Multiple day/date cells are visible.",
            )
        ]
    if _has(normalized, "palette") and _has(normalized, "picker"):
        return [
            _probe(
                "palette-picker-state-change",
                "Color palette picker exposes swatches and changes selected/generated color state.",
                ["select a swatch or click generate"],
                "Selected/generated color or visible palette state changes.",
            )
        ]
    if _has(normalized, "gallery"):
        return [
            _probe(
                "gallery-navigation-or-selection",
                "Image gallery mockup shows image items and supports selection or navigation when controls exist.",
                ["click thumbnail or next/previous control if present"],
                "Main image, selected item, or navigation state changes; static image items are acceptable for a mockup.",
            )
        ]
    if _has(normalized, "tabs"):
        return [
            _probe(
                "tabs-active-panel-change",
                "Tabs component changes active panel after selecting another tab.",
                ["click a non-active tab"],
                "Active tab or panel content changes.",
            )
        ]
    if _has(normalized, "accordion"):
        return [
            _probe(
                "accordion-expanded-state-change",
                "Accordion expands or collapses FAQ content after interaction.",
                ["click a question/header"],
                "Answer visibility or expanded state changes.",
            )
        ]
    if _has(normalized, "progress") and _has(normalized, "bar"):
        return [
            _probe(
                "progress-bar-visible-value",
                "Progress bar demo renders a visible progress value and changes if controls are present.",
                ["inspect progress value", "activate progress control if present"],
                "A non-empty progress value is visible; controls change it when provided.",
            )
        ]
    if _has(normalized, "star") and _has(normalized, "rating"):
        return [
            _probe(
                "star-rating-selection-change",
                "Star rating widget changes selected rating after clicking a star.",
                ["click a star"],
                "Selected rating count, filled stars, or text feedback changes.",
            )
        ]
    if (_has(normalized, "dark") and _has_any(normalized, "theme", "switcher", "toggle", "mode", "screen", "change")) or (
        _has_any(normalized, "day", "lite", "light", "night", "midnight", "sunrise", "sunset", "dusk", "dawn")
        and _has_any(normalized, "mode", "theme", "switcher", "switch", "toggle", "flips", "swap", "palette")
    ) or (
        _has_any(normalized, "palette", "color", "mood")
        and _has_any(normalized, "switch", "switcher", "toggle", "flipper", "mode")
    ):
        return [
            _probe(
                "theme-computed-color-change",
                "Theme toggle visibly changes computed colors.",
                ["capture computed body colors", "activate theme toggle", "capture computed colors again"],
                "Background or text color changes after the toggle.",
            )
        ]
    if _has_any(normalized, "checklist", "check-list"):
        return [
            _probe(
                "checklist-add-visible-item",
                "Checklist app accepts a typed item and shows it in the visible checklist.",
                ["type a checklist item", "click add/save or press Enter", "toggle/check an item if present"],
                "The entered item appears visibly and checklist state can change after interaction.",
            )
        ]
    if _has_any(normalized, "todo", "to-do"):
        return [
            _probe(
                "todo-add-and-change-item",
                "User can add an item and complete, delete, or otherwise change item state.",
                ["add a new item", "trigger a complete/delete/state-change control"],
                "The new item appears and at least one item state change is observable.",
            )
        ]
    if _has_any(normalized, "weather", "forecast") or (
        _has_any(normalized, "tile", "porch", "balcony", "weekend", "local")
        and _has_any(normalized, "temp", "temperature", "condition", "forecast", "weather")
    ):
        return [
            _probe(
                "weather-card-fields",
                "Weather/forecast artifact renders plausible local demo weather fields, and visible controls change local weather state when present.",
                ["inspect city, temperature, condition, forecast, or status fields", "activate local demo control if present"],
                "City, temperature, condition, forecast, or status text is visible; any provided local control changes visible state.",
            )
        ]
    if _has_any(normalized, "music", "podcast", "audio", "radio", "mixtape") and _has_any(normalized, "player", "mockup", "mock", "deck"):
        return [
            _probe(
                "music-player-control-state",
                "Player mockup exposes track info and play/pause or skip controls that mutate visible state.",
                ["inspect track info", "click play/pause", "click next/skip if present"],
                "Play/pause visibly changes label/status, and next/skip visibly changes track or player state if present.",
            )
        ]
    if _has(normalized, "habit"):
        return [
            _probe(
                "habit-state-change",
                "User can add, complete, edit, remove, or otherwise change habit state.",
                ["inspect for input/buttons/checkboxes", "add or toggle a habit"],
                "Habit state changes after user action; static hard-coded habits are not enough.",
            )
        ]
    if _has_any(normalized, "notes", "note", "scratchpad", "jot", "memo") and _has_any(normalized, "app", "application", "tool", "pad", "board"):
        return [
            _probe(
                "notes-create-edit-visible-note",
                "User can create, edit, or save note text and the actual typed note remains visible in a note/list/card area.",
                ["type note text", "save/add/edit the note", "inspect visible saved notes"],
                "Entered note text remains visible in the app artifact; a saved-status message alone is not enough.",
            )
        ]
    if (
        _has_any(normalized, "password", "passphrase", "phrase")
        and _has_any(normalized, "checker", "strength", "tool", "meter", "safety", "gauge", "strong")
    ) or (_has_any(normalized, "safety", "strength", "strong") and _has_any(normalized, "gauge", "meter", "checker", "phrase", "passphrase")):
        return [
            _probe(
                "password-strength-feedback-change",
                "Entered password/passphrase updates local visible strength feedback through input event handling.",
                ["type a weak password/passphrase", "type a stronger password/passphrase"],
                "Strength text, class, color, or status changes between weak and stronger inputs.",
            )
        ]
    if _has_any(normalized, "drawing", "draw", "doodle", "sketch", "paint", "finger-paint", "finger paint") and _has_any(normalized, "pad", "canvas", "app", "board", "thing"):
        return [
            _probe(
                "drawing-surface-changes",
                "Pointer or mouse interaction draws on a canvas or equivalent visible surface.",
                ["drag on the drawing surface"],
                "Canvas pixels or equivalent drawing marks change after the drag; static canvas markup is not enough.",
            )
        ]
    if _has_any(normalized, "homepage", "home page") and _has_any(normalized, "agent", "lab", "exper"):
        return [
            _probe(
                "homepage-visible-intent",
                "Homepage visible text identifies agent lab experiments.",
                ["open generated homepage", "inspect visible body text"],
                "Visible text includes agent/lab/experiment intent.",
            )
        ]
    return []


def _preview_requirement(artifact_class: str, behavior_required: bool) -> str:
    if not behavior_required:
        return "A later verifier must define artifact readiness for this artifact."
    if artifact_class in {"html_static_page", "static_ui_artifact", ""}:
        return "Openable HTML artifact is required before behavior can be evaluated."
    if artifact_class == "markdown_document":
        return "Markdown is not sufficient for an interactive app behavior contract."
    return "Usable generated artifact is required before behavior can be evaluated."


def _generic_interactive_requirement(criteria: list[dict[str, Any]]) -> str:
    if not criteria:
        return ""
    return (
        "Interactive static UI artifacts must include visible state mutation tied to the behavior contract; "
        "static controls, decorative DOM, and unchanged labels are not enough."
    )


def _generic_behavior_requirement_examples() -> list[str]:
    return [
        "timer/countdown: Start uses local interval/state mutation and visible time/count text changes after start",
        "bill/tip/splitter/calculator: entered numbers visibly update result",
        "checklist/list/notes: entered text appears visibly after add/save",
        "theme/toggle/day/night/dusk/dawn/palette: computed class/color/theme state visibly changes",
        "weather/player/tracker/password/passphrase/canvas: the primary control visibly changes state, feedback, track/status, or pixels",
    ]


def _probe(
    probe_id: str,
    acceptance_criterion: str,
    observable_actions: list[str],
    expected_observation: str,
) -> dict[str, Any]:
    return {
        "probe_id": probe_id,
        "acceptance_criterion": acceptance_criterion,
        "observable_actions": observable_actions,
        "expected_observation": expected_observation,
        "minimum_proof_tier": 2,
    }


def _has(normalized: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", normalized) is not None


def _has_any(normalized: str, *terms: str) -> bool:
    return any(_has(normalized, term) for term in terms)
