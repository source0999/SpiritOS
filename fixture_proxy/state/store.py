class DurableTaskStore:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, object]] = {}

    def create(self, task_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.records[task_id] = dict(payload)
        return self.records[task_id]
