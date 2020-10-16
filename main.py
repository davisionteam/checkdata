from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QShortcut
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
import sys
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt
import os
import json
import glob
import csv
import pandas as pd
from PyQt5.QtCore import Qt, qDebug, QSize, pyqtSignal, QEvent
from PyQt5.QtGui import (QColor, QGuiApplication, QImage, QImageReader, QKeyEvent,
                         QIntValidator, QImageWriter, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QScrollArea, QScrollBar, QSizePolicy,
                             QHBoxLayout, QVBoxLayout, QWidget)

WIN_SIZE = (1024, 128)

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

class Account():
    def __init__(self, acc_dir: Path):
        self.acc_images = sorted(list(acc_dir.glob('**/*.jpg')))
        self.acc_jsons = [image.with_suffix('.json') for image in self.acc_images]
        self.accs = []
        for image_path, json_path in zip(self.acc_images, self.acc_jsons):
            acc_file = AccountFile(image_path, json_path)
            if len(acc_file) > 0:
                self.accs.append(acc_file)
    
    def __getitem__(self, idx):
        return self.accs[idx]

    def __len__(self):
        return len(self.accs)


class AccountFile():
    def __init__(self, image_path: Path, json_path: Path):
        self.image_path = image_path
        self.json_path = json_path

        self.image: Image.Image = Image.open(image_path)
        self.textlines = json.load(open(json_path))
        self.check_flags = [0] * len(self.textlines)

    def __getitem__(self, idx):
        obj = self.textlines[idx]
        predict_text = obj['predict_text'].strip()
        labling_text = obj['labling_text'].strip()
        coords = obj['coords'].strip()
        x, y, w, h = [int(item) for item in coords.split()]
        cur_tl_img = self.image.crop((x, y, x + w, y + h))
        return cur_tl_img, predict_text, labling_text

    def __len__(self):
        return len(self.textlines)

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

        index_widget.setLayout(index_layout)
        layout.addWidget(index_widget)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)

        # self.pred_text = QLineEdit("pred")
        # self.pred_text.setReadOnly(True)
        # layout.addWidget(self.pred_text)

        self.label_text = QLineEdit("label")
        f = self.label_text.font()
        f.setPointSize(27) # sets the size to 27
        self.label_text.setFont(f)
        self.label_text.setFocus()
        self.label_text.setReadOnly(True)
        layout.addWidget(self.label_text)

        buttons = QWidget()
        button_layout = QHBoxLayout()
        self.correct_button = QPushButton('ĐÚNG')
        pallete = self.correct_button.palette()
        pallete.setColor(QPalette.Button, QColor(Qt.green))
        self.correct_button.setFixedHeight(40)
        self.correct_button.setPalette(pallete)
        self.correct_button.clicked.connect(self.on_correct_button_clicked)
        self.correct_button.setShortcut("1")
        button_layout.addWidget(self.correct_button)
        self.incorrect_button = QPushButton('SAI')
        pallete = self.correct_button.palette()
        pallete.setColor(QPalette.Button, QColor(Qt.red))
        self.incorrect_button.setFixedHeight(40)
        self.incorrect_button.setPalette(pallete)
        self.incorrect_button.clicked.connect(self.on_incorrect_button_clicked)
        self.incorrect_button.setShortcut("2")
        button_layout.addWidget(self.incorrect_button)
        buttons.setLayout(button_layout)
        layout.addWidget(buttons)

        signal_widget = SwitchSignal()
        signal_widget.next.connect(self.next_image)
        signal_widget.prev.connect(self.prev_image)
        layout.addWidget(signal_widget)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.resize(WIN_SIZE[0], WIN_SIZE[1])

        self.current_index = 0

        self.account = Account(acc_dir)

        if len(self.account) == 0:
            print('Nothing to do! Nice!')
            exit(0)

        self.label_text.installEventFilter(self)

        self.need_save = False
        self.acc_file_index = 0
        self.current_account_file = self.account[0]
        self.total_acc_label.setText(f'{len(self.account) - 1:05d}')
        self.total_line_label.setText(f'{len(self.current_account_file) - 1:05d}')
        self.set_step(0)

    def jump_to_line_index(self):
        step = int(self.current_line_index.text())
        self.set_step(step)
    
    def jump_to_acc_file(self):
        acc_index = min(int(self.current_acc_index_label.text()), len(self.account) - 1)
        line_index = min(int(self.current_line_index.text()), len(self.account[acc_index]) - 1)
        self.acc_file_index = acc_index
        self.current_account_file = self.account[self.acc_file_index]
        self.set_step(line_index)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and source is self.label_text):
            if event.key() == Qt.Key_Down:
                self.next_image()
            elif event.key() == Qt.Key_Up:
                self.prev_image()
        return super().eventFilter(source, event)

    def next_image(self):
        self.save()
        self.set_step(self.current_index + 1)

    def prev_image(self):
        self.save()
        self.set_step(self.current_index - 1)

    def on_correct_button_clicked(self):
        self.current_account_file.check_flags[self.current_index] = 1
        self.next_image()

    def on_incorrect_button_clicked(self):
        self.current_account_file.check_flags[self.current_index] = 0
        self.next_image()

    def is_able_to_next(self, step):
        if step >= len(self.current_account_file):
            if self.acc_file_index == len(self.account) - 1:
                return False
        return True

    def is_able_to_back(self, step):
        if step < 0:
            if self.acc_file_index == 0:
                return False
        return True

    def set_step(self, step):
        if step >= len(self.current_account_file):
            if self.acc_file_index == len(self.account) - 1:
                self.acc_file_index = 0
            else:    
                self.acc_file_index += 1
            self.current_account_file = self.account[self.acc_file_index]
            step = 0
        elif step < 0:
            if self.acc_file_index == 0:
                self.acc_file_index = len(self.account) - 1
            else:    
                self.acc_file_index -= 1
            self.current_account_file = self.account[self.acc_file_index]
            step = len(self.current_account_file) - 1

        self.current_index = step
        image, pred, label = self.current_account_file[step]
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

        self.current_line_index.setText(f'{self.current_index:05d}')
        self.current_acc_index_label.setText(f'{self.acc_file_index:05d}')
        self.total_line_label.setText(f'{len(self.current_account_file) - 1:05d}')
        # self.pred_text.setText(pred)
        self.label_text.setText(label)
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
            rect = metrics.boundingRect(target_rect, Qt.AlignLeft, label)
            if (rect.width() > target_rect.width() or
                    rect.height() > target_rect.height()):
                max_size = new_size
            else:
                min_size = new_size

        font.setPointSize(min_size)
        self.label_text.setFont(font)

    def loadImage(self, pillow_image: Image.Image):
        image_w, image_h = pillow_image.size
        target_h = 64
        factor = target_h / image_h
        image_w = factor * image_w
        image_h = factor * image_h
        image_w, image_h = int(image_w), int(image_h)
        pillow_image = pillow_image.resize((image_w, image_h))

        self.scrollArea.setVisible(True)
        self.image = ImageQt(pillow_image)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        self.imageLabel.setFixedSize(image_w, image_h)
        
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), 0)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), 1.0)

        message = "{}, {}x{}, Depth: {}".format(self.current_account_file.image_path, self.image.width(), self.image.height(), self.image.depth())
        self.statusBar().showMessage(message)
        return True

    def adjustScrollBar(self, scrollBar: QScrollBar, factor: float):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))

    def save(self):
        acc_file: AccountFile
        for acc_file in self.account:
            textline_incorrect = []
            for i, (flag, line) in enumerate(zip(acc_file.check_flags, acc_file.textlines)):
                if flag == 0:
                    textline_incorrect.append(line)
            save_path = acc_file.json_path
            json.dump(textline_incorrect, open(save_path, 'wt'))


if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]))
    window.show()
    # window.fixedText.setFocus()
    app.exec_()
