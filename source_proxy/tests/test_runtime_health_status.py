from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.runtime_status import router as runtime_status_router
from source_proxy.decision import runtime_health


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(runtime_status_router)
    return TestClient(app)


def _go_payload() -> dict[str, object]:
    return {
        "status": "GO",
        "service": "source-proxy",
        "timestamp": "2026-06-19T00:00:00Z",
        "checks": {
            "api": {"status": "GO", "details": "ok"},
            "next": {"status": "GO", "url": runtime_health.NEXT_ADMIN_URL, "http_status": 200, "latency_ms": 1},
            "ollama": {"status": "GO", "url": runtime_health.OLLAMA_TAGS_URL, "http_status": 200, "loaded_models": []},
            "watchers": {"status": "GO", "timer": {"status": "GO"}, "latest_logs": []},
            "git_authority": {"status": "GO", "dirty_source_proxy": False, "staged_files": 0},
            "failed_units": {"status": "GO", "units": []},
            "recent_crash_signals": {"status": "GO", "signal_count": 0},
        },
        "valid_liveness_endpoints": runtime_health.VALID_LIVENESS_ENDPOINTS,
        "invalid_legacy_health_endpoints": [],
        "notes": [],
    }


def test_health_routes_return_status_payload() -> None:
    with mock.patch(
        "source_proxy.api.runtime_status.build_runtime_health_status",
        return_value=_go_payload(),
    ):
        client = _client()
        for path in ("/health", "/v1/health", "/v1/runtime/status"):
            response = client.get(path)
            assert response.status_code == 200
            payload = response.json()
            assert payload["service"] == "source-proxy"
            assert payload["status"] == "GO"
            assert "/health" in payload["valid_liveness_endpoints"]
            assert "/v1/runtime/status" in payload["valid_liveness_endpoints"]


def test_next_check_handles_200() -> None:
    with mock.patch(
        "source_proxy.decision.runtime_health._http_json_or_text",
        return_value={
            "http_status": 200,
            "latency_ms": 12,
            "json": None,
            "error": None,
            "details": "request completed",
        },
    ):
        payload = runtime_health.check_next()

    assert payload["status"] == "GO"
    assert payload["http_status"] == 200
    assert payload["latency_ms"] == 12


def test_next_check_timeout_is_no_go_without_exception() -> None:
    with mock.patch(
        "source_proxy.decision.runtime_health._http_json_or_text",
        return_value={
            "http_status": None,
            "latency_ms": 2000,
            "json": None,
            "error": "timeout",
            "details": "request failed: timeout",
        },
    ):
        payload = runtime_health.check_next()

    assert payload["status"] == "NO_GO"
    assert payload["http_status"] is None
    assert "timeout" in payload["details"]


def test_ollama_check_handles_tags_and_ps() -> None:
    def fake_http(url: str, **_: object) -> dict[str, object]:
        if url.endswith("/api/tags"):
            return {
                "http_status": 200,
                "latency_ms": 4,
                "json": {"models": [{"name": "qwen2.5-coder:7b"}, {"model": "hermes4:latest"}]},
                "error": None,
                "details": "request completed",
            }
        return {
            "http_status": 200,
            "latency_ms": 2,
            "json": {"models": [{"name": "qwen2.5-coder:7b"}]},
            "error": None,
            "details": "request completed",
        }

    with mock.patch("source_proxy.decision.runtime_health._http_json_or_text", side_effect=fake_http):
        payload = runtime_health.check_ollama()

    assert payload["status"] == "GO"
    assert payload["model_count"] == 2
    assert payload["models"] == ["qwen2.5-coder:7b", "hermes4:latest"]
    assert payload["loaded_models"] == ["qwen2.5-coder:7b"]


def test_watcher_check_active_timer_and_latest_logs() -> None:
    with TemporaryDirectory() as temp_dir:
        log = Path(temp_dir) / "spiritos-host-health-snapshot.sh.2026.log"
        log.write_text("not read by status endpoint", encoding="utf-8")
        with mock.patch(
            "source_proxy.decision.runtime_health._systemctl_value",
            side_effect=[
                {"status": "GO", "unit": "spiritos-health-snapshot.timer", "state": "active"},
                {"status": "GO", "unit": "spiritos-health-snapshot.timer", "state": "enabled"},
                {"status": "GO", "unit": "spiritos-boot-postmortem.service", "state": "enabled"},
            ],
        ):
            payload = runtime_health.check_watchers(log_root=temp_dir)

    assert payload["status"] == "GO"
    assert payload["latest_logs"]
    assert payload["latest_logs"][0]["path"].endswith(".log")


def test_watcher_check_missing_systemctl_is_partial_when_logs_exist() -> None:
    with TemporaryDirectory() as temp_dir:
        (Path(temp_dir) / "watcher.log").write_text("metadata only", encoding="utf-8")
        with mock.patch(
            "source_proxy.decision.runtime_health._systemctl_value",
            return_value={"status": "UNKNOWN", "unit": "x", "state": None},
        ):
            payload = runtime_health.check_watchers(log_root=temp_dir)

    assert payload["status"] == "PARTIAL_GO"


def test_failed_units_summarizes_unit_names_only() -> None:
    result = runtime_health.CommandResult(
        returncode=0,
        stdout="mnt-spirit\\x2dprojects.mount loaded failed failed /mnt/spirit-projects\ncasaos.service loaded failed failed CasaOS\n",
        stderr="",
    )
    with mock.patch("source_proxy.decision.runtime_health.shutil.which", return_value="/bin/systemctl"), mock.patch(
        "source_proxy.decision.runtime_health._run_command",
        return_value=result,
    ):
        payload = runtime_health.check_failed_units()

    assert payload["status"] == "PARTIAL_GO"
    assert payload["units"] == ["mnt-spirit\\x2dprojects.mount", "casaos.service"]
    assert "/mnt/spirit-projects" not in str(payload)


def test_git_authority_no_go_for_dirty_source_proxy() -> None:
    result = runtime_health.CommandResult(
        returncode=0,
        stdout=" M source_proxy/main.py\x00",
        stderr="",
    )
    with mock.patch("source_proxy.decision.runtime_health.shutil.which", return_value="/usr/bin/git"), mock.patch(
        "source_proxy.decision.runtime_health._run_command",
        return_value=result,
    ):
        payload = runtime_health.check_git_authority()

    assert payload["status"] == "NO_GO"
    assert payload["dirty_source_proxy"] is True
    assert payload["dirty_source_proxy_count"] == 1


def test_git_authority_partial_for_unrelated_dirty_files() -> None:
    result = runtime_health.CommandResult(
        returncode=0,
        stdout=" M package.json\x00?? docs/evidence/example.txt\x00",
        stderr="",
    )
    with mock.patch("source_proxy.decision.runtime_health.shutil.which", return_value="/usr/bin/git"), mock.patch(
        "source_proxy.decision.runtime_health._run_command",
        return_value=result,
    ):
        payload = runtime_health.check_git_authority()

    assert payload["status"] == "PARTIAL_GO"
    assert payload["dirty_source_proxy"] is False
    assert payload["package_config_runtime_dirty_count"] == 1


def test_overall_status_is_truthful_not_always_go() -> None:
    checks = {
        "api": {"status": "GO"},
        "next": {"status": "GO"},
        "ollama": {"status": "GO"},
        "watchers": {"status": "GO"},
        "git_authority": {"status": "PARTIAL_GO"},
        "failed_units": {"status": "GO"},
        "recent_crash_signals": {"status": "GO"},
    }

    assert runtime_health._overall_status(checks) == "PARTIAL_GO"

    checks["git_authority"] = {"status": "NO_GO"}
    assert runtime_health._overall_status(checks) == "NO_GO"


def test_runtime_status_does_not_expose_secret_shaped_values() -> None:
    with mock.patch.dict(
        "os.environ",
        {"SOURCE_PROXY_TOKEN": "super-secret-token-value", "PASSWORD": "do-not-show"},
        clear=False,
    ), mock.patch("source_proxy.decision.runtime_health.check_next", return_value={"status": "GO"}), mock.patch(
        "source_proxy.decision.runtime_health.check_ollama",
        return_value={"status": "GO"},
    ), mock.patch(
        "source_proxy.decision.runtime_health.check_watchers",
        return_value={"status": "GO"},
    ), mock.patch(
        "source_proxy.decision.runtime_health.check_git_authority",
        return_value={"status": "GO"},
    ), mock.patch(
        "source_proxy.decision.runtime_health.check_failed_units",
        return_value={"status": "GO", "units": []},
    ), mock.patch(
        "source_proxy.decision.runtime_health.check_recent_crash_signals",
        return_value={"status": "GO"},
    ):
        payload = runtime_health.build_runtime_health_status()

    rendered = str(payload)
    assert "super-secret-token-value" not in rendered
    assert "do-not-show" not in rendered
    assert "PASSWORD" not in rendered
    assert "SOURCE_PROXY_TOKEN" not in rendered
