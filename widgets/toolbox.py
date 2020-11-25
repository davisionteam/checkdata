from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QFrame, QShortcut, QHBoxLayout, QPushButton, QSizePolicy


class Toolbox(QFrame):

    rotate_signal = pyqtSignal()
    zoom_in_signal = pyqtSignal()
    zoom_out_signal = pyqtSignal()

    def __init__(self, shortcut_rotate: str, shortcut_zoom_in: str, shortcut_zoom_out: str):
        super().__init__()

        layout = QHBoxLayout(self)

        self.rotate_clockwise_button = QPushButton('+90')
        self.rotate_clockwise_button.clicked.connect(self.on_clockwise_button_clicked)
        self.rotate_clockwise_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.rotate_clockwise_button)

        self.zoom_in_button = QPushButton('+')
        self.zoom_in_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.zoom_in_button.clicked.connect(self.zoom_in_button_clicked)
        layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton('-')
        self.zoom_out_button.clicked.connect(self.zoom_out_button_clicked)
        self.zoom_out_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.zoom_out_button)

        rotate_shortcut = QShortcut(QKeySequence(shortcut_rotate), self)
        rotate_shortcut.activated.connect(self.on_clockwise_button_clicked)

        zoom_in_shortcut = QShortcut(QKeySequence(shortcut_zoom_in), self)
        zoom_in_shortcut.activated.connect(self.zoom_in_button_clicked)

        zoom_out_shortcut = QShortcut(QKeySequence(shortcut_zoom_out), self)
        zoom_out_shortcut.activated.connect(self.zoom_out_button_clicked)

        self.adjustSize()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def on_clockwise_button_clicked(self):
        self.rotate_signal.emit()

    def zoom_in_button_clicked(self):
        self.zoom_in_signal.emit()

    def zoom_out_button_clicked(self):
        self.zoom_out_signal.emit()
