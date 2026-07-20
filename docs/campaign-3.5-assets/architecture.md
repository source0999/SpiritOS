# Campaign 3.5 asset-layer architecture

`source_proxy_coder_backend_100_v1.1` is the immutable public task-definition
layer.  The companion asset layer implements those records without changing
their bytes or semantics.

The harness has four roots.  They must never be nested in one another:

| Root | Contents | Coder access |
| --- | --- | --- |
| public definition | v1.1 task records and published harness contract | read-only only when explicitly supplied |
| private asset store | seed material, oracle profiles, reference transformations, failure injection and scoring inputs | never mounted or indexed |
| fixture root | one disposable repository plus declared tools/services | the only repository exposed to the production coder |
| evidence root | redacted traces, receipts, diffs and independent oracle result | written after execution; no reference patch or raw seed |

The fixture process receives a manifest containing only the fixture root,
baseline tree commitment, allowed paths and execution profile.  The private
asset process owns the seed and private profile.  It passes neither through the
fixture environment, prompt, trace, nor evidence payload.  The two processes
communicate only by a redacted result envelope after the fixture process has
ended.

Boundary assertions are mandatory: the fixture root cannot contain hidden test
paths or private-store paths; private files are mode `0600`, private directories
are mode `0700`; fixture materialization rejects traversal and a target plugin
accepts only a manifest-controlled root and path scope.  Search and retrieval
systems receive only the materialized fixture root, never the private store.

The generated [fixture inventory](../../source_proxy/benchmarks/campaign_3_5_assets/inventory.json)
is derived from the immutable `tasks.json`; it is a readiness record, not a
second task-definition source.
