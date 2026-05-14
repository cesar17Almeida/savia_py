from pathlib import Path

import pytest
from pydantic import ValidationError

from savia import config


def test_load_returns_defaults_when_path_is_none():
    cfg = config.load(None)
    assert cfg.log_level == "INFO"
    assert cfg.storage.db_path == Path("./savia.db")
    assert cfg.storage.retention_hours == 48


def test_load_parses_toml(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        'log_level = "DEBUG"\n'
        "[storage]\n"
        'db_path = "/tmp/savia-test.db"\n'
        "retention_hours = 24\n"
    )
    cfg = config.load(cfg_file)
    assert cfg.log_level == "DEBUG"
    assert cfg.storage.db_path == Path("/tmp/savia-test.db")
    assert cfg.storage.retention_hours == 24


def test_partial_toml_uses_defaults(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('log_level = "WARNING"\n')
    cfg = config.load(cfg_file)
    assert cfg.log_level == "WARNING"
    assert cfg.storage.retention_hours == 48


def test_invalid_log_level_rejected(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('log_level = "VERBOSE"\n')
    with pytest.raises(ValidationError):
        config.load(cfg_file)


def test_negative_retention_rejected(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("[storage]\nretention_hours = -1\n")
    with pytest.raises(ValidationError):
        config.load(cfg_file)


def test_unknown_field_rejected(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text("typo_field = 42\n")
    with pytest.raises(ValidationError):
        config.load(cfg_file)
