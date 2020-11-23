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
from PyQt5.QtCore import QEvent, QSize, Qt, pyqtSignal, qDebug
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QImage,
                         QImageReader, QImageWriter, QIntValidator, QKeyEvent,
                         QKeySequence, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QScrollBar, QShortcut, QSizePolicy,
                             QVBoxLayout, QWidget)

WIN_SIZE = (1024, 128)

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

class SwitchSignal(QWidget):

    next = pyqtSignal()
    prev = pyqtSignal()

    def keyPresseEvent(self, ev: QKeyEvent):
        super().keyPressEvent(ev)
        if ev.key() == Qt.Key_Up:
            print('KEy UP')
            self.prev.emit()
        elif ev.key() == Qt.Key_Down:
            print('KEy Down')
            self.next.emit()

class Dataset():
    def __init__(self, acc_dir: Path):
        ext_list = ['jpg', 'jpeg', 'png']
        ext_list.extend([x.upper() for x in ext_list])
        ext_list = [f'**/*.{ext}' for ext in ext_list]

        self.acc_images = sum([sorted(list(acc_dir.glob(pattern))) for pattern in ext_list], [])
        self.acc_jsons = [image.with_suffix('.json') for image in self.acc_images]
        self.acc_json_diff = [image.with_name(image.stem + '_checked.json') for image in self.acc_images]
        self.accs = []
        for image_path, json_path, json_diff_path in zip(self.acc_images, self.acc_jsons, self.acc_json_diff):
            acc_file = ImageDir(image_path, json_path, json_diff_path)
            if len(acc_file) > 0:
                self.accs.append(acc_file)
    
    def __getitem__(self, idx):
        return self.accs[idx]

    def __len__(self):
        return len(self.accs)


class ImageDir():
    def __init__(self, image_path: Path, json_path: Path, json_diff_path: Path):
        self.image_path = image_path
        self.json_path = json_path
        self.json_diff_path = json_diff_path

        self.image: Image.Image = Image.open(image_path)
        self.json_gt = json.load(open(json_path, encoding='utf8'))
        self.textlines_diff = json.load(open(json_diff_path, encoding='utf8'))
        self.check_flags = [0] * len(self.textlines_diff)

    def __getitem__(self, idx):
        obj = self.textlines_diff[idx]
        predict_text = obj['predict_text'].strip()
        label_text = obj['label_text'].strip()
        points = obj['coords']
        ref = self.find_ref_by_coords(points)
        textline = TextLine(ref, predict_text)

        if isinstance(points, list):
            cv_image = np.array(self.image)
            width = int(round((distance(points[0], points[1]) + distance(points[2], points[3])) / 2))
            height = int(round((distance(points[0], points[3]) + distance(points[1], points[2])) / 2))

            M = cv2.getPerspectiveTransform(np.float32(points), np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
            image = cv2.warpPerspective(cv_image, M, (width, height))

            cur_tl_img = Image.fromarray(image)
        elif isinstance(points, str):
            points = points.strip()
            x, y, w, h = [int(item) for item in points.split()]
            cur_tl_img = self.image.crop((x, y, x + w, y + h))
        else:
            print('Unknow type of "coords"')
            exit(-1)
        return textline, cur_tl_img

    def update_line_value(self, ref: Dict, value: str):
        ref['value'] = value

    def find_ref_by_coords(self, coords: List) -> Optional[Dict]:
        for shape in self.json_gt['shapes']:
            if len(shape['points']) != 4:
                # we know that textline must have 4 coords
                continue
            if self.is_same_coords(shape['points'], coords):
                return shape
        return None

    def is_same_coords(self, coords1, coords2) -> bool:
        if isinstance(coords1, list):
            coords1 = self.flatten_coords(coords1)
        else:
            print('Current only support list type')
            return False
        if isinstance(coords2, list):
            coords2 = self.flatten_coords(coords2)
        else:
            print('Current only support list type')
            return False

        assert len(coords1) == len(coords2)
        for idx in range(len(coords1)):
            if abs(coords1[idx] - coords2[idx]) > 2:
                return False
        return True

    def flatten_coords(self, coords):
        coords = [int(val) for coord in coords for val in coord]
        return coords

    def __len__(self):
        return len(self.textlines_diff)

    def save(self):
        json.dump(self.json_gt,
                  open(self.json_path, 'wt', encoding='utf8'),
                  indent=4,
                  ensure_ascii=False)

class TextLine():
    def __init__(self, ref: Dict, predict: str):
        self.ref = ref
        self.predict = predict

    @property
    def textline(self) -> str:
        return self.ref['value']

    @textline.setter
    def textline(self, value):
        self.ref['value'] = value

    @property
    def coords(self):
        return self.ref['points']

class App(QMainWindow):
    def __init__(self, acc_dir):
        super().__init__()

        self.image = QImage()
        self.scaleFactor = 1.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setFixedSize(1024, 64)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(False)

        layout = QVBoxLayout()

        ##################
        # Index
        ##################
        index_widget = QWidget()
        index_layout = QHBoxLayout()
        index_layout.setAlignment(Qt.AlignLeft)

        self.current_acc_index_label = QLineEdit(f'{0:05d}')
        self.current_acc_index_label.setValidator(QIntValidator())
        self.current_acc_index_label.setMaxLength(5)
        self.current_acc_index_label.setFixedWidth(50)
        self.current_acc_index_label.editingFinished.connect(self.jump_to_acc_file)
        self.total_acc_label = QLabel('/0')
        index_layout.addWidget(self.current_acc_index_label)
        index_layout.addWidget(self.total_acc_label)

        self.current_line_index = QLineEdit(f'{0:05d}')
        self.current_line_index.setValidator(QIntValidator())
        self.current_line_index.setMaxLength(5)
        self.current_line_index.setFixedWidth(50)
        self.current_line_index.editingFinished.connect(self.jump_to_line_index)
        self.total_line_label = QLabel('/0')
        index_layout.addWidget(self.current_line_index)
        index_layout.addWidget(self.total_line_label)

        self.rotate_clockwise_button = QPushButton('+90')
        self.rotate_clockwise_button.clicked.connect(self.on_clockwise_button_clicked)
        index_layout.addWidget(self.rotate_clockwise_button)

        self.current_path_label = QLineEdit('path')
        self.current_path_label.setFixedWidth(1000)
        self.current_path_label.setReadOnly(True)
        index_layout.addWidget(self.current_path_label)

        index_widget.setLayout(index_layout)
        layout.addWidget(index_widget)

        label = QLabel('Image:')
        layout.addWidget(label)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)

        label = QLabel('Label:')
        layout.addWidget(label)

        self.label_text = QLineEdit("label")
        f = self.label_text.font()
        f.setFamily('Times New Roman')
        f.setPointSize(27) # sets the size to 27
        f.setStyleHint(QFont.Monospace)
        self.label_text.setFont(f)
        self.label_text.setFocus()
        self.label_text.setReadOnly(False)
        layout.addWidget(self.label_text)

        label = QLabel('OCR Predict:')
        layout.addWidget(label)

        self.pred_text = QLineEdit("pred")
        f = self.pred_text.font()
        f.setFamily('Times New Roman')
        f.setPointSize(27) # sets the size to 27
        f.setStyleHint(QFont.Monospace)
        self.pred_text.setFont(f)
        self.pred_text.setFocus()
        self.pred_text.setReadOnly(True)
        layout.addWidget(self.pred_text)

        signal_widget = SwitchSignal()
        signal_widget.next.connect(self.next_image)
        signal_widget.prev.connect(self.prev_image)
        layout.addWidget(signal_widget)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.resize(WIN_SIZE[0], WIN_SIZE[1])

        self.current_index = 0

        self.account = Dataset(acc_dir)

        if len(self.account) == 0:
            print('Nothing to do! Nice!')
            exit(0)

        self.label_text.installEventFilter(self)

        self.need_save = False
        self.acc_file_index = 0
        self.current_image_dir = self.account[0]
        self.total_acc_label.setText(f'{len(self.account) - 1:05d}')
        self.total_line_label.setText(f'{len(self.current_image_dir) - 1:05d}')
        self.set_step(0)

        self.rotate_degree = 0

        #######################
        # Set shortcut
        #######################
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_current_line)

    def save_current_line(self):
        print('Save')
        if self.current_textline.textline != self.label_text.text():
            self.current_textline.textline = self.label_text.text()
            self.current_image_dir.save()


    def jump_to_line_index(self):
        step = int(self.current_line_index.text())
        self.set_step(step)
    
    def jump_to_acc_file(self):
        acc_index = min(int(self.current_acc_index_label.text()), len(self.account) - 1)
        line_index = min(int(self.current_line_index.text()), len(self.account[acc_index]) - 1)
        self.acc_file_index = acc_index
        self.current_image_dir = self.account[self.acc_file_index]
        self.set_step(line_index)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and source is self.label_text):
            if event.key() == Qt.Key_Down:
                self.next_image()
            elif event.key() == Qt.Key_Up:
                self.prev_image()
        return super().eventFilter(source, event)

    def next_image(self):
        self.rotate_degree = 0
        self.set_step(self.current_index + 1)

    def prev_image(self):
        self.rotate_degree = 0
        self.set_step(self.current_index - 1)

    def on_clockwise_button_clicked(self):
        if self.pillow_image.width * self.pillow_image.height == 0:
            return
        self.rotate_image(90)

    def rotate_image(self, angle):
        self.rotate_degree += angle
        _, image = self.current_image_dir[self.current_index]
        image = image.rotate(self.rotate_degree, expand=True)
        self.loadImage(image)

    def is_able_to_next(self, step):
        if step >= len(self.current_image_dir):
            if self.acc_file_index == len(self.account) - 1:
                return False
        return True

    def is_able_to_back(self, step):
        if step < 0:
            if self.acc_file_index == 0:
                return False
        return True

    def set_step(self, step):
        if step >= len(self.current_image_dir):
            if self.acc_file_index == len(self.account) - 1:
                return
            else:    
                self.acc_file_index += 1
            self.current_image_dir = self.account[self.acc_file_index]
            step = 0
        elif step < 0:
            if self.acc_file_index == 0:
                return
            else:    
                self.acc_file_index -= 1
            self.current_image_dir = self.account[self.acc_file_index]
            step = len(self.current_image_dir) - 1

        self.current_index = step
        textline, image = self.current_image_dir[step]

        if image.size[0] * image.size[1] == 0:
            print(f'Width or height is 0. WxH = {image.size[0]}x{image.size[1]}')
            if self.is_able_to_next(step):
                self.next_image()
                return
            elif self.is_able_to_back(step):
                self.prev_image()
                return
            else:
                print('Done!')
                exit(0)

        self.current_textline = textline
        self.current_line_index.setText(f'{self.current_index:05d}')
        self.current_acc_index_label.setText(f'{self.acc_file_index:05d}')
        self.total_line_label.setText(f'{len(self.current_image_dir) - 1:05d}')
        self.pred_text.setText(textline.predict)
        self.label_text.setText(textline.textline)
        self.loadImage(image)

        #### Resize font
        # Use binary search to efficiently find the biggest font that will fit.
        max_size = 27
        min_size = 1
        font = self.label_text.font()
        while 1 < max_size - min_size:
            new_size = (min_size + max_size) // 2
            font.setPointSize(new_size)
            metrics = QFontMetrics(font)

            target_rect = self.label_text.contentsRect()

            # Be careful which overload of boundingRect() you call.
            rect = metrics.boundingRect(target_rect, Qt.AlignLeft, textline.textline)
            if (rect.width() > target_rect.width() or
                    rect.height() > target_rect.height()):
                max_size = new_size
            else:
                min_size = new_size

        font.setPointSize(min_size)
        self.label_text.setFont(font)

        pred_font = self.pred_text.font()
        pred_font.setPointSize(min_size)
        self.pred_text.setFont(pred_font)

    def loadImage(self, pillow_image: Image.Image):
        image_w, image_h = pillow_image.size
        target_h = 64
        factor = target_h / image_h
        image_w = factor * image_w
        image_h = factor * image_h
        image_w, image_h = int(image_w), int(image_h)
        self.pillow_image = pillow_image.resize((image_w, image_h))

        self.scrollArea.setVisible(True)
        self.image = ImageQt(self.pillow_image)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        self.imageLabel.setFixedSize(image_w, image_h)
        
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), 0)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), 1.0)

        self.current_path_label.setText(str(self.current_image_dir.image_path))
        message = "{}, {}x{}, Depth: {}".format(self.current_image_dir.image_path, self.image.width(), self.image.height(), self.image.depth())
        self.statusBar().showMessage(message)
        return True

    def adjustScrollBar(self, scrollBar: QScrollBar, factor: float):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]))
    window.show()
    # window.fixedText.setFocus()
    app.exec_()
