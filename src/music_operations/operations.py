"""Core music-processing operations invoked by the CLI and the monitor.

Each public function in this module is a *pure* operation that does not read
config itself; callers are responsible for supplying resolved paths and
options.  This makes every operation trivially testable and independently
invokable from the Rust subprocess bridge.
"""

import subprocess
from logging import getLogger
from pathlib import Path
from shutil import copyfile
from typing import Optional

from music_operations import music_logging

logger = getLogger(__name__)
music_logging.setup_logger(logger)


def run_anthemscore(
    music_file: str,
    output_dir: str,
    anthem_cli_path: str,
    anthem_cli_options: str = "--headless",
) -> bool:
    """Transcribe *music_file* to MusicXML + ASDT using AnthemScore.

    Skips transcription if the output directory already exists (idempotent).

    Args:
        music_file: Absolute path to the source ``.wav`` file.
        output_dir: Root directory under which per-song subdirectories are
            created (one subdirectory per stem name).
        anthem_cli_path: Absolute path to the AnthemScore CLI executable.
        anthem_cli_options: Extra CLI flags forwarded to AnthemScore
            (default: ``"--headless"``).

    Returns:
        ``True`` when transcription ran, ``False`` when skipped (already done).

    Raises:
        ValueError: When *music_file* is not a supported audio format.
        subprocess.CalledProcessError: When AnthemScore exits non-zero.
    """
    if not any(music_file.lower().endswith(ext) for ext in (".wav",)):
        raise ValueError(f"Unsupported audio format: {music_file!r}")

    output_anthem_directory = Path(output_dir) / Path(music_file).stem
    output_anthem_base = output_anthem_directory / Path(music_file).stem

    if output_anthem_directory.exists():
        logger.warning("Skipping %s. It already exists.", output_anthem_base)
        return False

    output_anthem_directory.mkdir(parents=True, exist_ok=True)

    cmd = [
        anthem_cli_path,
        anthem_cli_options,
        "--asdt",
        str(output_anthem_base.with_suffix(".asdt")),
        "--musicxml",
        str(output_anthem_base.with_suffix(".xml")),
        music_file,
    ]
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)

    copyfile(music_file, output_anthem_base.with_suffix(".wav"))
    logger.info("Generated %s", output_anthem_directory)
    return True


def run_repomix(
    input_path: str,
    output_dir: str,
    repomix_home: Optional[str] = None,
) -> bool:
    """Run Repomix on *input_path* and write output to *output_dir*.

    Args:
        input_path: File or directory to pack with Repomix.
        output_dir: Directory where the Repomix output file is written.
        repomix_home: Optional path to the Repomix executable or home
            directory.  Falls back to ``repomix`` on ``$PATH``.

    Returns:
        ``True`` on success.

    Raises:
        subprocess.CalledProcessError: When Repomix exits non-zero.
    """
    repomix_bin = repomix_home if repomix_home else "repomix"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cmd = [repomix_bin, "--output", str(output_path), input_path]
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    return True
