# Reference Patterns

These are comparison references only; the pivot must adapt current SpiritOS machinery first and must not install a major framework unless Plan 0 proves adaptation is worse and Britton approves.

- Microsoft Magentic-One: Orchestrator, Task Ledger, Progress Ledger, specialist assignment, stall detection, replanning. Sources: https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/ and https://arxiv.org/abs/2411.04468.
- LangGraph: checkpoint persistence, thread-scoped state, long-term stores, durable human interrupts. Sources: https://docs.langchain.com/oss/python/langgraph/persistence and https://docs.langchain.com/oss/python/langgraph/interrupts.
- OpenTelemetry / W3C Trace Context: trace context propagation across services and nodes. Sources: https://opentelemetry.io/docs/concepts/context-propagation/ and https://www.w3.org/TR/trace-context/.
- Open Policy Agent: structured policy decisions separated from enforcement. Source: https://openpolicyagent.org/docs.
- OpenHands SDK: immutable typed events as an append-only agent execution and integration log. Source: https://docs.openhands.dev/sdk/arch/events.
- Aider repository map: tree-sitter symbol/signature context instead of dumping whole repositories. Sources: https://aider.chat/docs/repomap.html and https://aider.chat/2023/10/22/repomap.html.
- Letta memory: always-present memory blocks, archival retrieval memory, and shared writable memory. Sources: https://docs.letta.com/guides/core-concepts/memory/memory-blocks/, https://docs.letta.com/guides/core-concepts/memory/archival-memory/, and https://docs.letta.com/guides/core-concepts/memory/shared-memory/.

SpiritOS mapping rules: reuse existing long-running task state, Cartographer workflow state, workflow event ledger, central gate, Scout, Obsidian, worker contracts, model lanes, and verifier/repair machinery before proposing new frameworks or parallel orchestrators.
