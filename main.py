import sys
from pathlib import Path
from typing import List

from PyQt5.QtCore import (QEvent, QObject, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenu, QMenuBar, QAction, QActionGroup,
                             QSizePolicy, QVBoxLayout, QWidget)

from widgets.card_viewer import CardViewer
from widgets.index_widget import IndexWidget
from widgets.shape_editor import ShapeEditor

WIN_SIZE = (1024, 128)


class Dataset(QObject):
    new_card = pyqtSignal(str, str)

    def __init__(self, acc_dir: Path):
        super().__init__()
        ext_list = ['jpg', 'jpeg', 'png']
        ext_list.extend([x.upper() for x in ext_list])
        ext_list = [f'**/*.{ext}' for ext in ext_list]

        self.acc_images: List[Path] = sum([sorted(list(acc_dir.glob(pattern))) for pattern in ext_list], [])
        self.acc_jsons = [image.with_suffix('.json') for image in self.acc_images]
        # self.acc_json_diff = [image.with_name(image.stem + '_checked.json') for image in self.acc_images]
        self.accs = list(zip(self.acc_images, self.acc_jsons))
        # for image_path, json_path, json_diff_path in zip(self.acc_images, self.acc_jsons, self.acc_json_diff):
        #     acc_file = ImageDir(image_path, json_path, json_diff_path)
        #     if len(acc_file) > 0:
        #         self.accs.append(acc_file)
        self.current_card_idx = -1

    def __getitem__(self, idx):
        return self.accs[idx]

    def __len__(self):
        return len(self.accs)

    @pyqtSlot(int)
    def on_request_card_index(self, index: int):
        if 0 <= index < len(self):
            self.current_card_idx = index
            image_path, json_path = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path)

    @pyqtSlot()
    def on_request_next_card(self):
        if self.current_card_idx + 1 >= len(self):
            print('End!')
        else:
            self.on_request_card_index(self.current_card_idx + 1)

    @pyqtSlot()
    def on_request_prev_card(self):
        if self.current_card_idx - 1 < 0:
            print('End!')
        else:
            self.on_request_card_index(self.current_card_idx - 1)


class App(QMainWindow):

    def __init__(self, acc_dir):
        super().__init__()
        self.dataset = Dataset(acc_dir)

        left_layout = QVBoxLayout()

        index_selector = IndexWidget(self.dataset)
        index_selector.on_change.connect(self.dataset.on_request_card_index)
        left_layout.addWidget(index_selector)

        card_viewer = CardViewer()
        card_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(card_viewer)

        right_layout = QVBoxLayout()

        shapeEditor = ShapeEditor()
        right_layout.addWidget(shapeEditor)
        card_viewer.nextShapeHandler.connect(shapeEditor.setShape)

        self.dataset.new_card.connect(index_selector.update_card_index)
        self.dataset.new_card.connect(card_viewer.on_set_card)

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

        # set the first line of the first card
        self.dataset.on_request_next_card()

        ##################
        # Init Menubar
        ##################
        rotateAction = QAction('&Rotate', self)
        rotateAction.setShortcut('Ctrl+R')
        rotateAction.triggered.connect(card_viewer.imageViewer.rotateImage)
        zoomInAction = QAction('&Zoom In', self)
        zoomInAction.setShortcut('Ctrl+=')
        zoomInAction.triggered.connect(card_viewer.imageViewer.zoomInImage)
        zoomOutAction = QAction('&Zoom Out', self)
        zoomOutAction.setShortcut('Ctrl+-')
        zoomOutAction.triggered.connect(card_viewer.imageViewer.zoomOutImage)


        nextImageAction = QAction('&Next Image', self)
        nextImageAction.setShortcut(Qt.Key_PageDown)
        nextImageAction.triggered.connect(self.dataset.on_request_next_card)
        prevImageAction = QAction('&Previous Image', self)
        prevImageAction.setShortcut(Qt.Key_PageUp)
        prevImageAction.triggered.connect(self.dataset.on_request_prev_card)
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
