# ADR 0003: Server-owned capabilities and approvals

Decision: SpiritFlix mutations, Cartographer writes, and Design writeback require server-owned identity, capability, approval binding, and receipts.
Reason: request fields and preview state are not authority.
Consequences: GET stays non-mutating; rejected requests fail closed and leave no state change.
Campaign 2 dependency: contract migration may replace internal transport only, not this authority rule.
Revision condition: none without an approved replacement security model.