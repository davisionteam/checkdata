import csv
import glob
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, pyqtSignal, qDebug, QObject, pyqtSlot
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QImage,
                         QImageReader, QImageWriter, QIntValidator, QKeyEvent,
                         QKeySequence, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QScrollBar, QShortcut, QSizePolicy,
                             QVBoxLayout, QWidget)
from widgets.card_viewer import CardViewer
from widgets.textline_editor import TextLineEditor
from widgets.class_editor import ClassEditor
WIN_SIZE = (1024, 128)
from utils.utils import distance, _order_points


class Dataset(QObject):
    new_card = pyqtSignal(str, str, str)

    def __init__(self, acc_dir: Path):
        super().__init__()
        ext_list = ['jpg', 'jpeg', 'png']
        ext_list.extend([x.upper() for x in ext_list])
        ext_list = [f'**/*.{ext}' for ext in ext_list]

        self.acc_images = sum([sorted(list(acc_dir.glob(pattern))) for pattern in ext_list], [])
        self.acc_jsons = [image.with_suffix('.json') for image in self.acc_images]
        self.acc_json_diff = [image.with_name(image.stem + '_checked.json') for image in self.acc_images]
        self.accs = list(zip(self.acc_images, self.acc_jsons, self.acc_json_diff))
        # for image_path, json_path, json_diff_path in zip(self.acc_images, self.acc_jsons, self.acc_json_diff):
        #     acc_file = ImageDir(image_path, json_path, json_diff_path)
        #     if len(acc_file) > 0:
        #         self.accs.append(acc_file)
        self.current_card_idx = -1

    def __getitem__(self, idx):
        return self.accs[idx]

    def __len__(self):
        return len(self.accs)

    @pyqtSlot()
    def on_request_next_card(self):
        if self.current_card_idx >= len(self):
            print('End!')
            return None
        else:
            self.current_card_idx += 1
            image_path, json_path, json_diff = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path, json_diff)

    @pyqtSlot()
    def on_request_prev_card(self):
        if self.current_card_idx < 0:
            print('End!')
        else:
            self.current_card_idx -= 1
            image_path, json_path, json_diff = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path, json_diff)


class App(QMainWindow):

    next_line_signal = pyqtSignal()
    prev_line_signal = pyqtSignal()

    def __init__(self, acc_dir):
        super().__init__()
        self.dataset = Dataset(acc_dir)

        layout = QVBoxLayout()

        card_viewer = CardViewer()
        layout.addWidget(card_viewer)

        class_editor = ClassEditor(Path('./config.yaml'))
        layout.addWidget(class_editor)

        textline_editor = TextLineEditor()
        layout.addWidget(textline_editor)

        card_viewer.next_textline_handler.connect(textline_editor.on_new_textline)
        card_viewer.next_textline_handler.connect(class_editor.on_new_textline)
        card_viewer.next_card_signal.connect(self.dataset.on_request_next_card)
        card_viewer.prev_card_signal.connect(self.dataset.on_request_prev_card)
        self.dataset.new_card.connect(card_viewer.on_set_card)
        textline_editor.on_change.connect(card_viewer.on_update_textline_label)
        textline_editor.on_done.connect(card_viewer.on_next_textline)
        class_editor.on_class_name_change.connect(card_viewer.on_update_textline_classname)
        self.next_line_signal.connect(card_viewer.on_next_textline)
        self.prev_line_signal.connect(card_viewer.on_prev_textline)

        root = QWidget()
        root.setLayout(layout)
        root.adjustSize()
        self.setCentralWidget(root)
        self.adjustSize()
        # self.showMaximized()
        self.installEventFilter(self)

        # set the first line of the first card
        self.dataset.on_request_next_card()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress):
            if event.key() == Qt.Key_Down:
                self.next_line_signal.emit()
            elif event.key() == Qt.Key_Up:
                self.prev_line_signal.emit()
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]))
    window.show()
    # window.fixedText.setFocus()
    app.exec_()
