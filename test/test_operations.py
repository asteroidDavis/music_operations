"""Tests for music_operations.operations."""

from pathlib import Path
from unittest.mock import patch

import pytest

from music_operations.operations import run_anthemscore, run_repomix


# ---------------------------------------------------------------------------
# run_anthemscore
# ---------------------------------------------------------------------------


def test_run_anthemscore_skips_existing(tmp_path: Path) -> None:
    wav = tmp_path / "song.wav"
    wav.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "output"
    song_dir = output_dir / "song"
    song_dir.mkdir(parents=True)

    with patch("subprocess.run") as mock_run:
        result = run_anthemscore(str(wav), str(output_dir), "/bin/anthem")

    assert result is False, f"Expected False (skip), got {result!r}"
    mock_run.assert_not_called()


def test_run_anthemscore_runs_and_copies(tmp_path: Path) -> None:
    wav = tmp_path / "mysong.wav"
    wav.write_bytes(b"\x00" * 100)
    output_dir = tmp_path / "output"

    with patch("subprocess.run") as mock_run:
        result = run_anthemscore(str(wav), str(output_dir), "/bin/anthem", "--headless")

    assert result is True, f"Expected True (ran), got {result!r}"
    mock_run.assert_called_once()
    cmd = mock_run.call_args.args[0]
    assert "/bin/anthem" in cmd, f"Expected anthem path in cmd, got {cmd}"
    assert "--headless" in cmd, f"Expected --headless in cmd, got {cmd}"
    assert str(wav) in cmd, f"Expected input wav in cmd, got {cmd}"

    copied_wav = output_dir / "mysong" / "mysong.wav"
    assert copied_wav.exists(), f"Expected copied WAV at {copied_wav}"


def test_run_anthemscore_invalid_format(tmp_path: Path) -> None:
    mp3 = tmp_path / "song.mp3"
    mp3.write_bytes(b"\x00")
    with pytest.raises(ValueError, match="Unsupported audio format"):
        run_anthemscore(str(mp3), str(tmp_path / "out"), "/bin/anthem")


@pytest.mark.parametrize("options", ["--headless", "--no-gpu --headless"])
def test_run_anthemscore_options_forwarded(tmp_path: Path, options: str) -> None:
    wav = tmp_path / "track.wav"
    wav.write_bytes(b"\x00" * 50)
    output_dir = tmp_path / "out"

    with patch("subprocess.run") as mock_run:
        run_anthemscore(str(wav), str(output_dir), "/bin/anthem", options)

    cmd = mock_run.call_args.args[0]
    assert options in cmd, f"Expected options {options!r} in cmd, got {cmd}"


# ---------------------------------------------------------------------------
# run_repomix
# ---------------------------------------------------------------------------


def test_run_repomix_calls_subprocess(tmp_path: Path) -> None:
    input_dir = tmp_path / "project"
    input_dir.mkdir()
    output_dir = tmp_path / "repomix_out"

    with patch("subprocess.run") as mock_run:
        result = run_repomix(str(input_dir), str(output_dir))

    assert result is True, f"Expected True, got {result!r}"
    mock_run.assert_called_once()
    cmd = mock_run.call_args.args[0]
    assert "repomix" in cmd[0], f"Expected 'repomix' binary in cmd, got {cmd}"
    assert str(input_dir) in cmd, f"Expected input_dir in cmd, got {cmd}"


def test_run_repomix_custom_home(tmp_path: Path) -> None:
    input_dir = tmp_path / "src"
    input_dir.mkdir()
    output_dir = tmp_path / "out"

    with patch("subprocess.run") as mock_run:
        run_repomix(str(input_dir), str(output_dir), repomix_home="/opt/repomix/bin")

    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "/opt/repomix/bin", f"Expected custom repomix bin, got {cmd[0]!r}"


def test_run_repomix_creates_output_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "project"
    input_dir.mkdir()
    output_dir = tmp_path / "deeply" / "nested" / "out"

    with patch("subprocess.run"):
        run_repomix(str(input_dir), str(output_dir))

    assert output_dir.exists(), f"Expected output_dir to be created at {output_dir}"
