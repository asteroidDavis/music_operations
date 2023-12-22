import json
from logging import getLogger
from multiprocessing import Pool
from os import cpu_count
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
import threading
from tkinter import filedialog
from tkinter import *
from typing import NoReturn

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import read_config
import music_logging
from pedal import Pedal
from usb import detect_usb_insertion


logger = getLogger(__name__)
music_logging.setup_logger(logger)
MUSIC_DIRECTORIES, ANTHEM_CLI_PATH, DESTINATION_DIRECTORY, ANTHEM_CLI_OPTIONS = read_config()

# TODO: break down and unit test
# TODO: run this all in response to a usb event

def preprocess_music_file(output_dir: str, music_file: str) -> NoReturn:
    # check format
    if any(music_file.lower().endswith(extension) for extension in (".wav")):
        # skip overwritting
        output_anthem_directory = Path(output_dir) / Path(music_file).stem
        output_anthem_base = output_anthem_directory / Path(music_file).stem
        if output_anthem_directory.exists():
            logger.warn(f'Skipping {output_anthem_base}. It already exists.')
            return False
        command = f'{ANTHEM_CLI_PATH} {ANTHEM_CLI_OPTIONS} --asdt {output_anthem_base.with_suffix(".asdt")} --musicxml {output_anthem_base.with_suffix(".xml")} {music_file}'
        logger.info(command)
        subprocess.run([ANTHEM_CLI_PATH,
                        ANTHEM_CLI_OPTIONS,
                        '--asdt', f'{output_anthem_base.with_suffix(".asdt")}',
                        '--musicxml', f'{output_anthem_base.with_suffix(".xml")}',
                        music_file])
        copyfile(music_file, output_anthem_base.with_suffix('.wav'))
        logger.info(f'Generated {output_anthem_directory}')
        return True


if __name__ == '__main__':
    logger.info(f'Initial config: {MUSIC_DIRECTORIES, ANTHEM_CLI_PATH, DESTINATION_DIRECTORY, ANTHEM_CLI_OPTIONS}')

    pedal = Pedal(MUSIC_DIRECTORIES)

    root = Tk()
    root.output_dir =  filedialog.askdirectory(initialdir=DESTINATION_DIRECTORY, mustexist=True)

    # Define the file system event observer for each music directory
    music_observers = []
    logger.info(f'Monitoring {json.dumps(pedal.music_files)}')
    # TODO: parallelize or async this loop
    skip_count=0
    with Pool(cpu_count()) as multi_pool:
        import_count = sum(multi_pool.starmap(preprocess_music_file, zip([root.output_dir]*len(pedal.music_files), pedal.music_files)))

    logger.info(f'Imported {import_count}/{len(pedal.music_files)}')
    logger.info(f'Skipped {skip_count}/{len(pedal.music_files)}')
