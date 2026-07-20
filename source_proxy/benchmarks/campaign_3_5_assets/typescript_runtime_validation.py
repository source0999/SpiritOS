"""Compile and execute private TypeScript reference probes in fixture roots."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.core_references import apply_core_reference
from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


TYPESCRIPT_RUNTIME_TASKS = frozenset({"S08", "S10", "M12"})
ROOT = Path(__file__).resolve().parents[3]
TSC = ROOT / "node_modules/.bin/tsc"


def _replace(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if before not in text:
        raise ValueError("campaign_3_5_typescript_reference_baseline_mismatch")
    path.write_text(text.replace(before, after), encoding="utf-8")


def _compile_and_probe(source: Path, expression: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="campaign35-ts-output-") as temporary:
        output = Path(temporary)
        subprocess.run([str(TSC), str(source), "--outDir", str(output), "--target", "es2020", "--module", "commonjs", "--skipLibCheck"], check=True, capture_output=True, text=True)
        compiled = output / source.name.replace(".tsx", ".js").replace(".ts", ".js")
        result = subprocess.run(["node", "-e", f"const m=require({json.dumps(str(compiled))}); process.exit(({expression}) ? 0 : 1);"], capture_output=True, text=True)
        return result.returncode == 0


def apply_typescript_runtime_reference(task_id: str, root: Path) -> None:
    if task_id == "S08":
        apply_core_reference(task_id, root)
    elif task_id == "S10":
        _replace(root / "src/pagination.ts", "return page * pageSize;", "return (page - 1) * pageSize;")
    elif task_id == "M12":
        apply_core_reference(task_id, root)
    else:
        raise ValueError("campaign_3_5_typescript_runtime_task_unknown")


def probe_typescript_runtime(task_id: str, root: Path) -> tuple[bool, str]:
    if task_id == "S08":
        expression = "JSON.stringify(m.redactSecrets({Token:'x',nested:[{apiKey:'y'}]})) === JSON.stringify({Token:'[REDACTED]',nested:[{apiKey:'[REDACTED]'}]})"
        return _compile_and_probe(root / "src/security/redact.ts", expression), "typescript_recursive_redaction"
    if task_id == "S10":
        return _compile_and_probe(root / "src/pagination.ts", "m.offset(1, 25) === 0 && m.offset(2, 25) === 25"), "typescript_pagination"
    if task_id == "M12":
        return _compile_and_probe(root / "packages/worker/src/thumbnail.ts", "m.processThumbnail({id:'a'}).then(x => x.sizes.length === 3 && x.status === 'complete')"), "thumbnail_pipeline"
    return False, "unknown"


def validate_typescript_runtime_references(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if not TSC.is_file():
        raise RuntimeError("campaign_3_5_typescript_compiler_unavailable")
    by_id={task["task_id"]:task for task in tasks}; records=[]
    seed=Campaign35RunSeed(raw=b"campaign35-typescript-runtime".ljust(32,b"0"), commitment="typescript-runtime")
    with tempfile.TemporaryDirectory(prefix="campaign35-typescript-runtime-") as temporary:
        for index, task_id in enumerate(sorted(TYPESCRIPT_RUNTIME_TASKS)):
            task=by_id[task_id]; parent=Path(temporary)/str(index); parent.mkdir(); local=derive_task_seed(seed,task_id,task["fixture"])
            fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local))
            apply_typescript_runtime_reference(task_id,fixture.fixture_root)
            passed,category=probe_typescript_runtime(task_id,fixture.fixture_root)
            records.append({"task_id":task_id,"passed":passed,"category":category})
    return {"schema_version":"campaign-3.5-typescript-runtime-validation/v1","passed":all(row["passed"] for row in records),"task_count":len(records),"tasks":records,"validated_task_ids":[row["task_id"] for row in records if row["passed"]]}
