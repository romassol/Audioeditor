import sys
import argparse
from PyQt5.QtWidgets import QApplication

from audioeditor import AudioEditor
from audioplayer import AudioPlayer


def get_argparse():
    arg = argparse.ArgumentParser(
        description=" %(prog)s обрабатывает звук с возможностью ускорения, замедления, "
        "разреза, склейки, изменения громкости, изменения высоты звука. Есть возможность воспроизвести измененный файл "
        "с помощью аудиоплеера (только если не использовалась команда \'split\'.")

    arg.add_argument(
        '--file',
        '-f',
        type=str,
        default='обычный.wav',
        help='Name of wav file')
    arg.add_argument(
        "--speed",
        "-s",
        type=float,
        help='Speed by a factor with change of a pitch')
    arg.add_argument(
        "--temp",
        "-t",
        type=float,
        help='Speed by a factor without change of a pitch')
    arg.add_argument(
        "--pitch",
        "-p",
        type=int,
        help='Pitch in semitone')
    arg.add_argument(
        "--volume",
        "-v",
        type=int,
        help='How much volume (in dB) will add')
    arg.add_argument(
        "--split",
        "-spl",
        type=int,
        help='Position (in milliseconds) of split file on two and write in two new files')
    arg.add_argument(
        "--join",
        "-j",
        type=str,
        help='Name of wav file, which will be joined with running file')

    check_arguments(arg)
    return arg.parse_args()


def check_arguments(arg):
    non_none_arguments = {argument: value for argument, value in vars(arg.parse_args()).items() if value}
    if 'split' in non_none_arguments and len(non_none_arguments) > 2:
        raise ValueError('Command \'split\' is prohibited to use with other arguments')
    if 'join' in non_none_arguments and len(non_none_arguments) > 2:
        raise ValueError('Command \'join\' is prohibited to use with other arguments')


def execute_commands_and_write_changes_in_new_file(non_none_arguments):
    for key, value in non_none_arguments.items():
        if key != 'file':
            changing_actions[key](value)
    if 'split' not in non_none_arguments:
        audio_edditor.write_changes_to_new_file()


if __name__ == '__main__':
    arguments = get_argparse()
    audio_edditor = AudioEditor(arguments.file)
    changing_actions = {'speed': audio_edditor.change_speed, 'join': audio_edditor.join,
                        'split': audio_edditor.split_and_write_result_in_new_files,
                        'volume': audio_edditor.change_volume, 'pitch': audio_edditor.change_pitch,
                        'temp': audio_edditor.change_temp}
    non_none_arguments = {argument: value for argument, value in vars(arguments).items() if value}
    execute_commands_and_write_changes_in_new_file(non_none_arguments)
    if 'split' not in non_none_arguments:
        app = QApplication(sys.argv)
        audioplayer = AudioPlayer('changing_' + arguments.file, True)
        audioplayer.show()
        sys.exit(app.exec_())
