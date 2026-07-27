from qualification_fixture.config import load_config
from qualification_fixture.diagnostics import diagnostic_payload


def test_config_precedence_and_redaction() -> None:
    config = load_config({"log_level": "warning", "secret": "nope"}, {"QF_LOG_LEVEL": "debug", "QF_SECRET": "x"})
    assert config["log_level"] == "debug"
    assert "secret" not in config
    assert diagnostic_payload(config)["sources"]["log_level"] == "env"
