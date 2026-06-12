# Aider Readiness Decision

Qwen should be allowed through the Aider test now: True

The readiness gate should not block Aider when qwen2.5-coder:7b is installed and the HTTP API responds within 120 seconds. Treat readiness as diagnostic-only and keep the Aider run capped.

Recommended Aider timeout: 300 seconds.

Qwen runtime stable enough for one Aider run: True

Duplicate Ollama should be cleaned first: True

Reason: Duplicate Docker/system Ollama services are running. Qwen cold/warm CLI startup is too slow for readiness gates; readiness harness blocked before Aider. Swap is in use, which may contribute to slow model load.
