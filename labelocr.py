from typing import Dict
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QSizePolicy, QToolBar, QToolButton, QWidget, QGridLayout
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

        nextImageAction = QAction(QIcon('resources/skip_next-black-18dp/2x/baseline_skip_next_black_18dp.png'), 'Next Image')
        nextImageAction.setShortcut(Qt.Key_PageDown)
        nextImageAction.setToolTip(nextImageAction.shortcut().toString())
        nextImageAction.triggered.connect(self.dataset.next)
        nextImageButton = QToolButton()
        nextImageButton.setDefaultAction(nextImageAction)
        nextImageButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(nextImageButton)

        prevImageAction = QAction(QIcon('resources/skip_previous-black-18dp/2x/baseline_skip_previous_black_18dp.png'), 'Prev Image')
        prevImageAction.setShortcut(Qt.Key_PageUp)
        prevImageAction.setToolTip(prevImageAction.shortcut().toString())
        prevImageAction.triggered.connect(self.dataset.prev)
        prevImageButton = QToolButton()
        prevImageButton.setDefaultAction(prevImageAction)
        prevImageButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(prevImageButton)

        toolbar.addSeparator()

        prevShapeAction = QAction(QIcon('resources/fast_rewind-black-18dp/2x/baseline_fast_rewind_black_18dp.png'), 'Prev Shape')
        prevShapeAction.setShortcut(Qt.Key_Up)
        prevShapeAction.setToolTip(prevShapeAction.shortcut().toString())
        prevShapeAction.triggered.connect(annotationViewer.prev)
        prevShapeButton = QToolButton()
        prevShapeButton.setDefaultAction(prevShapeAction)
        prevShapeButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(prevShapeButton)

        nextShapeAction = QAction(QIcon('resources/fast_forward-black-18dp/2x/baseline_fast_forward_black_18dp.png'), 'Next Shape')
        nextShapeAction.setShortcut(Qt.Key_Down)
        nextShapeAction.setToolTip(nextShapeAction.shortcut().toString())
        nextShapeAction.triggered.connect(annotationViewer.next)
        nextShapeButton = QToolButton()
        nextShapeButton.setDefaultAction(nextShapeAction)
        nextShapeButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.addWidget(nextShapeButton)

        layout = QGridLayout(self)
        layout.addWidget(toolbar, 0, 0, 2, 1)
        layout.addWidget(index_selector, 0, 1, 1, 2)
        layout.addWidget(annotationViewer, 1, 1, 1, 1)
        layout.addWidget(shapeEditor, 1, 2, 1, 1)
