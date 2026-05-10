from __future__ import annotations

import csv
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GpuMetricsUnavailable(RuntimeError):
    """Raised when local NVIDIA VRAM metrics cannot be read."""


@dataclass(frozen=True)
class VramMetrics:
    used_gb: float
    total_gb: float
    source: str

    def as_healthcheck_payload(self) -> dict[str, str]:
        return {
            "vram_used": _format_gb(self.used_gb),
            "vram_total": _format_gb(self.total_gb),
        }


def collect_vram_metrics() -> VramMetrics:
    try:
        return _collect_with_nvml()
    except Exception as nvml_error:
        try:
            return _collect_with_nvidia_smi()
        except Exception as smi_error:
            raise GpuMetricsUnavailable(
                "Unable to read NVIDIA VRAM metrics with NVML or nvidia-smi. "
                f"NVML error: {nvml_error}. nvidia-smi error: {smi_error}."
            ) from smi_error or nvml_error


def _collect_with_nvml() -> VramMetrics:
    import pynvml

    pynvml.nvmlInit()
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return VramMetrics(
            used_gb=_bytes_to_gb(memory.used),
            total_gb=_bytes_to_gb(memory.total),
            source="nvml",
        )
    finally:
        pynvml.nvmlShutdown()


def _collect_with_nvidia_smi() -> VramMetrics:
    smi_path = _find_nvidia_smi()
    if smi_path is None:
        raise FileNotFoundError("nvidia-smi executable was not found.")

    result = subprocess.run(
        [
            str(smi_path),
            "--query-gpu=memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    first_row = next(csv.reader(result.stdout.splitlines()))
    used_mib, total_mib = (float(value.strip()) for value in first_row[:2])
    return VramMetrics(
        used_gb=_mib_to_gb(used_mib),
        total_gb=_mib_to_gb(total_mib),
        source="nvidia-smi",
    )


def _find_nvidia_smi() -> Path | None:
    path_match = shutil.which("nvidia-smi")
    if path_match:
        return Path(path_match)

    candidates = [
        Path("C:/Windows/System32/nvidia-smi.exe"),
        Path("C:/Program Files/NVIDIA Corporation/NVSMI/nvidia-smi.exe"),
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _bytes_to_gb(value: int) -> float:
    return value / 1024 / 1024 / 1024


def _mib_to_gb(value: float) -> float:
    return value / 1024


def _format_gb(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return f"{int(rounded)} GB"
    return f"{rounded} GB"
