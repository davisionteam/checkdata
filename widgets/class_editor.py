from PIL import Image
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QLineEdit, QLabel, QMessageBox, QVBoxLayout,
                             QWidget)


class ClassEditor(QWidget):

    on_class_name_change = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        label = QLabel('Field Class:')
        layout.addWidget(label)

        self.edit_text = QLineEdit(self)
        self.edit_text.textChanged.connect(self._on_text_change)
        layout.addWidget(self.edit_text)

        self.setLayout(layout)
        self.adjustSize()

    def _on_text_change(self, new_text):
        self.on_class_name_change.emit(new_text)

    @pyqtSlot(object)
    def on_new_textline(self, textline):
        self.current_class_name = textline.class_name
        self.edit_text.setText(self.current_class_name)

