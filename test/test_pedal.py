from os.path import exists
from pedal import Pedal

# test_glob = 'D:\CHERUB\WAVE\W*\*'
existing_glob = '.\*'


def test_music_files():
    nux = Pedal(existing_glob)
    assert all(map(exists, nux.music_files))
    assert nux.music_files
