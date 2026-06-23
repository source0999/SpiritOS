from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from source_proxy.verification.anticheat.detectors import AntiCheatDetector, DETECTORS
from source_proxy.verification.anticheat.types import AntiCheatReport, AntiCheatViolation

"""Runs anti-cheat detectors as an audit layer over already-produced evidence.

The registry reports contradictions and laundering risks; it does not repair,
reinterpret, or upgrade the underlying verdict.
"""


class AntiCheatRegistry:
    def __init__(self, detectors: Iterable[AntiCheatDetector] = DETECTORS) -> None:
        self._detectors = tuple(detectors)

    @property
    def detector_ids(self) -> tuple[str, ...]:
        return tuple(detector.detector_id for detector in self._detectors)

    def run(self, payload: dict[str, Any]) -> AntiCheatReport:
        violations: list[AntiCheatViolation] = []
        for detector in self._detectors:
            violation = detector.run(payload)
            if violation is not None:
                violations.append(violation)
        return AntiCheatReport(
            status="fail" if violations else "pass",
            violations=tuple(violations),
            checked_detector_ids=self.detector_ids,
        )


def detector_registry() -> AntiCheatRegistry:
    return AntiCheatRegistry()


def run_anticheat_detectors(payload: dict[str, Any]) -> AntiCheatReport:
    return detector_registry().run(payload)
