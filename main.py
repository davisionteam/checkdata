from data import Dataset
import sys
from pathlib import Path
from typing import List

from PyQt5.QtCore import (QEvent, QObject, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenu, QMenuBar, QAction,
                             QSizePolicy, QVBoxLayout, QWidget)

from widgets.card_viewer import CardViewer
from widgets.index_widget import IndexWidget
from widgets.shape_editor import ShapeEditor

WIN_SIZE = (1024, 128)


class App(QMainWindow):

    def __init__(self, label_dir: Path):
        super().__init__()
        self.dataset = Dataset(label_dir)

        left_layout = QVBoxLayout()

        index_selector = IndexWidget(self.dataset)
        index_selector.on_change.connect(self.dataset.next)
        left_layout.addWidget(index_selector)

        card_viewer = CardViewer()
        card_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(card_viewer)

        right_layout = QVBoxLayout()

        shapeEditor = ShapeEditor()
        right_layout.addWidget(shapeEditor)
        card_viewer.nextShapeHandler.connect(shapeEditor.setShape)

        self.dataset.item.connect(index_selector.update_card_index)
        self.dataset.item.connect(card_viewer.on_set_card)

        root = QWidget()
        layout = QHBoxLayout(root)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(left_widget)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        # right_widget.setFixedWidth(800)
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(right_widget)
        root.adjustSize()
        self.setCentralWidget(root)
        self.adjustSize()
        # self.showMaximized()

        # # set the first line of the first card
        self.dataset.itemAt(0)

        ##################
        # Init Menubar
        ##################
        rotateAction = QAction('&Rotate', self)
        rotateAction.setShortcut('Ctrl+R')
        rotateAction.triggered.connect(card_viewer.imageViewer.rotateImage)
        rotateAction.triggered.connect(shapeEditor.imageField.image.rotateImage)
        zoomInAction = QAction('&Zoom In', self)
        zoomInAction.setShortcut('Ctrl+=')
        zoomInAction.triggered.connect(card_viewer.imageViewer.zoomInImage)
        zoomInAction.triggered.connect(shapeEditor.imageField.image.zoomInImage)
        zoomOutAction = QAction('&Zoom Out', self)
        zoomOutAction.setShortcut('Ctrl+-')
        zoomOutAction.triggered.connect(card_viewer.imageViewer.zoomOutImage)
        zoomOutAction.triggered.connect(shapeEditor.imageField.image.zoomOutImage)

        nextImageAction = QAction('&Next Image', self)
        nextImageAction.setShortcut(Qt.Key_PageDown)
        nextImageAction.triggered.connect(self.dataset.next)
        prevImageAction = QAction('&Previous Image', self)
        prevImageAction.setShortcut(Qt.Key_PageUp)
        prevImageAction.triggered.connect(self.dataset.prev)
        nextShapeAction = QAction('&Next Shape', self)
        nextShapeAction.setShortcut(Qt.Key_Down)
        nextShapeAction.triggered.connect(card_viewer.on_next_textline)
        prevShapeAction = QAction('&Previous Shape', self)
        prevShapeAction.setShortcut(Qt.Key_Up)
        prevShapeAction.triggered.connect(card_viewer.on_prev_textline)

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')

        viewMenu = mainMenu.addMenu('&View')
        viewMenu.addActions([nextShapeAction, prevShapeAction])
        viewMenu.addActions([nextImageAction, prevImageAction])
        viewMenu.addSeparator()
        viewMenu.addActions([rotateAction, zoomInAction, zoomOutAction])

if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]))
    window.show()
    # window.fixedText.setFocus()
    app.exec_()
