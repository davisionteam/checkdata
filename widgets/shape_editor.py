from data import Shape
from typing import Optional
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLineEdit, QGroupBox, QSizePolicy, QVBoxLayout, QWidget


class ShapeEditor(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        self.labelField = _ShapeTextField('Label')
        self.labelField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.labelField)

        self.valueField = _ShapeTextField('Value')
        self.valueField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.valueField)

        self.adjustSize()

        self.shape: Optional[Shape] = None

        self.labelField.value.textChanged.connect(self._onLabelChange)
        self.valueField.value.textChanged.connect(self._onValueChange)

    @pyqtSlot(object)
    def setShape(self, shape: Shape):
        self.shape = shape
        self.labelField.setText(shape.label)
        self.valueField.setText(shape.value or '')

    @pyqtSlot(str)
    def _onLabelChange(self, newLabel):
        self.shape.label = newLabel

    @pyqtSlot(str)
    def _onValueChange(self, newValue):
        self.shape.value = newValue


class _ShapeField(QGroupBox):

    def __init__(self, name):
        super().__init__(name)
        self.init()

    def init(self):
        raise NotImplementedError()


class _ShapeTextField(_ShapeField):

    def __init__(self, name):
        super().__init__(name)

    def init(self):
        layout = QVBoxLayout(self)

        font = QFont()
        font.setFamily('Times New Roman')
        font.setPointSize(27)
        font.setStyleHint(QFont.Monospace)

        self.value = QLineEdit('')
        self.value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value.setFont(font)
        layout.addWidget(self.value)

        self.adjustSize()

    @pyqtSlot(str)
    def setText(self, text):
        self.value.setText(text)
