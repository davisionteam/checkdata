
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, pyqtSignal, qDebug, pyqtSlot
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QImage,
                         QImageReader, QImageWriter, QIntValidator, QKeyEvent,
                         QKeySequence, QPainter, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel, QComboBox,
                             QLineEdit, QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QScrollBar, QShortcut, QSizePolicy,
                             QVBoxLayout, QWidget)
from PIL import Image
from pathlib import Path
import yaml


class ClassEditor(QWidget):

    on_class_name_change = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        fields = [
            'O_DEPART',
            'HEADER', 'HEADING',
            'K_ID', 'V_ID',
            'K_NAME', 'V_NAME', 'V_NAME1', 'V_NAME2',
            'K_ONAME', 'V_ONAME',
            'K_BD', 'V_BD',
            'K_BP', 'V_BP1', 'V_BP2',
            'K_A', 'V_A1', 'V_A2',
            'K_SEX', 'V_SEX',
            'K_NAT', 'V_NAT',
            'K_ETH', 'V_ETH',
            'K_TL', 'V_TL',
            'K_REL', 'V_REL',
            'HEADING_FRI',
            'K_SPEC', 'V_SPEC1', 'V_SPEC2', 'V_SPEC3',
            'K_PRO', 'V_PRO', 'V_PRO1', 'V_PRO2',
            'DATE_ISS', 'DATE_1', 'DATE_2', 'DATE_3',
            'K_SIGN', 'K_SIGN1', 'K_SIGN2', 'V_SIGN', 'V_SIGN_NAME', 'SIGN_NAME',
            'K_VEH', 'K_VEH1', 'K_VEH2', 'V_VEH',
            'K_AD', 'K_AD1', 'K_AD2', 'V_AD',
            'K_C', 'K_CA1', 'K_CA2', 'K_CA3', 'K_CA4', 'K_CB1', 'K_CB2', 'K_CC', 'K_CD', 'K_CE', 'K_CF',
            'V_C', 'V_CA1', 'V_CA2', 'V_CA3', 'V_CA4', 'V_CB1', 'V_CB2', 'V_CC', 'V_CD', 'V_CE', 'V_CF',
            'FRAME_ID',
            'K_MR', 'V_MR',
            'K_BG', 'V_BG',
        ]

        layout = QVBoxLayout()

        label = QLabel('Field Class:')
        layout.addWidget(label)

        self.combo_box = QComboBox(self)
        self.combo_box.setEditable(True)
        self.combo_box.addItems(fields)
        self.combo_box.currentTextChanged.connect(self._on_text_change)
        self.combo_box.currentIndexChanged.connect(self._on_index_change)
        self.combo_box.setInsertPolicy(QComboBox.NoInsert)
        layout.addWidget(self.combo_box)

        self.setLayout(layout)
        self.adjustSize()

    def _on_text_change(self, new_text):
        self.on_class_name_change.emit(new_text)

    def _on_index_change(self, index):
        self.on_class_name_change.emit(self.combo_box.currentText())

    @pyqtSlot(object)
    def on_new_textline(self, textline):
        self.current_class_name = textline.class_name
        self.combo_box.setCurrentText(self.current_class_name)

    @pyqtSlot()
    def reject_if_invalid(self):
        class_name = self.combo_box.currentText()
        if self.combo_box.findText(class_name, Qt.MatchExactly) < 0:
            QMessageBox.warning(self, 'Warning', f'Invalid Field Class = {class_name}. Please choose one from the list')
            self._on_text_change(self.current_class_name) # reset previous class_name

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