from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize
from PyQt5.Qt import Qt


class PlayerButton(QPushButton):
    def __init__(self, parent, position, size_square, image):
        super().__init__(parent)
        self.position = position
        self.set_picture(size_square, image)

    def set_picture(self, size_square, image):
        self.setGeometry(
            self.position[0] * size_square,
            self.position[1] * size_square,
            size_square,
            size_square
        )
        self.pixmap = QIcon(image)
        self.setIcon(self.pixmap)
        self.setIconSize(QSize(size_square, size_square))
        self.setStyleSheet("QPushButton {border:none; "
                           "background-color:transparent;}")
        self.show()
