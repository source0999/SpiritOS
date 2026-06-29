from __future__ import annotations

import unittest

from source_proxy.benchmarks.model_lane_benchmark import (
    BenchmarkTask,
    aggregate_results,
    build_recommendation_matrix,
    parse_file_blocks,
    parse_json_response,
    score_result,
)


class ModelLaneBenchmarkParserTests(unittest.TestCase):
    def test_parse_json_response_accepts_strict_object(self) -> None:
        parsed = parse_json_response('{"status":"NO-GO","blockers":["missing evidence"]}')

        self.assertTrue(parsed["success"])
        self.assertTrue(parsed["clean"])
        self.assertEqual(parsed["parsed"]["status"], "NO-GO")

    def test_parse_json_response_extracts_object_but_marks_unclean(self) -> None:
        parsed = parse_json_response('Here: {"status":"NO-GO","blockers":[]} done')

        self.assertTrue(parsed["success"])
        self.assertFalse(parsed["clean"])
        self.assertEqual(parsed["parsed"]["status"], "NO-GO")

    def test_parse_file_blocks_rejects_missing_blocks(self) -> None:
        parsed = parse_file_blocks("no file here")

        self.assertFalse(parsed["success"])
        self.assertIn("no file blocks found", parsed["errors"])

    def test_parse_file_blocks_detects_markdown_fence_inside_block(self) -> None:
        parsed = parse_file_blocks('<file path="x.ts">\n```ts\nexport {}\n```\n</file>')

        self.assertTrue(parsed["success"])
        self.assertFalse(parsed["clean"])
        self.assertTrue(any("markdown fence" in error for error in parsed["errors"]))


class ModelLaneBenchmarkScoringTests(unittest.TestCase):
    def test_score_rewards_parseable_honest_output(self) -> None:
        task = BenchmarkTask(
            role="critique_risk_verifier",
            task_id="fake_go",
            title="Fake GO",
            parser="json",
            prompt="",
            model_keys=("hermes",),
            expected_fields=("verdict", "blockers"),
            positive_terms=("NO-GO", "evidence"),
        )
        raw = '{"verdict":"NO-GO","blockers":["missing evidence"],"evidence_required":["browser proof"]}'
        parsed_meta = parse_json_response(raw)
        scores = score_result(
            task,
            raw,
            parsed_meta["parsed"],
            parsed_meta,
            [],
            9000,
            {"status": "used", "gpus": [{"memory_total_mb": 12288, "memory_used_mb": 6000}]},
            [],
        )

        self.assertEqual(scores["parseability_contract_compliance"], 5)
        self.assertEqual(scores["failure_honesty"], 5)
        self.assertGreaterEqual(scores["latency_vram_practicality"], 4)

    def test_recommendation_keeps_current_when_ornith_has_blockers(self) -> None:
        aggregate = aggregate_results(
            [
                {
                    "role": "coder_patch_author",
                    "model_key": "qwen",
                    "status": "used",
                    "parse_success": True,
                    "hard_blockers": [],
                    "total_score": 4.2,
                    "latency_ms": 1000,
                },
                {
                    "role": "coder_patch_author",
                    "model_key": "ornith",
                    "status": "used",
                    "parse_success": True,
                    "hard_blockers": ["git apply --check failed"],
                    "total_score": 4.5,
                    "latency_ms": 1000,
                },
            ]
        )
        matrix = build_recommendation_matrix(aggregate)

        self.assertEqual(matrix["coder_patch_author"]["ornith_action"], "NEEDS_MORE_TESTS")
        self.assertIn("hard blocker", matrix["coder_patch_author"]["reason"])


if __name__ == "__main__":
    unittest.main()
