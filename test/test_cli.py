"""Tests for music_operations.cli."""

import configparser
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from music_operations.cli import _run_anthemscore_batch, build_parser, main
from music_operations.config import AppConfig


@pytest.fixture()
def ini_file(tmp_path: Path) -> Path:
    """Write a minimal INI config and return its path."""
    cfg = configparser.ConfigParser()
    cfg["host"] = {
        "anthem_cli_path": "/usr/bin/anthem",
        "destination_directory": str(tmp_path / "out"),
    }
    cfg["analysis"] = {"anthem_cli_options": "--headless"}
    cfg["pedal"] = {"music_directory_globs": str(tmp_path / "**" / "*.wav")}
    path = tmp_path / "test.ini"
    with open(path, "w") as fh:
        cfg.write(fh)
    return path


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


def test_parser_required_operation() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])
    assert (
        exc_info.value.code != 0
    ), "Expected non-zero exit when --operation is missing"


@pytest.mark.parametrize("operation", ["anthemscore", "repomix", "monitor"])
def test_parser_valid_operations(operation: str) -> None:
    parser = build_parser()
    args = parser.parse_args(["--operation", operation])
    assert (
        args.operation == operation
    ), f"Expected {operation!r}, got {args.operation!r}"


def test_parser_invalid_operation() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--operation", "invalid_op"])
    assert exc_info.value.code != 0


def test_parser_all_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--operation",
            "anthemscore",
            "--input-file",
            "/in/song.wav",
            "--output-dir",
            "/out",
            "--config",
            "/cfg/file.ini",
            "--anthemscore-home",
            "/opt/anthem",
            "--repomix-home",
            "/opt/repomix",
        ]
    )
    assert args.input_file == "/in/song.wav"
    assert args.output_dir == "/out"
    assert args.config == "/cfg/file.ini"
    assert args.anthemscore_home == "/opt/anthem"
    assert args.repomix_home == "/opt/repomix"


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------


def test_main_missing_input_file_returns_1(ini_file: Path) -> None:
    exit_code = main(["--operation", "anthemscore", "--config", str(ini_file)])
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"


def test_main_anthemscore_dispatched(ini_file: Path, tmp_path: Path) -> None:
    wav = tmp_path / "song.wav"
    wav.write_bytes(b"\x00" * 100)
    out = tmp_path / "out"
    out.mkdir()

    with patch("music_operations.cli.run_anthemscore", return_value=True) as mock_op:
        exit_code = main(
            [
                "--operation",
                "anthemscore",
                "--config",
                str(ini_file),
                "--input-file",
                str(wav),
                "--output-dir",
                str(out),
            ]
        )

    assert exit_code == 0, f"Expected 0, got {exit_code}"
    mock_op.assert_called_once()
    call_kwargs = mock_op.call_args
    assert str(wav) in call_kwargs.args or str(wav) == call_kwargs.kwargs.get(
        "music_file"
    ), f"Expected input file to be passed, got {call_kwargs}"


def test_main_repomix_dispatched(ini_file: Path, tmp_path: Path) -> None:
    input_dir = tmp_path / "project"
    input_dir.mkdir()

    with patch("music_operations.cli.run_repomix", return_value=True) as mock_op:
        exit_code = main(
            [
                "--operation",
                "repomix",
                "--config",
                str(ini_file),
                "--input-file",
                str(input_dir),
            ]
        )

    assert exit_code == 0, f"Expected 0, got {exit_code}"
    mock_op.assert_called_once()


def test_main_config_conflict_returns_2(ini_file: Path, tmp_path: Path) -> None:
    """A ConfigConflictError from read_config maps to exit code 2."""
    from music_operations.config import ConfigConflictError

    with patch(
        "music_operations.cli.read_config",
        side_effect=ConfigConflictError("anthem_cli_path conflict"),
    ):
        exit_code = main(
            [
                "--operation",
                "anthemscore",
                "--config",
                str(ini_file),
                "--input-file",
                str(tmp_path / "song.wav"),
            ]
        )
    assert exit_code == 2, f"Expected exit code 2 (conflict), got {exit_code}"


def test_main_missing_config_file_returns_2(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--operation",
            "anthemscore",
            "--config",
            str(tmp_path / "nonexistent.ini"),
            "--input-file",
            str(tmp_path / "song.wav"),
        ]
    )
    assert exit_code == 2, f"Expected exit code 2 (missing config), got {exit_code}"


def test_main_anthemscore_exception_returns_1(ini_file: Path, tmp_path: Path) -> None:
    wav = tmp_path / "bad.wav"
    wav.write_bytes(b"\x00")
    out = tmp_path / "out"
    out.mkdir()

    with patch(
        "music_operations.cli.run_anthemscore",
        side_effect=RuntimeError("anthem crashed"),
    ):
        exit_code = main(
            [
                "--operation",
                "anthemscore",
                "--config",
                str(ini_file),
                "--input-file",
                str(wav),
                "--output-dir",
                str(out),
            ]
        )

    assert (
        exit_code == 1
    ), f"Expected exit code 1 on subprocess failure, got {exit_code}"


def test_main_anthemscore_value_error_returns_1(ini_file: Path, tmp_path: Path) -> None:
    """ValueError from run_anthemscore (bad format) maps to exit code 1."""
    out = tmp_path / "out"
    out.mkdir()

    with patch(
        "music_operations.cli.run_anthemscore",
        side_effect=ValueError("Unsupported audio format"),
    ):
        exit_code = main(
            [
                "--operation",
                "anthemscore",
                "--config",
                str(ini_file),
                "--input-file",
                str(tmp_path / "song.mp3"),
                "--output-dir",
                str(out),
            ]
        )

    assert exit_code == 1, f"Expected exit code 1 for ValueError, got {exit_code}"


def test_main_anthemscore_missing_output_returns_1(tmp_path: Path) -> None:
    """Missing output dir (no CLI flag, empty INI) → exit code 1."""
    cfg = configparser.ConfigParser()
    cfg["host"] = {"anthem_cli_path": "/bin/anthem", "destination_directory": ""}
    cfg["analysis"] = {"anthem_cli_options": ""}
    cfg["pedal"] = {"music_directory_globs": ""}
    ini = tmp_path / "empty.ini"
    with open(ini, "w") as fh:
        cfg.write(fh)

    exit_code = main(
        [
            "--operation",
            "anthemscore",
            "--config",
            str(ini),
            "--input-file",
            str(tmp_path / "song.wav"),
        ]
    )
    assert exit_code == 1, f"Expected exit code 1 (no output dir), got {exit_code}"


def test_main_repomix_missing_input_returns_1(ini_file: Path) -> None:
    exit_code = main(["--operation", "repomix", "--config", str(ini_file)])
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"


def test_main_repomix_missing_output_returns_1(tmp_path: Path) -> None:
    """Repomix with no output dir (no CLI flag, empty INI) → exit code 1."""
    cfg = configparser.ConfigParser()
    cfg["host"] = {"anthem_cli_path": "/bin/anthem", "destination_directory": ""}
    cfg["analysis"] = {"anthem_cli_options": ""}
    cfg["pedal"] = {"music_directory_globs": ""}
    ini = tmp_path / "empty.ini"
    with open(ini, "w") as fh:
        cfg.write(fh)

    exit_code = main(
        [
            "--operation",
            "repomix",
            "--config",
            str(ini),
            "--input-file",
            str(tmp_path / "project"),
        ]
    )
    assert exit_code == 1, f"Expected exit code 1 (no output dir), got {exit_code}"


def test_main_repomix_exception_returns_1(ini_file: Path, tmp_path: Path) -> None:
    with patch(
        "music_operations.cli.run_repomix",
        side_effect=RuntimeError("repomix crashed"),
    ):
        exit_code = main(
            [
                "--operation",
                "repomix",
                "--config",
                str(ini_file),
                "--input-file",
                str(tmp_path / "project"),
            ]
        )
    assert exit_code == 1, f"Expected exit code 1 on repomix failure, got {exit_code}"


def test_main_monitor_dispatches(ini_file: Path) -> None:
    with patch("music_operations.cli._run_monitor") as mock_monitor:
        exit_code = main(["--operation", "monitor", "--config", str(ini_file)])
    assert exit_code == 0, f"Expected 0, got {exit_code}"
    mock_monitor.assert_called_once()


# ---------------------------------------------------------------------------
# _run_anthemscore_batch unit tests
# ---------------------------------------------------------------------------


def _make_cfg(tmp_path: Path) -> AppConfig:
    return AppConfig(
        music_directory_globs="",
        anthem_cli_path="/bin/anthem",
        destination_directory=str(tmp_path / "out"),
        anthem_cli_options="--headless",
    )


def test_run_anthemscore_batch_empty(tmp_path: Path) -> None:
    cfg = _make_cfg(tmp_path)
    mock_pool = MagicMock()
    mock_pool.__enter__ = MagicMock(return_value=mock_pool)
    mock_pool.__exit__ = MagicMock(return_value=False)
    mock_pool.starmap.return_value = []
    with patch("music_operations.cli.Pool", return_value=mock_pool):
        _run_anthemscore_batch([], str(tmp_path / "out"), cfg)
    mock_pool.starmap.assert_called_once()


def test_run_anthemscore_batch_counts(tmp_path: Path) -> None:
    cfg = _make_cfg(tmp_path)
    files = [str(tmp_path / f"s{i}.wav") for i in range(3)]
    mock_pool = MagicMock()
    mock_pool.__enter__ = MagicMock(return_value=mock_pool)
    mock_pool.__exit__ = MagicMock(return_value=False)
    mock_pool.starmap.return_value = [True, False, True]
    with patch("music_operations.cli.Pool", return_value=mock_pool):
        _run_anthemscore_batch(files, str(tmp_path / "out"), cfg)
    mock_pool.starmap.assert_called_once()
