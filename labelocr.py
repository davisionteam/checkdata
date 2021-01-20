from typing import Dict
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QSizePolicy, QToolBar, QWidget, QGridLayout
from data import Dataset
from widgets.shape_editor import ShapeEditor
from widgets.annotation_viewer import AnnotationViewer
from widgets.index_widget import IndexWidget


class LabelOCR(QWidget):

    def __init__(self, dataset: Dataset, config: Dict):
        super().__init__()
        self.dataset = dataset

        index_selector = IndexWidget(self.dataset)
        index_selector.on_change.connect(self.dataset.itemAt)
        self.dataset.indexChanged.connect(index_selector.updateIndex)

        annotationViewer = AnnotationViewer(config['labels'])
        annotationViewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        annotationViewer.setAnnotation(self.dataset[0][0], self.dataset[0][1])

        shapeEditor = ShapeEditor()
        shapeEditor.setMinimumWidth(600)
        shapeEditor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        annotationViewer.shape.connect(shapeEditor.setShape)

        self.dataset.item.connect(annotationViewer.setAnnotation)

        self.dataset.itemAt(0)

        ##################
        # Init Menubar
        ##################
        toolbar = QToolBar('Toolbar')
        toolbar.setOrientation(Qt.Vertical)
        # rotateAction = QAction('&Rotate', self)
        # rotateAction.setShortcut('Ctrl+R')
        # rotateAction.triggered.connect(annotationViewer.imageViewer.rotateImage)
        # rotateAction.triggered.connect(shapeEditor.imageField.image.rotateImage)
        # zoomInAction = QAction('&Zoom In', self)
        # zoomInAction.setShortcut('Ctrl+=')
        # zoomInAction.triggered.connect(annotationViewer.imageViewer.zoomInImage)
        # zoomInAction.triggered.connect(shapeEditor.imageField.image.zoomInImage)
        # zoomOutAction = QAction('&Zoom Out', self)
        # zoomOutAction.setShortcut('Ctrl+-')
        # zoomOutAction.triggered.connect(annotationViewer.imageViewer.zoomOutImage)
        # zoomOutAction.triggered.connect(shapeEditor.imageField.image.zoomOutImage)

        nextImageAction = QAction('&Next Image', self)
        nextImageAction.setShortcut(Qt.Key_PageDown)
        nextImageAction.triggered.connect(self.dataset.next)
        prevImageAction = QAction('&Previous Image', self)
        prevImageAction.setShortcut(Qt.Key_PageUp)
        prevImageAction.triggered.connect(self.dataset.prev)
        nextShapeAction = QAction('&Next Shape', self)
        nextShapeAction.setShortcut(Qt.Key_Down)
        nextShapeAction.triggered.connect(annotationViewer.next)
        prevShapeAction = QAction('&Previous Shape', self)
        prevShapeAction.setShortcut(Qt.Key_Up)
        prevShapeAction.triggered.connect(annotationViewer.prev)

        toolbar.addActions([nextImageAction, prevImageAction, nextShapeAction, prevShapeAction])

        layout = QGridLayout(self)
        layout.addWidget(toolbar, 0, 0, 2, 1)
        layout.addWidget(index_selector, 0, 1, 1, 2)
        layout.addWidget(annotationViewer, 1, 1, 1, 1)
        layout.addWidget(shapeEditor, 1, 2, 1, 1)
