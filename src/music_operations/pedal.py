"""Pedal device abstraction for resolving music file globs."""

import glob
from dataclasses import dataclass
from typing import List


@dataclass
class Pedal:
    """Resolves music file paths from a semicolon-delimited list of globs.

    Attributes:
        music_directory_globs: A ``;``-separated list of glob patterns
            matching directories or files on connected USB pedal devices.
    """

    music_directory_globs: str

    @property
    def music_files(self) -> List[str]:
        """Expand all globs and return matching file paths.

        Returns:
            A flat list of absolute file paths matched by
            :attr:`music_directory_globs`.
        """
        music_directory_list: List[str] = []
        for directory in self.music_directory_globs.split(";"):
            music_directory_list.extend(glob.glob(directory))
        return music_directory_list
