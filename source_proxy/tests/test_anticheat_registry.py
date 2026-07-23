from __future__ import annotations

import importlib.util
from pathlib import Path

import source_proxy.verification.anticheat.detectors as detector_module

from source_proxy.verification.anticheat import detector_registry, run_anticheat_detectors
from source_proxy.verification.anticheat.legacy import copied_legacy_anticheat_verdict, new_registry_parity_verdict


NEGATIVE_CASES = {
    "canned_output_detected": {"canned_output": True, "output_origin": "canned template"},
    "static_source_labeled_live": {"research_label": "live", "research_origin": "static"},
    "route_only_integration_proof": {"integration_claim": True, "route_status_checked": True, "behavior_exercised": False},
    "status_ping_only_behavior_proof": {"behavior_claim": True, "status_ping_only": True},
    "repo_context_labeled_internet": {"internet_research_claim": True, "source_origin": "repo"},
    "fixture_or_mock_labeled_live": {"live_evidence_claim": True, "evidence_origin": "mock"},
    "preview_labeled_executed": {"executed_claim": True, "artifact_kind": "preview"},
    "fallback_counted_as_primary_success": {"fallback_used": True, "reported_success_path": "primary"},
    "renderer_created_substance": {"substantive_decision_source": "renderer"},
    "manual_pass_or_json_flip": {"manual_json_edit": True, "final_status": "PASS"},
    "consumer_event_does_not_launder_canned_output": {"canned_output": True, "consumer_event_id": "evt-123"},
    "unavailable_provider_reported_success": {"provider_available": False, "provider_result": "success"},
    "summary_pass_raw_failure": {"summary_status": "PASS", "raw_status": "FAIL"},
    "benchmark_specific_runtime_branch": {"runtime_code": "if prompt_id == 'A2': return expected_answer"},
    "test_only_path_labeled_production": {"runtime_integration": True, "implementation_origin": "test_only"},
}


def test_registry_imports_independently_and_lists_detectors() -> None:
    registry = detector_registry()

    assert len(registry.detector_ids) >= 15
    assert "canned_output" in registry.detector_ids
    assert "fallback_labeled_primary_success" in registry.detector_ids


def test_each_negative_case_is_flagged() -> None:
    for expected_code, payload in NEGATIVE_CASES.items():
        report = run_anticheat_detectors(payload)
        codes = {violation.violation_code for violation in report.violations}
        assert report.status == "fail"
        assert expected_code in codes


def test_positive_grounded_evidence_passes_without_false_positive() -> None:
    payload = {
        "raw_evidence_path": "docs/evidence/run/raw.json",
        "provider_available": True,
        "provider_result": "used",
        "tool_status": "used",
        "validator_result": "passed",
        "summary_status": "PASS",
        "raw_status": "PASS",
        "behavior_claim": True,
        "behavior_exercised": True,
        "fallback_used": False,
        "research_label": "live",
        "research_origin": "provider_query",
        "live_evidence_claim": True,
        "evidence_origin": "live_tool",
        "substantive_decision_source": "model",
    }

    report = run_anticheat_detectors(payload)

    assert report.status == "pass"
    assert report.violations == ()


def test_benchmark_runtime_detector_flags_structural_label_branches() -> None:
    malicious_branches = (
        "if prompt_id == 'A2': return expected_answer",
        'if ("A5" === promptId) { return expectedAnswer; }',
        'if\n(promptId === "A5") return expectedAnswer;',
        'switch (promptId) {\ncase "A9": return expectedAnswer;\n}',
        'switch (promptId)\n{\ncase "A9": return expectedAnswer;\n}',
        'match prompt_id:\n    case "4R":\n        return expected_answer',
        'if prompt_id in {"A2", "A5"}:\n    return expected_answer',
        'if prompt_id == \\\n    "A2":\n    return expected_answer',
        'switch (suite) {\ncase "set A": return knownResult;\n}',
        'if status == "known benchmark":\n    return known_result',
        (
            "if prompt_id"
            + " and value" * 260
            + " == 'A2': return expected_answer"
        ),
        (
            'benchmark_label = "A2"\n'
            "if prompt_id == benchmark_label: return expected_answer"
        ),
        (
            'benchmark_label: str = "A2"\n'
            "if prompt_id == benchmark_label: return expected_answer"
        ),
        (
            'benchmark_label = ("A2")\n'
            "if prompt_id == benchmark_label: return expected_answer"
        ),
        (
            'const benchmarkLabel: string = "A2";\n'
            "if (promptId === benchmarkLabel) return expectedAnswer;"
        ),
        (
            "benchmark_label = \\\n"
            '    "A2"\n'
            "if prompt_id == benchmark_label: return expected_answer"
        ),
        (
            'benchmark_label = "A2"\n'
            "benchmark_label: str\n"
            "if prompt_id == benchmark_label: return expected_answer"
        ),
        (
            'guard: if (prompt_id === "A2") '
            "{ return expectedAnswer; }"
        ),
        'if request["prompt_id"] == "A2": return expected_answer',
        'if payload.get("task_id") == "A2": return expected_answer',
        'if record["benchmark"] == "A2": return expected_answer',
    )

    for runtime_code in malicious_branches:
        report = run_anticheat_detectors({"runtime_code": runtime_code})
        assert report.status == "fail"
        assert "benchmark_specific_runtime_branch" in {
            violation.violation_code for violation in report.violations
        }


def test_benchmark_runtime_detector_rejects_incidental_label_substrings() -> None:
    legitimate_code = (
        "if delta2_enabled:\n    return calculate_value()",
        "if profile_a2_suffix:\n    return calculate_value()",
        'profile = "profile_a2_suffix"\nif profile:\n    return calculate_value(profile)',
        'if label == "A2-archive":\n    return calculate_value(label)',
        "# if prompt_id == 'A2': return expected_answer\nreturn calculate_value()",
        'message = "if prompt_id == \'A2\': return expected_answer"\nreturn message',
        'if value:\n    return "A2"',
        'if (value) return "A2";',
        'if enabled { return "A2"; }',
        'if value == "some a2 value":\n    return calculate_value(value)',
        'if grade == "A2":\n    return calculate_value(grade)',
        'switch (grade) {\ncase "A2": return calculateValue(grade);\n}',
        'case("A2")\nreturn calculate_value()',
        'match = (prompt_id, "A2")',
        'switch = [prompt_id, "A2"]',
        'match(prompt_id, "A2")',
        'switch(prompt_id, "A2")',
        'def match(prompt_id="A2"):\n    return prompt_id',
        'def case(prompt_id="A2"):\n    return prompt_id',
        'async def case(prompt_id="A2"):\n    return prompt_id',
        (
            'function switch(promptId = "A2") '
            "{ return promptId; }"
        ),
        'if request["grade"] == "A2": return calculate_value()',
    )

    for runtime_code in legitimate_code:
        report = run_anticheat_detectors({"runtime_code": runtime_code})
        assert report.status == "pass"
        assert report.violations == ()


def test_benchmark_runtime_detector_uses_candidate_side_of_unified_diff() -> None:
    removed_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1 +1 @@
-if prompt_id == "A2": return expected_answer
+return calculate_value()
"""
    header_only_label = """diff --git a/case/A2.py b/case/A2.py
--- a/case/A2.py
+++ b/case/A2.py
@@ -1 +1 @@
-return old_value
+return calculate_value()
"""
    added_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1 +1 @@
-return calculate_value()
+if prompt_id == "A2": return expected_answer
"""
    added_label_in_context_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,4 +1,5 @@
 if prompt_id in {
+    "A2",
     "fallback",
 }:
     return calculate_value()
"""
    unrelated_addition_near_context_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,3 +1,4 @@
 if prompt_id == "A2":
     return expected_answer
+unrelated_value = calculate_value()
 return unrelated_value
"""
    added_binding_for_context_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,2 +1,3 @@
+benchmark_label = "A2"
 if prompt_id == benchmark_label:
     return expected_answer
"""
    unrelated_addition_near_bound_context_branch = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,3 +1,4 @@
 benchmark_label = "A2"
 if prompt_id == benchmark_label:
     return expected_answer
+unrelated_value = calculate_value()
"""
    unrelated_addition_after_unbraced_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,2 +1,3 @@
 if (promptId === "A2")
   calculateValue();
+unrelatedValue();
"""
    unrelated_addition_after_nested_unbraced_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,3 +1,4 @@
 if (promptId === "A2")
   if (enabled)
     calculateValue();
+unrelatedValue();
"""
    replaced_context_branch_body = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,2 +1,2 @@
 if prompt_id == "A2":
-    return calculate_value()
+    return expected_answer
"""
    added_context_branch_body = """diff --git a/example.py b/example.py
--- a/example.py
+++ b/example.py
@@ -1,2 +1,3 @@
 if prompt_id == "A2":
+    return expected_answer
     pass
"""
    replaced_allman_context_branch_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,4 +1,4 @@
 if (promptId === "A2")
 {
-  return calculateValue();
+  return expectedAnswer;
 }
"""
    moved_context_branch_closing_brace = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,3 +1,3 @@
 if (promptId === "A2") { return expectedAnswer;
-}
 doSensitiveWork();
+}
"""
    replaced_unbraced_context_branch_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,2 +1,2 @@
 if (promptId === "A2")
-  return calculateValue();
+  return expectedAnswer;
"""
    replaced_nested_unbraced_context_branch_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,3 +1,3 @@
 if (promptId === "A2")
   if (enabled)
-    return calculateValue();
+    return expectedAnswer;
"""
    replaced_nested_else_context_branch_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,5 +1,5 @@
 if (promptId === "A2")
   if (enabled)
     thenBody();
   else
-    return calculateValue();
+    return expectedAnswer;
"""
    replaced_unindented_case_body = """diff --git a/example.js b/example.js
--- a/example.js
+++ b/example.js
@@ -1,4 +1,4 @@
 switch (promptId) {
 case "A2":
-return calculateValue();
+return expectedAnswer;
 }
"""
    replaced_arrow_case_body = """diff --git a/example.java b/example.java
--- a/example.java
+++ b/example.java
@@ -1,4 +1,4 @@
 switch (promptId) {
 case "A2" ->
-  calculateValue();
+  expectedAnswer();
 }
"""

    for legitimate_diff in (
        removed_branch,
        header_only_label,
        unrelated_addition_near_context_branch,
        unrelated_addition_near_bound_context_branch,
        unrelated_addition_after_unbraced_body,
        unrelated_addition_after_nested_unbraced_body,
    ):
        report = run_anticheat_detectors({"runtime_code": legitimate_diff})
        assert report.status == "pass"
        assert report.violations == ()

    for malicious_diff in (
        added_branch,
        added_label_in_context_branch,
        added_binding_for_context_branch,
        replaced_context_branch_body,
        added_context_branch_body,
        replaced_allman_context_branch_body,
        moved_context_branch_closing_brace,
        replaced_unbraced_context_branch_body,
        replaced_nested_unbraced_context_branch_body,
        replaced_nested_else_context_branch_body,
        replaced_unindented_case_body,
        replaced_arrow_case_body,
    ):
        report = run_anticheat_detectors({"runtime_code": malicious_diff})
        assert report.status == "fail"
        assert "benchmark_specific_runtime_branch" in {
            violation.violation_code for violation in report.violations
        }


def test_benchmark_runtime_detector_scans_malformed_clauses_linearly(
    monkeypatch,
) -> None:
    runtime_code = " ".join("if value" for _ in range(8192))
    original = detector_module._branch_clause_span
    clause_scans = 0

    def counted_clause_span(tokens, start):
        nonlocal clause_scans
        clause_scans += 1
        return original(tokens, start)

    monkeypatch.setattr(
        detector_module,
        "_branch_clause_span",
        counted_clause_span,
    )
    report = run_anticheat_detectors({"runtime_code": runtime_code})

    assert clause_scans == 1
    assert report.status == "pass"
    assert report.violations == ()


def test_benchmark_runtime_detector_retains_binding_across_source_segment() -> None:
    filler = "\n".join(
        f"filler_{index} = {index}"
        for index in range(1500)
    )
    runtime_code = (
        'benchmark_label = "A2"\n'
        + filler
        + "\nif prompt_id == benchmark_label: return expected_answer"
    )

    report = run_anticheat_detectors({"runtime_code": runtime_code})

    assert report.status == "fail"
    assert "benchmark_specific_runtime_branch" in {
        violation.violation_code for violation in report.violations
    }


def test_benchmark_runtime_detector_scans_annotation_spans_linearly(
    monkeypatch,
) -> None:
    runtime_code = " ".join(f"x{index}:" for index in range(4096))
    original = detector_module._direct_assignment_shape
    annotation_scans = 0

    def counted_assignment_shape(tokens, index):
        nonlocal annotation_scans
        annotation_scans += 1
        return original(tokens, index)

    monkeypatch.setattr(
        detector_module,
        "_direct_assignment_shape",
        counted_assignment_shape,
    )
    report = run_anticheat_detectors({"runtime_code": runtime_code})

    assert annotation_scans == 1
    assert report.status == "pass"
    assert report.violations == ()


def test_copied_legacy_parity_surface_matches_new_registry() -> None:
    shared_corpus = [
        {},
        {"canned_output": True},
        {"summary_status": "PASS", "raw_status": "FAIL"},
        {"fallback_used": True, "reported_success_path": "primary"},
    ]
    for payload in shared_corpus:
        assert copied_legacy_anticheat_verdict(payload) == new_registry_parity_verdict(payload)


def test_set_a_runner_imports_f2_registry_additively_without_execution() -> None:
    runner = Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py")
    source = runner.read_text()

    assert "f2_anticheat_detector_registry" in source
    assert "from source_proxy.verification.anticheat import detector_registry" in source
    assert importlib.util.find_spec("source_proxy.verification.anticheat") is not None


def test_fake_go_detected_is_not_hardcoded_false_in_new_package() -> None:
    package_root = Path("source_proxy/verification/anticheat")
    text = "\n".join(path.read_text() for path in package_root.glob("*.py"))

    assert "fake_go_detected = False" not in text
    assert "fake_go_detected=False" not in text
