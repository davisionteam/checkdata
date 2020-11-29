from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import (QLabel, QScrollArea, QSizePolicy, QVBoxLayout,
                             QWidget)

class ImageView(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imageLabel.setScaledContents(False)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.scrollArea)

        self.rotateDegree = 0
        self.scaleFactor = 1.0

    @pyqtSlot(object)
    def setImage(self, pillowImage):
        if pillowImage.size[0] * pillowImage.size[1] == 0:
            print(f'Width or height is 0. WxH = {pillowImage.size[0]}x{pillowImage.size[1]}')
            return

        self.scaleFactor = 1.0
        self.rotateDegree = 0.0
        self.rawImage = pillowImage
        self.transformedImage = self.rawImage
        self._updateImage()

    @pyqtSlot()
    def rotateImage(self):
        self.rotateDegree += 90
        self._updateImage()

    @pyqtSlot()
    def zoomInImage(self):
        self.scaleFactor = min(self.scaleFactor + 0.25, 3.0)
        self._updateImage()

    @pyqtSlot()
    def zoomOutImage(self):
        self.scaleFactor = max(self.scaleFactor - 0.25, 0.25)
        self._updateImage()

    def _updateImage(self):
        image_w, image_h = self.rawImage.size
        image_w = self.scaleFactor * image_w
        image_h = self.scaleFactor * image_h
        image_w, image_h = int(image_w), int(image_h)

        self.transformedImage = self.rawImage.resize((image_w, image_h), Image.ANTIALIAS)
        self.transformedImage = self.transformedImage.rotate(self.rotateDegree, expand=True)
        self.image = ImageQt(self.transformedImage)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        self.imageLabel.setFixedSize(self.transformedImage.size[0], self.transformedImage.size[1])
