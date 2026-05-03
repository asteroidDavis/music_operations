"""Entry-point for the ``music-operations`` CLI.

Designed to be invoked by both humans and the Rust PersonalMusicBrowser
subprocess bridge::

    music-operations --operation anthemscore \\
        --input-file /path/to/recording.wav \\
        --output-dir /path/to/exports

All paths that can be supplied via the INI config can also be passed as
explicit CLI arguments.  When both sources provide the *same* key and their
values differ, the command exits with a non-zero status (conflict error).
"""

import argparse
import sys
from logging import getLogger
from multiprocessing import Pool, cpu_count
from typing import List, NoReturn, Optional

from music_operations import music_logging
from music_operations.config import (
    DEFAULT_CONFIG_FILE,
    AppConfig,
    ConfigConflictError,
    read_config,
)
from music_operations.operations import run_anthemscore, run_repomix
from music_operations.pedal import Pedal

logger = getLogger(__name__)
music_logging.setup_logger(logger)

SUPPORTED_OPERATIONS = ("anthemscore", "repomix", "monitor")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="music-operations",
        description=(
            "Music file operations toolkit.  Can be called directly or "
            "spawned as a subprocess by the Rust PersonalMusicBrowser worker."
        ),
    )

    parser.add_argument(
        "--operation",
        required=True,
        choices=SUPPORTED_OPERATIONS,
        help=(
            "Operation to perform: "
            "'anthemscore' – transcribe WAV → MusicXML/ASDT; "
            "'repomix' – pack a directory with Repomix; "
            "'monitor' – start the USB pedal monitor (interactive)."
        ),
    )
    parser.add_argument(
        "--input-file",
        dest="input_file",
        metavar="PATH",
        help="Input file (required for 'anthemscore' and 'repomix').",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        metavar="DIR",
        help=(
            "Output directory.  Overrides 'destination_directory' from the "
            "INI config; conflicts raise an error."
        ),
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_FILE,
        metavar="FILE",
        help=f"INI config file (default: {DEFAULT_CONFIG_FILE}).",
    )
    parser.add_argument(
        "--anthemscore-home",
        dest="anthemscore_home",
        metavar="PATH",
        help=(
            "Path to the AnthemScore executable.  Overrides 'anthem_cli_path' "
            "from the INI config; conflicts raise an error."
        ),
    )
    parser.add_argument(
        "--repomix-home",
        dest="repomix_home",
        metavar="PATH",
        help="Path to the Repomix executable or home directory.",
    )
    return parser


def _run_anthemscore_batch(
    music_files: List[str],
    output_dir: str,
    cfg: AppConfig,
) -> NoReturn:
    """Run AnthemScore on *music_files* using a multiprocessing pool.

    Args:
        music_files: List of WAV file paths to process.
        output_dir: Root destination directory.
        cfg: Resolved application configuration.
    """
    args = [
        (f, output_dir, cfg.anthem_cli_path, cfg.anthem_cli_options)
        for f in music_files
    ]
    with Pool(cpu_count()) as pool:
        results = pool.starmap(run_anthemscore, args)

    imported = sum(results)
    skipped = len(results) - imported
    logger.info("Imported %d/%d", imported, len(music_files))
    logger.info("Skipped  %d/%d", skipped, len(music_files))


def _run_monitor(cfg: AppConfig) -> NoReturn:  # pragma: no cover
    """Start the interactive USB-pedal monitor with a directory picker.

    Args:
        cfg: Resolved application configuration.
    """
    import json
    from tkinter import Tk, filedialog

    pedal = Pedal(cfg.music_directory_globs)
    root = Tk()
    output_dir = filedialog.askdirectory(
        initialdir=cfg.destination_directory, mustexist=True
    )
    root.destroy()

    if not output_dir:
        logger.error("No output directory selected. Exiting.")
        sys.exit(1)

    logger.info("Monitoring %s", json.dumps(pedal.music_files))
    _run_anthemscore_batch(pedal.music_files, output_dir, cfg)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry-point.

    Args:
        argv: Argument list (defaults to :data:`sys.argv`).

    Returns:
        Exit code (0 = success, non-zero = failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = read_config(
            file=args.config,
            anthemscore_home=args.anthemscore_home,
            repomix_home=args.repomix_home,
            output_dir=args.output_dir,
        )
    except ConfigConflictError as exc:
        logger.error("Configuration conflict: %s", exc)
        return 2
    except FileNotFoundError as exc:
        logger.error("Config file error: %s", exc)
        return 2

    operation = args.operation

    if operation == "anthemscore":
        if not args.input_file:
            logger.error("--input-file is required for the 'anthemscore' operation.")
            return 1
        output = args.output_dir or cfg.destination_directory
        if not output:
            logger.error(
                "--output-dir (or destination_directory in config) is required "
                "for the 'anthemscore' operation."
            )
            return 1
        try:
            run_anthemscore(
                music_file=args.input_file,
                output_dir=output,
                anthem_cli_path=cfg.anthem_cli_path,
                anthem_cli_options=cfg.anthem_cli_options,
            )
        except ValueError as exc:
            logger.error("Invalid input: %s", exc)
            return 1
        except Exception as exc:  # noqa: BLE001
            logger.error("AnthemScore failed: %s", exc)
            return 1

    elif operation == "repomix":
        if not args.input_file:
            logger.error("--input-file is required for the 'repomix' operation.")
            return 1
        output = args.output_dir or cfg.destination_directory
        if not output:
            logger.error(
                "--output-dir (or destination_directory in config) is required "
                "for the 'repomix' operation."
            )
            return 1
        try:
            run_repomix(
                input_path=args.input_file,
                output_dir=output,
                repomix_home=cfg.repomix_home,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Repomix failed: %s", exc)
            return 1

    elif operation == "monitor":
        _run_monitor(cfg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
