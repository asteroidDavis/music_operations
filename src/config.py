import configparser


def read_config(file='config/NUX.loop-core.ini'):
    config = configparser.ConfigParser()
    config.read(file)
    anthem_cli_path = config['host']['anthem_cli_path']
    destination_directory = config['host']['destination_directory']
    anthem_cli_options = config['analysis']['anthem_cli_options']
    music_directory = config['pedal']['music_directory_globs']
    return music_directory, anthem_cli_path, destination_directory, anthem_cli_options
