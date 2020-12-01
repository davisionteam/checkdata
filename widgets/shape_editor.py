from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from typing import Optional
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QFont, QImage, QKeySequence, QPalette, QPixmap
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox,
                             QShortcut, QSizePolicy, QVBoxLayout,
                             QWidget, QFrame)
from utils.utils import distance, _order_points, flatten_coords
import numpy as np
import cv2
from .image_viewer import ImageView

class Shape():
    def __init__(self, shape, full_image):
        self.data = shape
        self.full_image = full_image

    @property
    def value(self) -> str:
        return self.data.get('value', '')

    @value.setter
    def value(self, value):
        if value == '':
            if 'value' in self.data.keys():
                del self.data['value']
        else:
            self.data['value'] = value

    @property
    def points(self):
        return self.data['points']

    @points.setter
    def points(self, points):
        self.data['points'] = points

    @property
    def label(self):
        return self.data['label']

    @label.setter
    def label(self, new_name):
        self.data['label'] = new_name

    @property
    def shape_type(self):
        return self.data['shape_type']

    @shape_type.setter
    def shape_type(self, shape_type: str):
        self.data["shape_type"] = shape_type

    @property
    def image(self):
        points = _order_points(self.points)
        if isinstance(points, list):
            cv_image = np.array(self.full_image)
            width = int(round((distance(points[0], points[1]) + distance(points[2], points[3])) / 2))
            height = int(round((distance(points[0], points[3]) + distance(points[1], points[2])) / 2))

            M = cv2.getPerspectiveTransform(np.float32(points), np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
            image = cv2.warpPerspective(cv_image, M, (width, height))

            textline_image = Image.fromarray(image)
        elif isinstance(points, str):
            points = points.strip()
            x, y, w, h = [int(item) for item in points.split()]
            textline_image = self.full_image.crop((x, y, x + w, y + h))
        else:
            print('Unknow type of "points"')
            exit(-1)
        return textline_image

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

        self.imageField = _ShapeImageField('Image')
        self.imageField.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.imageField)

        self.adjustSize()

        self.shape: Optional[Shape] = None

        self.labelField.value.textChanged.connect(self._onLabelChange)
        self.valueField.value.textChanged.connect(self._onValueChange)

    @pyqtSlot(object)
    def setShape(self, shape: Shape):
        self.shape = shape
        self.labelField.setText(shape.label)
        self.valueField.setText(shape.value)
        self.imageField.setImage(shape.image)

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


class _ShapeImageField(_ShapeField):

    def __init__(self, name):
        super().__init__(name)

    def init(self):
        layout = QVBoxLayout(self)
        self.image = ImageView()
        layout.addWidget(self.image)
        self.setImage = self.image.setImage

        self.adjustSize()
