from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from source_proxy.decision.human_messy_homepage import run_human_messy_homepage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    workspace = run_dir / "workspace"
    score = run_human_messy_homepage(
        prompt=args.prompt,
        workspace=workspace,
        receipt_path=run_dir / "receipt.json",
        score_path=run_dir / "score.json",
        transcript_path=run_dir / "transcript.txt",
        diff_path=run_dir / "workspace.diff",
        preview_url="",
        mode="product",
    )
    (run_dir / "generation-result.json").write_text(
        json.dumps({"prompt": args.prompt, "score": score}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
