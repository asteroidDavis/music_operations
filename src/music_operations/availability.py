"""Report which operations can run on this host and why not."""

import os
import platform
import shutil
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional

from music_operations.config import AppConfig

# AnthemScore publishes builds for these (system, machine) pairs only.
ANTHEMSCORE_PLATFORMS = {
    ("Linux", "x86_64"),
    ("Windows", "AMD64"),
    ("Darwin", "x86_64"),
    ("Darwin", "arm64"),
}


@dataclass
class OperationStatus:
    """Availability of one operation."""

    name: str
    available: bool
    reason: str = ""


def _executable(path: Optional[str], default: str) -> Optional[str]:
    """Resolve *path* (or *default* on ``$PATH``) to an executable, if any."""
    candidate = os.path.expanduser(path) if path else default
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return shutil.which(candidate)


def anthemscore_status(
    cfg: Optional[AppConfig], system: str, machine: str
) -> OperationStatus:
    """Return the availability of the ``anthemscore`` operation."""
    if (system, machine) not in ANTHEMSCORE_PLATFORMS:
        return OperationStatus(
            "anthemscore",
            False,
            f"AnthemScore has no build for {system} {machine}",
        )
    path = cfg.anthem_cli_path if cfg else None
    if not path or not _executable(path, path):
        return OperationStatus(
            "anthemscore", False, f"AnthemScore not installed at {path or '?'}"
        )
    return OperationStatus("anthemscore", True)


def repomix_status(cfg: Optional[AppConfig]) -> OperationStatus:
    """Return the availability of the ``repomix`` operation."""
    home = cfg.repomix_home if cfg else None
    if _executable(home, "repomix"):
        return OperationStatus("repomix", True)
    return OperationStatus("repomix", False, f"{home or 'repomix'} not found")


def monitor_status(system: str, env: Dict[str, str]) -> OperationStatus:
    """Return the availability of the interactive ``monitor`` operation."""
    if system == "Linux" and not (env.get("DISPLAY") or env.get("WAYLAND_DISPLAY")):
        return OperationStatus("monitor", False, "needs a desktop display")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return OperationStatus("monitor", False, "tkinter is not installed")
    return OperationStatus("monitor", True)


def list_operations(
    cfg: Optional[AppConfig],
    system: Optional[str] = None,
    machine: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> List[Dict[str, object]]:
    """Return availability for every operation as JSON-ready dicts."""
    system = system or platform.system()
    machine = machine or platform.machine()
    env = dict(os.environ) if env is None else env
    checks: List[Callable[[], OperationStatus]] = [
        lambda: anthemscore_status(cfg, system, machine),
        lambda: repomix_status(cfg),
        lambda: monitor_status(system, env),
    ]
    return [asdict(check()) for check in checks]
