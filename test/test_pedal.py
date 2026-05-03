from os.path import exists

from music_operations.pedal import Pedal

existing_glob = "./*"


def test_music_files() -> None:
    nux = Pedal(existing_glob)
    assert nux.music_files, "Expected at least one file matched by glob"
    assert all(
        map(exists, nux.music_files)
    ), f"Some paths do not exist: {[p for p in nux.music_files if not exists(p)]}"


def test_music_files_no_match() -> None:
    nux = Pedal("/nonexistent/path/that/matches/nothing/**/*.wav")
    assert (
        nux.music_files == []
    ), f"Expected empty list for non-matching glob, got {nux.music_files}"
