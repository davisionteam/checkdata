
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, pyqtSignal, pyqtSlot, qDebug
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QImage,
                         QImageReader, QImageWriter, QIntValidator, QKeyEvent,
                         QKeySequence, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QScrollArea, QScrollBar,
                             QShortcut, QSizePolicy, QVBoxLayout, QWidget)


class IndexWidget(QWidget):

    on_change = pyqtSignal(int)

    def __init__(self, dataset):
        super().__init__()

        layout = QHBoxLayout(self)

        self.index_line_edit = QLineEdit('0')
        self.index_line_edit.setValidator(QIntValidator(0, len(dataset) - 1))
        layout.addWidget(self.index_line_edit)

        self.length_label = QLabel(f'{len(dataset) - 1:05d}')
        layout.addWidget(self.length_label)

        self.index_line_edit.returnPressed.connect(self._on_text_change)
        self.dataset = dataset

    def _on_text_change(self):
        text = self.index_line_edit.text()
        if text == '':
            text = '0'
        self.on_change.emit(int(text))

    @pyqtSlot()
    def update_card_index(self):
        index = self.dataset.current_card_idx
        self.index_line_edit.setText(f'{index:05d}')