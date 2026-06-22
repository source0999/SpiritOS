from __future__ import annotations

import socket
import subprocess
import urllib.request

from source_proxy.decision.escalation_contract import BrainSwitchEvidence, FailureClass, recommend_brain_switch
from source_proxy.decision.packet_decomposition import (
    decompose_task,
    monolithic_packet_quality,
    normalize_task_shape,
    supported_task_shapes,
)
from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet


def test_all_task_shapes_decompose_and_validate() -> None:
    for shape in supported_task_shapes():
        result = decompose_task(f"Plan a fresh {shape} task for unrelated domain nouns", task_shape=shape)

        assert result.validation_status == "pass"
        assert result.local_only is True
        assert result.provider_call_performed is False
        assert len(result.sub_packets) >= 3


def test_same_shape_with_different_wording_yields_same_family() -> None:
    first = decompose_task("Compare two current deployment tools for a studio workflow")
    second = decompose_task("Which tool should this team use versus the other option for releases?")

    assert first.task_shape == "current_tool_comparison"
    assert first.decomposition_family == second.decomposition_family


def test_benchmark_labels_do_not_change_decomposition_family() -> None:
    neutral = decompose_task("Compare two current tools for deployment checks")
    labeled = decompose_task("A2 A5 A9 Set A 4R7 compare two current tools for deployment checks")

    assert neutral.task_shape == labeled.task_shape
    assert neutral.decomposition_family == labeled.decomposition_family
    assert [packet.packet_id for packet in neutral.sub_packets] == [packet.packet_id for packet in labeled.sub_packets]


def test_sub_packets_serialize_with_evidence_validation_and_failure_classes() -> None:
    result = decompose_task(
        "Prepare a multi-node resource plan for three build machines",
        evidence_ids=("ev-node-1", "ev-node-2"),
    )
    payload = result.to_dict()

    assert payload["sub_packets"]
    for packet in payload["sub_packets"]:
        assert packet["evidence_requirements"]
        assert packet["validation_focus"]
        assert packet["failure_classifications"]
        assert all(isinstance(item, str) for item in packet["failure_classifications"])


def test_decomposition_improves_monolithic_packet_quality_for_holdout_shape() -> None:
    task = "Research and recommend a current database choice using fresh evidence"
    monolithic = monolithic_packet_quality(task)
    decomposed = decompose_task(task)

    assert monolithic["has_independent_validation"] is False
    assert len(decomposed.sub_packets) > monolithic["sub_packet_count"]
    assert decomposed.validation_status == "pass"


def test_f3_local_decomposition_recommendation_triggers_prompt_packet_metadata() -> None:
    verdict = recommend_brain_switch(
        BrainSwitchEvidence(
            task_shape="architecture planning",
            formatting_failures=2,
            failure_classification=FailureClass.MODEL_FORMATTING_FAILURE,
            decomposable=True,
            evidence_ids=("ev-format-1",),
        )
    )
    packet = build_prompt_packet(
        PromptPacketInput(
            task="Create an architecture plan for a queue migration",
            brain_switch_recommendation=verdict.recommendation.value,
            task_shape=verdict.task_shape,
            evidence_ids=verdict.evidence_ids,
        )
    ).as_payload()

    assert packet["local_decomposition"]["task_shape"] == "architecture_planning"
    assert packet["local_decomposition"]["provider_call_performed"] is False
    assert packet["context_metadata"]["local_decomposition_status"] == "pass"


def test_no_provider_network_or_subprocess_call(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("provider/network/subprocess call attempted")

    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(urllib.request, "urlopen", fail)
    monkeypatch.setattr(subprocess, "run", fail)

    result = decompose_task("Create an implementation handoff for a local parser fix")

    assert result.provider_call_performed is False
    assert result.local_only is True


def test_shape_normalization_ignores_benchmark_labels() -> None:
    assert normalize_task_shape(task_shape="A2 current tool comparison") == "current_tool_comparison"
    assert normalize_task_shape(task="A9 Set A implementation handoff for a worker") == "implementation_handoff"
