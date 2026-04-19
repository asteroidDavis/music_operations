"""Tests for music_operations.config."""

import configparser
from pathlib import Path

import pytest

from music_operations.config import (
    AppConfig,
    ConfigConflictError,
    read_config,
)


@pytest.fixture()
def ini_file(tmp_path: Path) -> Path:
    """Write a minimal INI config and return its path."""
    cfg = configparser.ConfigParser()
    cfg["host"] = {
        "anthem_cli_path": "/usr/bin/anthem",
        "destination_directory": "/music/out",
    }
    cfg["analysis"] = {"anthem_cli_options": "--headless"}
    cfg["pedal"] = {"music_directory_globs": "/media/USB/**/*.wav"}
    path = tmp_path / "test.ini"
    with open(path, "w") as fh:
        cfg.write(fh)
    return path


def test_read_config_basic(ini_file: Path) -> None:
    result = read_config(str(ini_file))
    assert isinstance(result, AppConfig), f"Expected AppConfig, got {type(result)}"
    assert result.anthem_cli_path == "/usr/bin/anthem"
    assert result.destination_directory == "/music/out"
    assert result.anthem_cli_options == "--headless"
    assert result.music_directory_globs == "/media/USB/**/*.wav"


def test_read_config_cli_override_anthem(ini_file: Path) -> None:
    """CLI --anthemscore-home silently overrides the INI anthem_cli_path."""
    result = read_config(str(ini_file), anthemscore_home="/opt/anthem/bin")
    assert (
        result.anthem_cli_path == "/opt/anthem/bin"
    ), f"Expected CLI override to take effect, got {result.anthem_cli_path!r}"


def test_read_config_cli_override_output_dir(ini_file: Path) -> None:
    """CLI --output-dir silently overrides the INI destination_directory."""
    result = read_config(str(ini_file), output_dir="/tmp/custom_out")
    assert (
        result.destination_directory == "/tmp/custom_out"
    ), f"Expected output_dir override, got {result.destination_directory!r}"


def test_read_config_repomix_home(ini_file: Path) -> None:
    result = read_config(str(ini_file), repomix_home="/opt/repomix")
    assert (
        result.repomix_home == "/opt/repomix"
    ), f"Expected repomix_home to be set, got {result.repomix_home!r}"


def test_resolve_field_cli_conflict_raises() -> None:
    """Two CLI-level values for the same field with different values raises."""
    from music_operations.config import _resolve_field

    with pytest.raises(ConfigConflictError) as exc_info:
        _resolve_field(
            "anthem_cli_path",
            ini_value="/ini/anthem",
            cli_value="/cli/anthem/a",
            extra_cli_value="/cli/anthem/b",
        )
    assert "anthem_cli_path" in str(
        exc_info.value
    ), f"Expected field name in error, got: {exc_info.value}"


def test_resolve_field_cli_conflict_same_value_no_raise() -> None:
    """Two CLI-level values that agree should not raise."""
    from music_operations.config import _resolve_field

    result = _resolve_field(
        "anthem_cli_path",
        ini_value="/ini/anthem",
        cli_value="/same/anthem",
        extra_cli_value="/same/anthem",
    )
    assert result == "/same/anthem", f"Expected '/same/anthem', got {result!r}"


def test_read_config_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        read_config("/nonexistent/path/config.ini")


def test_read_config_cli_wins_over_ini(ini_file: Path) -> None:
    """CLI value always wins over INI, even when they differ."""
    result = read_config(str(ini_file), anthemscore_home="/usr/bin/anthem")
    assert (
        result.anthem_cli_path == "/usr/bin/anthem"
    ), f"Expected CLI value to win, got {result.anthem_cli_path!r}"
