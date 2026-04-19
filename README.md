# music-operations

![CI](https://github.com/asteroidDavis/music_operations/actions/workflows/ci.yml/badge.svg)

CLI toolkit for music file operations: AnthemScore transcription, Repomix packaging, and USB pedal monitoring.

## Installation

**Conda (recommended):**

```shell
conda env create -f environment.yml
conda activate music_operations
```

To update an existing env after dependency changes:

```shell
conda env update -f environment.yml --prune
```

**pip fallback:**

```shell
pip install -e ".[dev]"
```

## CLI Usage

### AnthemScore transcription

Transcribe a WAV recording to MusicXML + ASDT:

```shell
music-operations --operation anthemscore \
    --input-file /path/to/recording.wav \
    --output-dir /path/to/exports
```

Override the AnthemScore executable path at call time (conflicts with the INI value raise an error):

```shell
music-operations --operation anthemscore \
    --input-file /path/to/recording.wav \
    --output-dir /path/to/exports \
    --anthemscore-home "/Applications/AnthemScore.app/Contents/MacOS/AnthemScore"
```

### Repomix packaging

Pack a directory with Repomix:

```shell
music-operations --operation repomix \
    --input-file /path/to/project \
    --output-dir /path/to/repomix_output \
    --repomix-home /opt/repomix/bin
```

### USB pedal monitor (interactive)

Start the interactive USB-pedal monitor (opens a directory picker):

```shell
music-operations --operation monitor
```

Or via the legacy entry point:

```shell
python src/new_music_usb_monitor.py
```

### Configuration

All options can be specified in an INI file (default: `config/NUX.loop-core.ini`):

```ini
[host]
anthem_cli_path = /Applications/AnthemScore.app/Contents/MacOS/AnthemScore
destination_directory = /Users/you/Music/exports

[analysis]
anthem_cli_options = --headless

[pedal]
music_directory_globs = /Volumes/PEDAL/WAVE/W*/*.wav
```

Pass an alternate config with `--config`:

```shell
music-operations --operation anthemscore \
    --config config/MyPedal.ini \
    --input-file recording.wav \
    --output-dir /exports
```

**Conflict detection:** if a CLI argument (e.g. `--anthemscore-home`) is provided and
the INI file already has a *different* value for the same field, the command exits
with code 2. Matching values are silently accepted.

## Rust subprocess bridge

The Rust `PersonalMusicBrowser` worker spawns this CLI as a subprocess:

```rust
std::process::Command::new("music-operations")
    .args([
        "--operation", "anthemscore",
        "--input-file", &resolved_local_path,
        "--output-dir", &song_export_folder,
    ])
    .spawn()
```

Exit codes:
- `0` — success
- `1` — operational error (bad input, subprocess failure)
- `2` — configuration error (conflict or missing config file)

## Development

```shell
conda activate music_operations
pre-commit install
pytest --cov
```
