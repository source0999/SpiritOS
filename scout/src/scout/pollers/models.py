from dataclasses import dataclass


@dataclass(frozen=True)
class PollResult:
    status: str
    source_uri: str
    events_added: int = 0
    reason: str | None = None
    pause_source: bool = False
    next_run_epoch: int | None = None
