# Current Research Regression

Live current research:

- Status: `INTEGRATED_LIVE`
- Task: `task_8e88f3a54bc2`
- Provider used: `http://127.0.0.1:8080`
- Scout status: `skipped`
- Scout reason: `scout_research_disabled`
- SearXNG status: `used`
- SearXNG reason: `live_searxng_provider_query_executed`
- Source count: `4`
- Downstream decision: `research_sources_available`
- Downstream state changed: `true`
- Untrusted content marked: `true`
- Consumer: `cartographer_current_research_consumer`
- Consumer event: `consumer_3a8289e42ec6494a`
- Research packet hash: `24107e8056410c9f0dc69702eb99e95f4af2e56586a2c608d51e55b43fa99ad3`

Fail-closed provider diagnostic:

- Explicit provider: `http://127.0.0.1:1`
- Status: `blocked`
- Reason: `searxng_unreachable`
- Provider candidates: `["http://127.0.0.1:1"]`
- Provider URL used: empty
- Source count: `0`

Patch 3 changed explicit provider diagnostics so they do not silently fall back to the healthy default provider.
