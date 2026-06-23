from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from source_proxy.diagnostics.status_codes import FailureClass


Severity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class AntiCheatViolation:
    detector_id: str
    violation_code: str
    message: str
    failure_class: FailureClass | None = None
    severity: Severity = "error"
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failure_class"] = self.failure_class.value if self.failure_class else None
        return payload


@dataclass(frozen=True)
class AntiCheatReport:
    status: Literal["pass", "fail"]
    violations: tuple[AntiCheatViolation, ...]
    checked_detector_ids: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "violations": [violation.to_dict() for violation in self.violations],
            "checked_detector_ids": list(self.checked_detector_ids),
        }
