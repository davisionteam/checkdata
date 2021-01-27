from typing import Any, List, Optional

from data import Annotation, Point, Shape
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import (QLineF, QPoint, QPointF, QRectF, Qt,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QBrush, QColor, QPen, QPixmap, QPolygonF,
                         QWheelEvent)
from PyQt5.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                             QGraphicsLineItem, QGraphicsPolygonItem,
                             QGraphicsRectItem, QGraphicsScene, QGraphicsView,
                             QVBoxLayout, QWidget)


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
        polygon = PolygonShape(points, self.pixmap)
        self._keepOne(polygon)

    def addLine(self, points):
        line = LineShape(points, self.pixmap)
        self._keepOne(line)

    def addRectangle(self, points):
        rect = RectangleShape(points, self.pixmap)
        self._keepOne(rect)

    def _keepOne(self, item: QGraphicsItem):
        if self.currentShape is not None:
            self.scene().removeItem(self.currentShape)
        self.currentShape = item
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


class PointShape(QGraphicsEllipseItem):

    def __init__(self, point: Point, radius, parent=None, callback=None):
        x, y = point.x - radius, point.y - radius
        w, h = 2 * radius, 2 * radius
        super(PointShape, self).__init__(x, y, w, h, parent)

        self.point = point
        self.originalPoint = Point([point.x, point.y])
        self.radius = radius

        color = QColor(0, 255, 0, 255)
        pen = QPen(color)
        pen.setWidth(10)
        self.setPen(pen)

        brush = QBrush(color)
        self.setBrush(brush)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.callback = callback

    def itemChange(self, change: 'QGraphicsItem.GraphicsItemChange', value: Any) -> Any:
        if (change == QGraphicsItem.ItemPositionChange):
            self.point.x = self.originalPoint.x + value.x()
            self.point.y = self.originalPoint.y + value.y()
            if self.callback is not None:
                self.callback()
        return super().itemChange(change, value)


class PolygonShape(QGraphicsPolygonItem):
    def __init__(self, points, parent=None):
        super(PolygonShape, self).__init__(self._makePolygon(points), parent)
        self.points = points
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        brush = QBrush(QColor(255, 0, 0, 100))
        self.setPen(pen)
        self.setBrush(brush)

        for point in points:
            point = PointShape(point, 10, self, self.onPointChange)
            point.setFlag(QGraphicsItem.ItemIsMovable, True)

    def _makePolygon(self, points: List[Point]):
        return QPolygonF(list(map(lambda p: QPointF(p.x, p.y), points)))

    def onPointChange(self):
        self.setPolygon(self._makePolygon(self.points))


class LineShape(QGraphicsLineItem):
    def __init__(self, points, parent=None):
        self.points = points
        super(LineShape, self).__init__(self._makeLine(self.points), parent)
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        self.setPen(pen)

        for point in points:
            point = PointShape(point, 10, self, self.onPointChange)
            point.setFlag(QGraphicsItem.ItemIsMovable, True)

    def _makeLine(self, points):
        return QLineF(points[0].x, points[0].y, points[1].x, points[1].y)

    def onPointChange(self):
        self.setLine(self._makeLine(self.points))


class RectangleShape(QGraphicsRectItem):
    def __init__(self, points, parent=None):
        self.points = points
        super(RectangleShape, self).__init__(self._makeRect(self.points), parent)
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(10)
        self.setPen(pen)
        brush = QBrush(QColor(255, 0, 0, 100))
        self.setBrush(brush)

        for point in points:
            point = PointShape(point, 10, self, self.onPointChange)
            point.setFlag(QGraphicsItem.ItemIsMovable, True)

    def _makeRect(self, points):
        rect = QRectF(QPointF(points[0].x, points[0].y), QPointF(points[1].x, points[1].y))
        return rect

    def onPointChange(self):
        self.setRect(self._makeRect(self.points))
