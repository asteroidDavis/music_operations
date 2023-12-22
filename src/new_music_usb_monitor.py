import json
import music_logging
from logging import getLogger
from pathlib import Path
import subprocess
import sys
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import read_config
from pedal import Pedal
from usb import detect_usb_insertion

MUSIC_DIRECTORIES, ANTHEM_CLI_PATH, DESTINATION_DIRECTORY, ANTHEM_CLI_OPTIONS = read_config()


if __name__ == '__main__':
    # TODO: break down and unit test
    # TODO: run this all in response to a usb event

    logger = getLogger(__name__)
    music_logging.setup_logger(logger)
    logger.info(f'Initial config: {MUSIC_DIRECTORIES, ANTHEM_CLI_PATH, DESTINATION_DIRECTORY, ANTHEM_CLI_OPTIONS}')

    pedal = Pedal(MUSIC_DIRECTORIES)
    # TODO: add an output directory chooser

    # Define the file system event observer for each music directory
    music_observers = []
    logger.info(f'Monitoring {json.dumps(pedal.music_files)}')
    # TODO: skip things which have already been imported
    # TODO: parallelize or async this loop
    for music_file in pedal.music_files:
        # check format
        if any(music_file.lower().endswith(extension) for extension in (".mp3", ".wav")):
            # skip overwritting
            output_anthem_directory = Path(DESTINATION_DIRECTORY) / Path(music_file).stem / Path(music_file).stem
            if output_anthem_directory.exists():
                logger.warn(f'Skipping {output_anthem_file}. It already exists.')
                continue
            command = f'{ANTHEM_CLI_PATH} {ANTHEM_CLI_OPTIONS} --asdt {output_anthem_directory.with_suffix(".asdt")} --musicxml {output_anthem_directory.with_suffix(".xml")} {music_file}'
            logger.info(command)
            # TODO: cp the WAV too
            subprocess.run([ANTHEM_CLI_PATH,
                            ANTHEM_CLI_OPTIONS,
                            '--asdt', f'{output_anthem_directory.with_suffix(".asdt")}',
                            '--musicxml', f'{output_anthem_directory.with_suffix(".xml")}',
                            music_file])
            logger.info(f'Generated {output_anthem_directory}')
    # TODO: finally a summary metric
