from typing import Dict
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QHBoxLayout, QSizePolicy, QToolBar, QVBoxLayout, QWidget
from data import Dataset
from widgets.shape_editor import ShapeEditor
from widgets.annotation_viewer import AnnotationViewer
from widgets.index_widget import IndexWidget


class LabelOCR(QWidget):

    def __init__(self, dataset: Dataset, config: Dict):
        super().__init__()
        self.dataset = dataset
        left_layout = QVBoxLayout()

        index_selector = IndexWidget(self.dataset)
        index_selector.on_change.connect(self.dataset.itemAt)
        self.dataset.indexChanged.connect(index_selector.updateIndex)
        left_layout.addWidget(index_selector)

        annotationViewer = AnnotationViewer(config['labels'])
        annotationViewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(annotationViewer)

        annotationViewer.setAnnotation(self.dataset[0][0], self.dataset[0][1])

        right_layout = QVBoxLayout()

        shapeEditor = ShapeEditor()
        shapeEditor.setMinimumWidth(600)
        shapeEditor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(shapeEditor)
        annotationViewer.shape.connect(shapeEditor.setShape)

        # self.dataset.item.connect(index_selector.update_card_index)
        self.dataset.item.connect(annotationViewer.setAnnotation)

        layout = QHBoxLayout(self)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(left_widget)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        # right_widget.setFixedWidth(800)
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(right_widget)
        self.adjustSize()
        # self.showMaximized()

        # # set the first line of the first card
        self.dataset.itemAt(0)

        ##################
        # Init Menubar
        ##################
        self.toolbar = QToolBar('Toolbar', self)
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

        self.toolbar.addActions([nextImageAction, prevImageAction, nextShapeAction, prevShapeAction])
