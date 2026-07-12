# ADR 0006: Retain Scout until contract stability

Decision: Scout stays inside SpiritOS until its contract is stable.
Reason: premature extraction would turn an interface uncertainty into deployment drift.
Consequences: Campaign 1 defines contracts and profiles but does not split the service.
Campaign 2 dependency: independently verified stable Scout contract.
Revision condition: a verified runtime boundary requires an earlier extraction.