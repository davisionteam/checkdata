from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QVBoxLayout
from PyQt5.QtGui import QPixmap, QPalette
from PIL import Image
from PIL.ImageQt import ImageQt
from typing import Dict, List, Optional
from pathlib import Path
import cv2
import numpy as np
from utils.utils import distance, _order_points, flatten_coords, transform
import json
from PIL import ImageDraw
from .shape_editor import Shape
from .image_viewer import ImageView

class CardViewer(QWidget):

    nextShapeHandler = pyqtSignal(object)
    next_card_signal = pyqtSignal()
    prev_card_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        self.imageViewer = ImageView()
        layout.addWidget(self.imageViewer)
        self.adjustSize()

    @pyqtSlot(str, str)
    def on_set_card(self, image_path, json_path):
        self.json_path = json_path
        self.full_image = Image.open(image_path)
        self.card_json = json.load(open(json_path, encoding='utf8'))

        self.card_image, self.card_location, self.M = self.extract_card(self.full_image, self.card_json)
        self.shapes = self.extract_shapes(self.full_image, self.card_json)
        print(json_path, len(self.shapes))
        if len(self.shapes) == 0:
            print(f'Nothing to do with {image_path}')
            self.next_card_signal.emit()
            return

        self.imageViewer.setImage(self.card_image)
        self.adjustSize()

        self.current_textline_idx = -1
        self.on_next_textline()

    @pyqtSlot()
    def on_next_textline(self):
        self._set_line_index(self.current_textline_idx + 1)

    @pyqtSlot()
    def on_prev_textline(self):
        self._set_line_index(self.current_textline_idx - 1)

    def _set_line_index(self, idx):
        self.save()
        if idx >= len(self.shapes):
            self.next_card_signal.emit()
        elif idx < 0:
            self.prev_card_signal.emit()
        else:
            self.current_textline_idx = idx
            textline = self.shapes[self.current_textline_idx]
            self._highlight_textline()
            self.nextShapeHandler.emit(textline)

    def _highlight_textline(self):
        assert len(self.card_location) == 4
        textline = self.shapes[self.current_textline_idx]
        textline_coords = _order_points(textline.points)

        if self.M is None:
            x_min = min([x for (x, y) in self.card_location])
            y_min = min([y for (x, y) in self.card_location])
            textline_location = [(abs(text_x - x_min), abs(text_y - y_min)) for (text_x, text_y) in textline_coords]
        else:
            textline_location = transform(textline_coords, self.M)

        self.imageViewer.setImage(self.card_image)
        self.imageViewer.highlight(textline_location)

    def extract_card(self, pil_image, json_dict):
        for shape in json_dict['shapes']:
            if shape['label'].upper() in ['CCCD_BACK', 'CCCD', 'BLX', 'BLX_BACK', 'CMND', 'CMND_BACK', 'CMCC', 'RECEIPT']:
                points = shape['points']
                if len(points) > 4:
                    x_min = min([int(x) for (x, y) in points])
                    x_max = max([int(x) for (x, y) in points])
                    y_min = min([int(y) for (x, y) in points])
                    y_max = max([int(y) for (x, y) in points])
                    card_image = self.full_image.crop((x_min, y_min, x_max, y_max))
                    location = _order_points([[x_min, y_min], [x_max, y_max]])
                    M = None
                else:
                    points = _order_points(points)
                    cv_image = np.array(pil_image)
                    width = int(round((distance(points[0], points[1]) + distance(points[2], points[3])) / 2))
                    height = int(round((distance(points[0], points[3]) + distance(points[1], points[2])) / 2))
                    M = cv2.getPerspectiveTransform(np.float32(points), np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
                    image = cv2.warpPerspective(cv_image, M, (width, height))
                    location = points
                    card_image = Image.fromarray(image)
                return card_image, location, M
        return None, None

    def extract_shapes(self, pil_image, json_dict):
        shapes = []
        for shape in json_dict['shapes']:
            if shape['label'] not in ['CCCD_BACK', 'CCCD', 'BLX', 'BLX_BACK', 'CMND', 'CMND_BACK', 'CMCC', 'RECEIPT']:
                shape = Shape(shape, pil_image)
                shapes.append(shape)
        return shapes

    def __getitem__(self, idx):
        return self.shapes[idx]

    def __len__(self):
        return len(self.shapes)

    @pyqtSlot()
    def save(self):
        json.dump(self.card_json,
                  open(self.json_path, 'wt', encoding='utf8'),
                  indent=4,
                  ensure_ascii=False)
