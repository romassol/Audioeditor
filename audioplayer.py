import pyaudio
import wave
import time
import sys
import os
import argparse
import threading
from PyQt5.QtCore import QSize
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMainWindow, QPushButton
from PyQt5.QtGui import QPixmap

from playerbutton import PlayerButton


class AudioPlayer(QMainWindow):
    def __init__(self, file_name, removed):
        super().__init__()
        self.file_name = file_name
        self.removed = removed
        self.height = 768
        self.width = 1366
        self.wav_file = wave.open(file_name, "rb")
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(self.wav_file.getsampwidth()),
                                  channels=self.wav_file.getnchannels(),
                                  rate=self.wav_file.getframerate(),
                                  output=True,
                                  stream_callback=self.callback,
                                  start=False)
        self.central_widget = CentralWidget(self, self.wav_file, self.stream, (self.width, self.height))
        self.setCentralWidget(self.central_widget)
        self.setGeometry(0, 25,
                         self.width,
                         self.height)

    def callback(self, in_data, frame_count, time_info, status):
        data = self.wav_file.readframes(frame_count)
        return data, pyaudio.paContinue

    def closeEvent(self, QCloseEvent):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.wav_file.close()
        if self.removed:
            os.remove(self.file_name)


class CentralWidget(QWidget):
    def __init__(self, parent, wav_file, stream, size_window):
        super().__init__(parent)
        self.wav_file = wav_file
        self.size_window = size_window
        self.stream = stream

        self.background = QLabel(self)
        self.set_background('фон.jpg')

        self.play_button = PlayerButton(self, (3, 3.5), 150, 'play.png')
        self.play_button.clicked.connect(self.play)

        self.pause_button = PlayerButton(self, (5, 3.5), 150, 'pause.png')
        self.pause_button.clicked.connect(self.pause)

        self.thread = threading.Thread(target=self.check)
        self.thread.daemon = True
        self.thread.start()

    def set_background(self, image):
        pixmap = QPixmap(image)
        self.background.setPixmap(pixmap)
        self.background.setAlignment(Qt.AlignCenter)
        self.background.setGeometry(0, 0,
                                    self.size_window[0], self.size_window[1])

    def check(self):
        while True:
            while self.wav_file.tell() != self.wav_file.getnframes():
                time.sleep(0.1)
            self.stream.stop_stream()
            self.wav_file.rewind()

    def play(self):
        self.stream.start_stream()

    def pause(self):
        self.stream.stop_stream()


def get_argparse():
    arg = argparse.ArgumentParser(
        description=" %(prog)s воспроизводит аудиофайл.")
    arg.add_argument(
        '--file',
        '-f',
        type=str,
        default='обычный.wav',
        help='Name of wav file')
    return arg.parse_args()


if __name__ == "__main__":
    arguments = get_argparse()
    app = QApplication(sys.argv)
    ex = AudioPlayer(arguments.file)
    ex.show()
    sys.exit(app.exec_())
