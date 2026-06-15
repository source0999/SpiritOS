from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


LEVEL5_RUNNER_PATH = Path(__file__).resolve().with_name("integrated_level5_runner.py")
spec = importlib.util.spec_from_file_location("integrated_level5_runner", LEVEL5_RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {LEVEL5_RUNNER_PATH}")
level5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(level5)


ALL_PROMPTS: list[dict[str, Any]] = list(level5.level3.PROMPTS)
NOOP_IDS = {"level5-13-noop-honesty", "level5-14-noop-repeat"}
SMOKE_IDS = {
    "level5-01-repo-context-no-web",
    "level5-13-noop-honesty",
    "level5-11-repair-loop",
    "level5-15-env-trap",
    "level5-20-trace-receipt-audit",
}


def _select_prompts(mode: str) -> list[dict[str, Any]]:
    if mode == "noop":
        wanted = NOOP_IDS
    elif mode == "smoke":
        wanted = SMOKE_IDS
    elif mode == "full":
        return ALL_PROMPTS
    else:
        raise SystemExit("Usage: integrated_level5r_runner.py [noop|smoke|full]")
    return [prompt for prompt in ALL_PROMPTS if prompt["prompt_id"] in wanted]


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    level5.level3.PROMPTS = _select_prompts(mode)
    level5.level3.OUT_DIR = Path("docs/evidence/source-proxy-full-integration-pivot/integrated-level-5R")
    level5.level3.OUTPUT_PREFIX = (
        "integrated-level-5R" if mode == "full" else f"integrated-level-5R-{mode}"
    )
    level5.level3.main()


if __name__ == "__main__":
    main()
