
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, pyqtSignal, qDebug, pyqtSlot
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QImage,
                         QImageReader, QImageWriter, QIntValidator, QKeyEvent,
                         QKeySequence, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QScrollBar, QShortcut, QSizePolicy,
                             QVBoxLayout, QWidget)
from PIL import Image


class TextLineEditor(QWidget):

    on_change = pyqtSignal(str)
    on_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.image = QImage()
        self.scaleFactor = 1.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setFixedSize(1024, 64)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.setFixedHeight(300)
        layout = QVBoxLayout()

        # self.rotate_clockwise_button = QPushButton('+90')
        # self.rotate_clockwise_button.clicked.connect(self.on_clockwise_button_clicked)
        # index_layout.addWidget(self.rotate_clockwise_button)
        # index_widget.setLayout(index_layout)
        # layout.addWidget(index_widget)

        label = QLabel('Text Line Image')
        layout.addWidget(label)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)
        self.scrollArea.setWidgetResizable(False)
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

        self.setLayout(layout)

        # signal_widget = SwitchSignal()
        # signal_widget.next.connect(self.next_image)
        # signal_widget.prev.connect(self.prev_image)
        # layout.addWidget(signal_widget)

        # self.resize(WIN_SIZE[0], WIN_SIZE[1])

        # self.account = Dataset(acc_dir)

        # if len(self.account) == 0:
        #     print('Nothing to do! Nice!')
        #     exit(0)

        self.label_text.installEventFilter(self)

        # self.need_save = False
        # self.acc_file_index = 0
        # self.current_image_dir = self.account[0]
        # self.total_acc_label.setText(f'{len(self.account) - 1:05d}')
        # self.total_line_label.setText(f'{len(self.current_image_dir) - 1:05d}')
        # self.set_step(0)

        # self.rotate_degree = 0

        #######################
        # Set shortcut
        #######################
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self._on_save)

        self.label_text.textChanged.connect(self._on_text_change)
        self.label_text.returnPressed.connect(self._on_save)

    def _on_save(self):
        self.on_done.emit()

    def _on_text_change(self, new_text):
        self.on_change.emit(new_text)

    @pyqtSlot(object)
    def on_new_textline(self, textline):
        if textline.image.size[0] * textline.image.size[1] == 0:
            print(f'Width or height is 0. WxH = {textline.image.size[0]}x{textline.image.size[1]}')
            return

        self.loadImage(textline.image)
        self.label_text.setText(textline.textline)
        self.pred_text.setText(textline.predict)

    # def save_current_line(self):
    #     print('Save')
    #     if self.current_textline.textline != self.label_text.text():
    #         self.current_textline.textline = self.label_text.text()
    #         self.current_image_dir.save()


    # def jump_to_line_index(self):
    #     step = int(self.current_line_index.text())
    #     self.set_step(step)
    
    # def jump_to_acc_file(self):
    #     acc_index = min(int(self.current_acc_index_label.text()), len(self.account) - 1)
    #     line_index = min(int(self.current_line_index.text()), len(self.account[acc_index]) - 1)
    #     self.acc_file_index = acc_index
    #     self.current_image_dir = self.account[self.acc_file_index]
    #     self.set_step(line_index)

    # def eventFilter(self, source, event):
    #     if (event.type() == QEvent.KeyPress and source is self.label_text):
    #         if event.key() == Qt.Key_Down:
    #             self.next_image()
    #         elif event.key() == Qt.Key_Up:
    #             self.prev_image()
    #     return super().eventFilter(source, event)

    # def next_image(self):
    #     self.rotate_degree = 0
    #     self.set_step(self.current_index + 1)

    # def prev_image(self):
    #     self.rotate_degree = 0
    #     self.set_step(self.current_index - 1)

    # def on_clockwise_button_clicked(self):
    #     if self.pillow_image.width * self.pillow_image.height == 0:
    #         return
    #     self.rotate_image(90)

    # def rotate_image(self, angle):
    #     self.rotate_degree += angle
    #     textline = self.current_image_dir[self.current_index]
    #     image = textline.image.rotate(self.rotate_degree, expand=True)
    #     self.loadImage(image)

    # def is_able_to_next(self, step):
    #     if step >= len(self.current_image_dir):
    #         if self.acc_file_index == len(self.account) - 1:
    #             return False
    #     return True

    # def is_able_to_back(self, step):
    #     if step < 0:
    #         if self.acc_file_index == 0:
    #             return False
    #     return True

    # def set_step(self, step):
    #     if step >= len(self.current_image_dir):
    #         if self.acc_file_index == len(self.account) - 1:
    #             return
    #         else:    
    #             self.acc_file_index += 1
    #         self.current_image_dir = self.account[self.acc_file_index]
    #         step = 0
    #     elif step < 0:
    #         if self.acc_file_index == 0:
    #             return
    #         else:    
    #             self.acc_file_index -= 1
    #         self.current_image_dir = self.account[self.acc_file_index]
    #         step = len(self.current_image_dir) - 1

    #     self.current_index = step
    #     textline = self.current_image_dir[step]

    #     if textline.image.size[0] * textline.image.size[1] == 0:
    #         print(f'Width or height is 0. WxH = {textline.image.size[0]}x{textline.image.size[1]}')
    #         if self.is_able_to_next(step):
    #             self.next_image()
    #             return
    #         elif self.is_able_to_back(step):
    #             self.prev_image()
    #             return
    #         else:
    #             print('Done!')
    #             exit(0)

    #     self.current_textline = textline
    #     self.current_line_index.setText(f'{self.current_index:05d}')
    #     self.current_acc_index_label.setText(f'{self.acc_file_index:05d}')
    #     self.total_line_label.setText(f'{len(self.current_image_dir) - 1:05d}')
    #     self.pred_text.setText(textline.predict)
    #     self.label_text.setText(textline.textline)
    #     self.loadImage(textline.image)

    #     #### Resize font
    #     # Use binary search to efficiently find the biggest font that will fit.
    #     max_size = 27
    #     min_size = 1
    #     font = self.label_text.font()
    #     while 1 < max_size - min_size:
    #         new_size = (min_size + max_size) // 2
    #         font.setPointSize(new_size)
    #         metrics = QFontMetrics(font)

    #         target_rect = self.label_text.contentsRect()

    #         # Be careful which overload of boundingRect() you call.
    #         rect = metrics.boundingRect(target_rect, Qt.AlignLeft, textline.textline)
    #         if (rect.width() > target_rect.width() or
    #                 rect.height() > target_rect.height()):
    #             max_size = new_size
    #         else:
    #             min_size = new_size

    #     font.setPointSize(min_size)
    #     self.label_text.setFont(font)

    #     pred_font = self.pred_text.font()
    #     pred_font.setPointSize(min_size)
    #     self.pred_text.setFont(pred_font)

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
        
        # self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), 0)
        # self.adjustScrollBar(self.scrollArea.verticalScrollBar(), 1.0)

        # self.current_path_label.setText(str(self.current_image_dir.image_path))
        # message = "{}, {}x{}, Depth: {}".format(self.current_image_dir.image_path, self.image.width(), self.image.height(), self.image.depth())
        # self.statusBar().showMessage(message)

    # def adjustScrollBar(self, scrollBar: QScrollBar, factor: float):
    #     scrollBar.setValue(int(factor * scrollBar.value()
    #                             + ((factor - 1) * scrollBar.pageStep()/2)))