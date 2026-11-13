"""Tests for music_operations.availability."""

import json
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from music_operations.availability import (
    anthemscore_status,
    list_operations,
    monitor_status,
    repomix_status,
)
from music_operations.cli import main
from music_operations.config import AppConfig


def _cfg(anthem: str = "", repomix=None) -> AppConfig:
    return AppConfig(
        music_directory_globs="",
        anthem_cli_path=anthem,
        destination_directory="",
        anthem_cli_options="",
        repomix_home=repomix,
    )


def _exe(tmp_path: Path, name: str) -> str:
    path = tmp_path / name
    path.write_text("#!/bin/sh\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def test_anthemscore_unsupported_arch() -> None:
    status = anthemscore_status(_cfg("/opt/a"), "Linux", "aarch64")
    assert not status.available
    assert "no build for Linux aarch64" in status.reason


def test_anthemscore_missing_binary() -> None:
    status = anthemscore_status(_cfg("/nonexistent/anthem"), "Linux", "x86_64")
    assert not status.available
    assert "not installed" in status.reason


def test_anthemscore_no_config() -> None:
    assert not anthemscore_status(None, "Linux", "x86_64").available


def test_anthemscore_available(tmp_path: Path) -> None:
    status = anthemscore_status(_cfg(_exe(tmp_path, "AnthemScore")), "Linux", "x86_64")
    assert status.available and status.reason == ""


def test_repomix_from_config(tmp_path: Path) -> None:
    assert repomix_status(_cfg(repomix=_exe(tmp_path, "repomix"))).available


def test_repomix_missing() -> None:
    with patch("music_operations.availability.shutil.which", return_value=None):
        status = repomix_status(None)
    assert not status.available
    assert status.reason == "repomix not found"


def test_monitor_headless_linux() -> None:
    status = monitor_status("Linux", {})
    assert not status.available
    assert "display" in status.reason


def test_monitor_without_tkinter() -> None:
    with patch.dict("sys.modules", {"tkinter": None}):
        status = monitor_status("Darwin", {})
    assert not status.available
    assert "tkinter" in status.reason


def test_monitor_with_display() -> None:
    with patch.dict("sys.modules", {"tkinter": object()}):
        assert monitor_status("Linux", {"DISPLAY": ":0"}).available


def test_list_operations_names() -> None:
    ops = list_operations(None, "Linux", "aarch64", {})
    assert [o["name"] for o in ops] == ["anthemscore", "repomix", "monitor"]
    assert set(ops[0]) == {"name", "available", "reason"}


def test_list_operations_defaults() -> None:
    assert len(list_operations(None)) == 3


def test_cli_list_operations_json(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    rc = main(["--list-operations", "--config", str(tmp_path / "missing.ini")])
    assert rc == 0
    ops = json.loads(capsys.readouterr().out)
    assert {o["name"] for o in ops} == {"anthemscore", "repomix", "monitor"}


def test_cli_list_operations_with_config(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    ini = tmp_path / "c.ini"
    ini.write_text(
        "[host]\nanthem_cli_path = /x\ndestination_directory = /o\n"
        "[analysis]\nanthem_cli_options = --headless\n"
        "[pedal]\nmusic_directory_globs = /m\n"
    )
    assert main(["--list-operations", "--config", str(ini)]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "anthemscore"


def test_cli_list_and_operation_conflict() -> None:
    with pytest.raises(SystemExit):
        main(["--list-operations", "--operation", "repomix"])
