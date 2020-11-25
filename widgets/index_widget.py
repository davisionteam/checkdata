from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
                             QWidget)


class IndexWidget(QWidget):

    on_change = pyqtSignal(int)

    def __init__(self, dataset):
        super().__init__()

        layout = QHBoxLayout(self)

        self.index_line_edit = QLineEdit(f'{0:05d}')
        self.index_line_edit.setValidator(QIntValidator(0, len(dataset) - 1))
        self.index_line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.index_line_edit.adjustSize()
        layout.addWidget(self.index_line_edit)

        self.length_label = QLabel(f'{len(dataset) - 1:05d}')
        self.length_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.length_label)

        self.path_label = QLabel('Image path')
        self.path_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.path_label)

        self.path_line_edit = QLineEdit(f'')
        self.path_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.path_line_edit.setReadOnly(True)
        self.path_line_edit.adjustSize()
        layout.addWidget(self.path_line_edit)

        self.adjustSize()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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
        image_path, _, _ = self.dataset[index]
        self.path_line_edit.setText(str(image_path))
