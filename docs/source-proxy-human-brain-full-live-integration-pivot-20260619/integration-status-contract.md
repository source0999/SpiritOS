# Integration Status Contract

Allowed statuses: `LIVE_INTEGRATED`, `LIVE_OBSERVATIONAL_DECISIVE`, `PARTIAL_UNCONSUMED`, `PREVIEW_ONLY`, `ADVISORY_ONLY`, `READ_ONLY_ONLY`, `DORMANT`, `MISSING`, and `NOT_APPLICABLE`.

GO requires causal identifiers: `task_id`, `trace_id`, `invocation_event_id`, `consumer_event_id`, `consumer_subsystem`, and task-state fields changed. No invocation event means no GO. No downstream consumer event means no GO.
