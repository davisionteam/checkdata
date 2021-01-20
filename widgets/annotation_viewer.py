from data import Annotation, Shape
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout
from PyQt5.QtGui import QBrush, QColor, QPen, QPixmap, QPolygonF, QWheelEvent
from PIL import Image
from PIL.ImageQt import ImageQt
from typing import List, Optional


class AnnotationViewer(QWidget):

    shape = pyqtSignal(object)
    nextItem = pyqtSignal()
    prevItem = pyqtSignal()

    def __init__(self, patterns: Optional[List[str]] = None):
        super().__init__()
        self.annotation: Optional[Annotation] = None
        self.viewer = _Viewer()
        layout = QVBoxLayout(self)
        layout.addWidget(self.viewer)
        self.adjustSize()
        self.patterns = patterns

    @pyqtSlot(str, str)
    def setAnnotation(self, imagePath, jsonPath):
        self.jsonPath = jsonPath
        self.fullImage = Image.open(imagePath)
        annotation = Annotation.parse_from_labelme(jsonPath, patterns=self.patterns)

        assert len(annotation) > 0, "Annotation must have at least 1 shape"
        self.annotation = annotation
        self.shapes = self.annotation.shapes
        self.viewer.setImage(self.fullImage)
        self.setShape(self.annotation[0])

    @pyqtSlot(object)
    def setShape(self, shape):
        self.annotation.to_json(self.jsonPath)
        self.hightlightShape(shape)
        self.shape.emit(shape)

    @pyqtSlot()
    def next(self):
        shape = self.annotation.next()
        self.setShape(shape)

    @pyqtSlot()
    def prev(self):
        shape = self.annotation.prev()
        self.setShape(shape)

    def hightlightShape(self, shape: Shape):
        if shape.type == 'polygon':
            self.viewer.addPolygon(shape.points)
        elif shape.type == 'line':
            self.viewer.addLine(shape.points)
        elif shape.type == 'rectangle':
            self.viewer.addRectangle(shape.points)

    def __getitem__(self, idx):
        return self.shapes[idx]

    def __len__(self):
        return len(self.shapes)


class _Viewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.pixmap = None
        self.modifier = Qt.NoModifier
        self.zoomSpeed = 0.1

    def setImage(self, pilImage):
        self.imageQt = ImageQt(pilImage)
        if self.pixmap is not None:
            self.scene().removeItem(self.pixmap)

        self.prevPos: Optional[QPoint] = None
        self.highlighted_polygon = None
        self.currentShape: Optional[QGraphicsItem] = None

        self.setScene(QGraphicsScene(0, 0, 4000, 3000))
        self.pixmap = self.scene().addPixmap(QPixmap.fromImage(self.imageQt))
        self.pixmap.setFlag(QGraphicsItem.ItemIsMovable, True)

    def addPolygon(self, points):
        polygon = list(map(lambda p: QPointF(p[0], p[1]), points))
        dots = polygon
        polygon = QPolygonF(polygon)
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        pen.setJoinStyle(Qt.MiterJoin)
        brush = QBrush(QColor(255, 0, 0, 100))
        polygon = self.scene().addPolygon(polygon, pen=pen, brush=brush)

        pen.setColor(QColor(0, 255, 0, 255))
        radius = 5
        for dot in dots:
            x, y = dot.x() - radius, dot.y() - radius
            w, h = 2 * radius, 2 * radius
            ellipse = self.scene().addEllipse(x, y, w, h, pen, brush)
            ellipse.setParentItem(polygon)

        self._keepOne(polygon)

    def addLine(self, points):
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        item = self.scene().addLine(points[0][0], points[0][1], points[1][0], points[1][1], pen)

        pen.setColor(QColor(0, 255, 0, 255))
        brush = QBrush(QColor(255, 0, 0, 100))
        radius = 10
        for point in points:
            x, y = point[0] - radius, point[1] - radius
            w, h = 2 * radius, 2 * radius
            ellipse = self.scene().addEllipse(x, y, w, h, pen, brush)
            ellipse.setParentItem(item)

        self._keepOne(item)

    def addRectangle(self, points):
        rect = QRectF(QPointF(points[0][0], points[0][1]), QPointF(points[1][0], points[1][1]))
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        brush = QBrush(QColor(255, 0, 0, 100))
        item = self.scene().addRect(rect, pen, brush)
        self._keepOne(item)

    def _keepOne(self, item: QGraphicsItem):
        if self.currentShape is not None:
            self.scene().removeItem(self.currentShape)
        self.currentShape = item
        self.currentShape.setParentItem(self.pixmap)
        self.fitCurrentShape()

    def wheelEvent(self, event: QWheelEvent):
        modifier = event.modifiers()
        if modifier == self.modifier:
            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = 1 + self.zoomSpeed
            else:
                zoomFactor = 1 - self.zoomSpeed

            self.scale(zoomFactor, zoomFactor)

    def showEvent(self, event):
        self.fitCurrentShape()
        super(_Viewer, self).showEvent(event)

    def resizeEvent(self, event):
        self.fitCurrentShape()
        super(_Viewer, self).resizeEvent(event)

    def fitCurrentShape(self):
        margin = 100
        boundingRect = self.currentShape.boundingRect()
        viewRect = QRectF(boundingRect)
        viewRect.setX(viewRect.x() - margin)
        viewRect.setY(viewRect.y() - margin)
        viewRect.setWidth(viewRect.width() + 2 * margin)
        viewRect.setHeight(viewRect.height() + 2 * margin)
        self.fitInView(viewRect, Qt.KeepAspectRatio)
        self.ensureVisible(viewRect, -margin, -margin)