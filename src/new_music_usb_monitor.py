"""Legacy entry-point — delegates to the ``music_operations`` package CLI.

Run via:
    python new_music_usb_monitor.py

Or preferably use the installed CLI:
    music-operations --operation monitor
"""

import sys

from music_operations.cli import main

if __name__ == "__main__":
    sys.exit(main(["--operation", "monitor"]))
