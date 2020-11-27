from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QImage, QKeySequence, QPalette, QPixmap
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QShortcut, QSizePolicy, QVBoxLayout,
                             QWidget)


class TextLineEditor(QWidget):

    on_change = pyqtSignal(str)
    on_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.image = QImage()

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setFixedSize(1024, 128)
        self.imageLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imageLabel.setScaledContents(True)
        layout = QVBoxLayout()

        toolbar = _Toolbox()
        toolbar.zoom_in_signal.connect(self.zoom_in_image)
        toolbar.zoom_out_signal.connect(self.zoom_out_image)
        toolbar.rotate_signal.connect(self.on_clockwise_button_clicked)
        layout.addWidget(toolbar)

        label = QLabel('Text Line Image')
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(label)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.scrollArea)

        label = QLabel('Label:')
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(label)

        self.label_text = QLineEdit("label")
        self.label_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        f = self.label_text.font()
        f.setFamily('Times New Roman')
        f.setPointSize(27) # sets the size to 27
        f.setStyleHint(QFont.Monospace)
        self.label_text.setFont(f)
        self.label_text.setFocus()
        self.label_text.setReadOnly(False)
        layout.addWidget(self.label_text)

        self.setLayout(layout)
        self.adjustSize()
        self.rotate_degree = 0
        self.scale_factor = 1.0

        #######################
        # Set shortcut
        #######################
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self._on_save)

        self.label_text.textChanged.connect(self._on_text_change)
        self.label_text.returnPressed.connect(self._on_save)

    def _on_save(self):
        self.on_done.emit()

    def _on_text_change(self, new_text):
        self.on_change.emit(new_text)

    @pyqtSlot(object)
    def on_new_textline(self, textline):
        if textline.image.size[0] * textline.image.size[1] == 0:
            print(f'Width or height is 0. WxH = {textline.image.size[0]}x{textline.image.size[1]}')
            return

        self.scale_factor = 1.0
        self.rotate_degree = 0.0

        self.current_textline = textline
        self.loadImage(textline.image)
        self.label_text.setText(textline.textline)

    def on_clockwise_button_clicked(self):
        if self.pillow_image.width * self.pillow_image.height == 0:
            return
        self.rotate_image(90)

    def rotate_image(self, angle):
        self.rotate_degree += angle
        self.loadImage(self.current_textline.image)

    def zoom_in_image(self):
        self.scale_factor = min(self.scale_factor + 0.25, 3.0)
        self.loadImage(self.current_textline.image)

    def zoom_out_image(self):
        self.scale_factor = max(self.scale_factor - 0.25, 0.25)
        self.loadImage(self.current_textline.image)

    def loadImage(self, pillow_image: Image.Image):
        image_w, image_h = pillow_image.size
        image_w = self.scale_factor * image_w
        image_h = self.scale_factor * image_h
        image_w, image_h = int(image_w), int(image_h)
        pillow_image = pillow_image.resize((image_w, image_h), Image.ANTIALIAS)
        pillow_image = pillow_image.rotate(self.rotate_degree, expand=True)
        self.pillow_image = pillow_image
        self.scrollArea.setVisible(True)
        self.image = ImageQt(self.pillow_image)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        self.imageLabel.setFixedSize(self.pillow_image.size[0], self.pillow_image.size[1])

class _Toolbox(QWidget):

    rotate_signal = pyqtSignal()
    zoom_in_signal = pyqtSignal()
    zoom_out_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.rotate_clockwise_button = QPushButton('+90')
        self.rotate_clockwise_button.clicked.connect(self.on_clockwise_button_clicked)
        layout.addWidget(self.rotate_clockwise_button)

        self.zoom_in_button = QPushButton('+')
        self.zoom_in_button.clicked.connect(self.zoom_in_button_clicked)
        layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton('-')
        self.zoom_out_button.clicked.connect(self.zoom_out_button_clicked)
        layout.addWidget(self.zoom_out_button)

        rotate_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        rotate_shortcut.activated.connect(self.on_clockwise_button_clicked)

        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in_shortcut.activated.connect(self.zoom_in_button_clicked)

        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self.zoom_out_button_clicked)

        self.adjustSize()

    def on_clockwise_button_clicked(self):
        self.rotate_signal.emit()

    def zoom_in_button_clicked(self):
        self.zoom_in_signal.emit()

    def zoom_out_button_clicked(self):
        self.zoom_out_signal.emit()
