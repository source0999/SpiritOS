from dataclasses import dataclass


TERMINAL = {"completed", "failed", "cancelled"}


@dataclass
class TaskState:
    status: str = "running"

    def transition(self, status: str) -> str:
        self.status = status
        return self.status
