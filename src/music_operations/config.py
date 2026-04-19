"""Configuration loading for music-operations.

Reads from an INI file and optionally accepts CLI overrides.  When a CLI
override conflicts with the INI value (both are non-empty and differ), a
:class:`ConfigConflictError` is raised so callers fail loudly rather than
silently using the wrong path.
"""

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConfigConflictError(ValueError):
    """Raised when a CLI argument conflicts with the INI config value."""


DEFAULT_CONFIG_FILE = "config/NUX.loop-core.ini"


@dataclass
class AppConfig:
    """Resolved application configuration."""

    music_directory_globs: str
    anthem_cli_path: str
    destination_directory: str
    anthem_cli_options: str
    anthemscore_home: Optional[str] = None
    repomix_home: Optional[str] = None


def _resolve_field(
    field_name: str,
    ini_value: str,
    cli_value: Optional[str],
    *,
    extra_cli_value: Optional[str] = None,
) -> str:
    """Return the resolved value, raising only on CLI-level conflicts.

    CLI arguments override INI file values (CLI wins).  A
    :class:`ConfigConflictError` is only raised when two *CLI-level* sources
    provide the same field with different values (``cli_value`` vs
    ``extra_cli_value``).

    Args:
        field_name: Human-readable name used in the error message.
        ini_value: Value from the INI file (may be empty string).
        cli_value: Primary CLI override (``None`` means not provided).
        extra_cli_value: Secondary CLI override for the same field, used to
            detect within-CLI conflicts (e.g. two flags mapping to one key).

    Returns:
        The resolved string value: CLI value if provided, else INI value.

    Raises:
        ConfigConflictError: When two CLI-level sources disagree.
    """
    if (
        cli_value is not None
        and extra_cli_value is not None
        and cli_value != extra_cli_value
    ):
        raise ConfigConflictError(
            f"Conflicting CLI values for '{field_name}': "
            f"'{cli_value}' vs '{extra_cli_value}'. "
            "Provide only one."
        )
    if cli_value is not None:
        return cli_value
    if extra_cli_value is not None:
        return extra_cli_value
    return ini_value


def read_config(
    file: str = DEFAULT_CONFIG_FILE,
    anthemscore_home: Optional[str] = None,
    repomix_home: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> "AppConfig":
    """Load configuration, merging INI file values with optional CLI overrides.

    Args:
        file: Path to the INI configuration file.
        anthemscore_home: CLI override for the AnthemScore executable path.
        repomix_home: CLI override for the Repomix executable/home path.
        output_dir: CLI override for the destination directory.

    Returns:
        A fully resolved :class:`AppConfig`.

    Raises:
        ConfigConflictError: When a CLI argument conflicts with the INI value.
        FileNotFoundError: When the config file does not exist.
    """
    config_path = Path(file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(file)

    ini_anthem = parser["host"].get("anthem_cli_path", "")
    ini_dest = parser["host"].get("destination_directory", "")
    ini_options = parser["analysis"].get("anthem_cli_options", "")
    ini_music_dir = parser["pedal"].get("music_directory_globs", "")

    resolved_anthem = _resolve_field("anthem_cli_path", ini_anthem, anthemscore_home)
    resolved_dest = _resolve_field("destination_directory", ini_dest, output_dir)

    return AppConfig(
        music_directory_globs=ini_music_dir,
        anthem_cli_path=resolved_anthem,
        destination_directory=resolved_dest,
        anthem_cli_options=ini_options,
        anthemscore_home=anthemscore_home,
        repomix_home=repomix_home,
    )
