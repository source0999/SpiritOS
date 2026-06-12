# Qwen Ollama Runtime Diagnostic Closeout

Final status: RUNTIME_CONFLICT_DETECTED
Qwen installed: True
Duplicate Ollama warning: True
System Ollama running: True
Docker Ollama running: True
CLI cold time: 119.934s
CLI warm time: 119.925s
HTTP cold time: 29.939s
HTTP warm time: 0.226s
GPU used: True
Swap pressure: True
Suspected blocker: Duplicate Docker/system Ollama services are running. Qwen cold/warm CLI startup is too slow for readiness gates; readiness harness blocked before Aider. Swap is in use, which may contribute to slow model load.
Recommended fix: OPERATOR_DECISION_REQUIRED
Aider should be rerun: True
Recommended Aider timeout: 300s
Clean command: python3 scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py --clean
