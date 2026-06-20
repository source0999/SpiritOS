# Operator Check Patch

Updated `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/operator-check.sh`.

The operator remains read-only and now fails on:

- missing policy `latest_consumer_event_id`, `consumer_event_id`, `consumer_subsystem`, or same-trace consumer event.
- missing policy blocked decision, blocked action, or `mutation_prevented=true`.
- missing recovery `latest_consumer_event_id`, `consumer_event_id`, same-trace consumer event, or duplicate action prevention.
- missing repair explicit verifier failure event.
- missing repair event, reverify event, final result, repair attempt count, bounded max attempts, consumer event, or same-trace consumer event.
- JSON syntax errors.
- Plan 4 artifacts.

It no longer treats top-level GO booleans as sufficient proof.
