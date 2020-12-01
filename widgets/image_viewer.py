from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint
from PyQt5.QtGui import QPalette, QPixmap, QWheelEvent, QTransform, QMouseEvent
from PyQt5.QtWidgets import (QLabel, QSizePolicy, QVBoxLayout,
                             QWidget, QGraphicsScene, QGraphicsView)
from typing import Optional


class ImageView(QGraphicsView):

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(0, 0, 600, 600))
        self.viewport().installEventFilter(self)
        self.setMouseTracking(True)
        self.modifier = Qt.NoModifier
        self.zoomSpeed = 0.1
        self.isMoving = False

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalScrollBar().disconnect()
        self.verticalScrollBar().disconnect()

        # Set Anchors
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)

    def wheelEvent(self, event: QWheelEvent):
        modifier = event.modifiers()
        if modifier == self.modifier:
            # Save the scene pos
            oldPos = self.mapToScene(event.pos())

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = 1 + self.zoomSpeed
            else:
                zoomFactor = 1 - self.zoomSpeed

            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene to old position
            delta = newPos - oldPos
            print(delta)
            self.translate(delta.x(), delta.y())

    def mouseMoveEvent(self, event: QMouseEvent):
        self.__startPos: Optional[QPoint]
        if event.buttons() == Qt.LeftButton:
            if self.__startPos is not None:
                newPos = self.mapToScene(event.pos())
                delta = newPos - self.__startPos
                self.translate(delta.x(), delta.y())
            self.__startPos = self.mapToScene(event.pos())
        else:
            self.__startPos = None

    @pyqtSlot(object)
    def setImage(self, pillowImage):
        if pillowImage.size[0] * pillowImage.size[1] == 0:
            print(f'Width or height is 0. WxH = {pillowImage.size[0]}x{pillowImage.size[1]}')
            return
        self.image = ImageQt(pillowImage)
        self.scene().clear()
        self.scene().update(0, 0, pillowImage.size[0], pillowImage.size[1])
        self.scene().addPixmap(QPixmap.fromImage(self.image))
        self.adjustSize()

    @pyqtSlot()
    def rotateImage(self):
        self.rotate(90)

    @pyqtSlot()
    def zoomInImage(self):
        self.scale(1 + self.zoomSpeed, 1 + self.zoomSpeed)

    @pyqtSlot()
    def zoomOutImage(self):
        self.scale(1 - self.zoomSpeed, 1 - self.zoomSpeed)
