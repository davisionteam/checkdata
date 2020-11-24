from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QScrollArea
from PyQt5.QtGui import QPixmap, QPalette
from PIL import Image
from PIL.ImageQt import ImageQt
from typing import Dict, List, Optional
from pathlib import Path
import cv2
import numpy as np
from utils.utils import distance, _order_points, flatten_coords
import json


class CardViewer(QWidget):

    next_textline_handler = pyqtSignal(object)
    next_card_signal = pyqtSignal()
    prev_card_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setFixedSize(800, 600)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setVisible(True)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setAlignment(Qt.AlignHCenter)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scrollArea.setFixedSize(800, 600)
        self.setFixedSize(800, 600)

    @pyqtSlot(str, str, str)
    def on_set_card(self, image_path, json_path, json_diff_path):
        self.json_path = json_path
        self.full_image = Image.open(image_path)
        self.card_json = json.load(open(json_path, encoding='utf8'))

        self.card_image, self.card_location = self.extract_card(self.full_image, self.card_json)
        self.textlines = self.extract_textlines(json_diff_path)
        print(json_path, len(self.textlines))
        if len(self.textlines) == 0:
            print(f'Nothing to do with {image_path}')
            self.next_card_signal.emit()
            return

        self.image = ImageQt(self.card_image)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
        # self.imageLabel.setFixedSize(self.card_image.size[0], self.card_image.size[1])
        # self.imageLabel.adjustSize()
        # self.scrollArea.setFixedSize(self.imageLabel.size())
        # self.scrollArea.adjustSize()

        self.adjustSize()

        self.current_textline_idx = -1
        self.on_next_textline()

    @pyqtSlot(str)
    def on_update_textline_label(self, new_text):
        textline = self.textlines[self.current_textline_idx]
        textline.textline = new_text

    @pyqtSlot(str)
    def on_update_textline_classname(self, new_classname):
        textline = self.textlines[self.current_textline_idx]
        textline.class_name = new_classname

    @pyqtSlot()
    def on_next_textline(self):
        self._set_line_index(self.current_textline_idx + 1)

    @pyqtSlot()
    def on_prev_textline(self):
        self._set_line_index(self.current_textline_idx - 1)

    def _set_line_index(self, idx):
        self.save()
        if idx >= len(self.textlines):
            self.next_card_signal.emit()
        elif idx < 0:
            self.prev_card_signal.emit()
        else:
            self.current_textline_idx = idx
            textline = self.textlines[self.current_textline_idx]
            self._highlight_textline()
            self.next_textline_handler.emit(textline)

    def _highlight_textline(self):
        assert len(self.card_location) == 4
        textline = self.textlines[self.current_textline_idx]
        textline_coords = _order_points(textline.coords)
        x_min = min([x for (x, y) in self.card_location])
        y_min = min([y for (x, y) in self.card_location])
        textline_location = [(abs(text_x - x_min), abs(text_y - y_min)) for (text_x, text_y) in textline_coords]

        from PIL import ImageDraw
        back = self.card_image.copy()
        poly = self.card_image.copy()
        pdraw = ImageDraw.Draw(poly)
        pdraw.polygon(textline_location, fill=(200,0,0),outline=(255,0,0))
        back = Image.blend(back, poly, alpha=0.2)

        self.image = ImageQt(back)
        self.imageLabel.setPixmap(QPixmap.fromImage(self.image))

    def extract_card(self, pil_image, json_dict):
        for shape in json_dict['shapes']:
            if shape['label'] in ['CCCD_BACK', 'CCCD', 'BLX', 'BLX_back', 'CMND', 'CMND_back', 'CMCC']:
                points = shape['points']
                if len(points) > 4:
                    x_min = min([int(x) for (x, y) in points])
                    x_max = max([int(x) for (x, y) in points])
                    y_min = min([int(y) for (x, y) in points])
                    y_max = max([int(y) for (x, y) in points])
                    card_image = self.full_image.crop((x_min, y_min, x_max, y_max))
                    location = _order_points([[x_min, y_min], [x_max, y_max]])
                else:
                    points = _order_points(points)
                    cv_image = np.array(pil_image)
                    width = int(round((distance(points[0], points[1]) + distance(points[2], points[3])) / 2))
                    height = int(round((distance(points[0], points[3]) + distance(points[1], points[2])) / 2))
                    M = cv2.getPerspectiveTransform(np.float32(points), np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
                    image = cv2.warpPerspective(cv_image, M, (width, height))
                    location = points
                    card_image = Image.fromarray(image)
                return card_image, location
        return None, None

    def extract_textlines(self, json_diff_path: Path):
        textlines = []
        textlines_diff = json.load(open(json_diff_path, encoding='utf8'))
        for textline_diff in textlines_diff:
            predict_text = textline_diff['predict_text'].strip()
            ref = self.find_ref_by_coords(textline_diff['coords'])
            if ref is None:
                print(f'{textline_diff} does not have corresponding label in groundtruth')
                continue

            if 'value' not in ref.keys():
                print(f'Field "value" is not found in {ref}')
                continue

            textline = TextLine(ref, predict_text, self.full_image)
            textlines.append(textline)
        return textlines

    def __getitem__(self, idx):
        return self.textlines[idx]

    def find_ref_by_coords(self, coords: List) -> Optional[Dict]:
        for shape in self.card_json['shapes']:
            if len(shape['points']) != 4:
                # we know that textline must have 4 coords
                continue
            if self.is_same_coords(_order_points(shape['points']), _order_points(coords)):
                return shape
        return None

    def is_same_coords(self, coords1, coords2) -> bool:
        if isinstance(coords1, list):
            coords1 = flatten_coords(coords1)
        else:
            print('Current only support list type')
            return False
        if isinstance(coords2, list):
            coords2 = flatten_coords(coords2)
        else:
            print('Current only support list type')
            return False

        assert len(coords1) == len(coords2)
        for idx in range(len(coords1)):
            if abs(coords1[idx] - coords2[idx]) > 3:
                return False
        return True

    def __len__(self):
        return len(self.textlines)

    @pyqtSlot()
    def save(self):
        json.dump(self.card_json,
                  open(self.json_path, 'wt', encoding='utf8'),
                  indent=4,
                  ensure_ascii=False)

class TextLine():
    def __init__(self, ref: Dict, predict: str, image: Image.Image):
        self.ref = ref
        self.predict = predict
        self.full_image = image

    @property
    def textline(self) -> str:
        return self.ref['value']

    @textline.setter
    def textline(self, value):
        self.ref['value'] = value

    @property
    def coords(self):
        return self.ref['points']

    @property
    def class_name(self):
        return self.ref['label']

    @class_name.setter
    def class_name(self, new_name):
        self.ref['label'] = new_name

    @property
    def image(self):
        points = _order_points(self.coords)
        if isinstance(points, list):
            cv_image = np.array(self.full_image)
            width = int(round((distance(points[0], points[1]) + distance(points[2], points[3])) / 2))
            height = int(round((distance(points[0], points[3]) + distance(points[1], points[2])) / 2))

            M = cv2.getPerspectiveTransform(np.float32(points), np.float32([[0, 0], [width, 0], [width, height], [0, height]]))
            image = cv2.warpPerspective(cv_image, M, (width, height))

            textline_image = Image.fromarray(image)
        elif isinstance(points, str):
            points = points.strip()
            x, y, w, h = [int(item) for item in points.split()]
            textline_image = self.full_image.crop((x, y, x + w, y + h))
        else:
            print('Unknow type of "coords"')
            exit(-1)
        return textline_image