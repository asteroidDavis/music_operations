import glob
from dataclasses import dataclass
from typing import List


@dataclass
class Pedal:
    """
    music_directory_globs: a ; seperated list of globs to match where usb devices containgin music may be added
    """
    music_directory_globs: str

    @property
    def music_files(self) -> List[str]:
        """
        Convert MUSIC_DIRECTORIES to a list of directory paths using glob
        :return:
        """
        music_directory_list = []
        for directory in self.music_directory_globs.split(';'):  # Separating directories by ';'
            music_directory_list.extend(glob.glob(directory))
        return music_directory_list


