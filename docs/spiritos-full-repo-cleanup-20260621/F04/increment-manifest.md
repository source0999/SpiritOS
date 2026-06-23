# F04 Increment Manifest

| Increment | Title | Source files (<=12) | Status | Commit |
|---|---|---|---|---|
| 4.1 | generic decomposer + validator + unseen tests | `source_proxy/decision/packet_decomposition.py`, `source_proxy/decision/packet_templates/__init__.py`, `source_proxy/tests/test_packet_decomposition.py` | COMPLETE | pending commit |
| 4.2 | prompt_packet dry-run wiring + API passthrough | `source_proxy/decision/prompt_packet.py`, `source_proxy/api/decision.py`, `source_proxy/tests/test_packet_decomposition.py` | COMPLETE | pending commit |

Repair attempts used: 1. Manual diff inspection caught and removed accidental non-prompt-packet API spillover before commit.
