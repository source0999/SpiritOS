# Source Proxy Basic Backend 10 v1

This directory is the frozen **public** contract for the Campaign 3.5
human-prompt comprehension gate.  It contains ordinary prompt templates,
fixture scope, public test commands, and trace requirements.  It intentionally
contains no hidden checks, expected patches, reference implementations, raw
seeds, or oracle details.

The harness derives each rendered fixture from a private 256-bit run secret
using the domain-separated HMAC contract in `seed-contract.json`.  Only the
rendered names and a one-way seed commitment may cross into the disposable
repository.  Production Source Proxy receives the rendered human prompt, the
repository, normal tools, public test output, and normal diagnostics only.

Task IDs are harness bookkeeping and are not passed to production dispatch.
Private assets live in
`source_proxy/benchmarks/campaign_3_5_basic_assets/`; production modules must
not import that package.
