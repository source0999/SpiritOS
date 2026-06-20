# Tests Added

Updated `source_proxy/tests/test_plan3_durable_execution.py`.

Required coverage added:

- policy proof fails if `latest_consumer_event_id` is missing.
- policy proof fails if the consumer event is in a different trace.
- policy proof passes when same-trace consumer evidence exists.
- recovery proof fails if `latest_consumer_event_id` is missing.
- recovery proof fails if duplicate action prevention is missing.
- recovery proof passes when same-trace consumer evidence exists.
- repair proof fails if explicit verifier failure event is missing.
- repair proof fails if repair/reverify lacks downstream consumer evidence.
- repair proof fails if consumer event is in a different trace.
- repair proof passes when failure -> repair -> reverify -> consumer exists in the same trace.
- helper rejects missing policy consumer, missing recovery consumer, missing repair failure event, and missing repair consumer.
