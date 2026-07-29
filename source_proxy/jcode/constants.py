"""Sealed authority constants for the Gate 2-J.9 JCode qualification dispatcher.

These values are sealed by the campaign authority architect from current repository
source, the live model registry, current executor implementations, existing campaign
policy, Dell host capabilities, prior qualification evidence, and the frozen-benchmark
and safety/authority invariants. They are the single source of truth the dispatcher
consumes; nothing here grants JCode execution authority. JCode remains disabled.

Canonical machine-readable companions live under
``docs/architecture/jcode-qualification/gate_2j_9_*.json``.
"""
from __future__ import annotations

# --- Identity / schemas -----------------------------------------------------

GATE_2J_9_CONSTANTS_SCHEMA_VERSION = "source-proxy.gate-2j-9-authority-constants/v1"
CAMPAIGN_ID = "campaign-2-j"
GATE_ID = "2-J.9"
GATE_2J_9A_ID = "2-J.9A"

QUALIFICATION_SCHEMA_VERSION = "coding.jcode-qualification/v1"
REQUEST_ENVELOPE_SCHEMA_VERSION = "coding.jcode-execution-request/v1"
RESULT_ENVELOPE_SCHEMA_VERSION = "coding.jcode-execution-result/v1"
EVENT_SCHEMA_VERSION = "source-proxy.jcode-event/v1"
CONTEXT_SCHEMA_VERSION = "source-proxy.jcode-qualification-context-packet/v1"
ADAPTER_VERSION = "jcode-qualification-adapter/v1"
EXECUTOR_ID = "candidate.jcode-executor"
HARNESS_ID = "SpiritOS-Source-Proxy/CodingOrchestrator"
HARNESS_VERSION = "coding-orchestrator/v2"

# --- JCode binary / source (attested) ---------------------------------------

JCODE_SOURCE_COMMIT = "2444e7b6bc80d421ae3ee404081bdb41150a1830"
JCODE_BINARY_SHA256 = "2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6"
JCODE_VERSION = "0.58.51-dev"
JCODE_BINARY_PATH = (
    "/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode"
)

# --- Campaign anchors -------------------------------------------------------

QUALIFICATION_BASE_COMMIT = "1641ddb1c71e6b364e98aa9aeff4b4719627d926"
CAMPAIGN_2_ACCEPTANCE_COMMIT = "17f3ce8739192e5c91534dc7ddde1086e83d5e0e"

# --- Provider / model (Decision 3) ------------------------------------------

PROVIDER_PROFILE_ID = "spiritos-qualification"
INFERENCE_BRIDGE_ID = "sealed-loopback-inference-bridge/v1"
PERMITTED_INFERENCE_ENDPOINT = "http://127.0.0.1:11434/api/generate"
PERMITTED_REGISTRY_ENDPOINT = "http://127.0.0.1:11434/api/tags"
# NOTE: the Gate 2-J.8.5 packet referenced http://127.0.0.1:4000/v1 as the
# jcode_sandbox_endpoint. A 2026-07-29 live probe found nothing listening on
# port 4000. The sealed profile binds to the live 11434 endpoint; the 4000
# slot is retracted.
RETRACTED_DEAD_ENDPOINT = "http://127.0.0.1:4000/v1"
CREDENTIAL_POLICY = "none"
FALLBACK_POLICY = "none"

# --- Lane binding (Decision 1) ----------------------------------------------

LANE_EXECUTOR_BASELINE = (
    "source_proxy/decision/tool_action_loop.py::run_bounded_agent_loop "
    "via source_proxy/decision/human_messy_homepage.py::run_human_messy_homepage"
)
LANE_EXECUTOR_JCODE = (
    "source_proxy/jcode/dispatcher.py launching sealed JCode CLI per task"
)

PRIMARY_MODEL = "qwen2.5-coder:7b"
PRIMARY_MODEL_DIGEST = (
    "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364"
)
CHALLENGER_MODEL = "qwen2.5-coder:14b"
CHALLENGER_MODEL_DIGEST = (
    "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849"
)
MODEL_QUANTIZATION = "Q4_K_M"
CONTEXT_LIMIT_TOKENS = 32768

GENERATION_PARAMETERS = {"max_tokens": 4096, "seed": 7, "temperature": 0}

LANE_BINDINGS = {
    "A": {"role": "existing_baseline_primary", "model": PRIMARY_MODEL,
          "harness": LANE_EXECUTOR_BASELINE},
    "B": {"role": "jcode_primary", "model": PRIMARY_MODEL,
          "harness": LANE_EXECUTOR_JCODE},
    "C": {"role": "existing_baseline_challenger", "model": CHALLENGER_MODEL,
          "harness": LANE_EXECUTOR_BASELINE},
    "D": {"role": "jcode_challenger", "model": CHALLENGER_MODEL,
          "harness": LANE_EXECUTOR_JCODE},
}

# --- Terminal authority -----------------------------------------------------

PERMITTED_TERMINAL_CLASSES = (
    "COMPLETED_VERIFIED",
    "ESCALATION_CONTEXT_PACK_READY",
    "BLOCKED_OR_DEGRADED_TRUTHFULLY",
)
JCODE_TERMINAL_AUTHORITY = False

# --- Real-model probe (Decision 5) ------------------------------------------

REAL_MODEL_PROBE_DECISION = "DEFERRED_TO_GATE_2J_9H"
REAL_MODEL_REQUEST_PERMITTED_AT_2J_9F = False
