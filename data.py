from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
import json
import re


class Dataset(QObject):
    item = pyqtSignal(str, str)
    indexChanged = pyqtSignal(int)

    def __init__(self, acc_dir: Path):
        super().__init__()
        extList = ['jpg', 'jpeg', 'png']
        extList.extend([x.upper() for x in extList])
        extList = [f'**/*.{ext}' for ext in extList]

        self.imagePaths: List[Path] = sum([sorted(list(acc_dir.glob(pattern))) for pattern in extList], [])
        self.jsonPaths = [image.with_suffix('.json') for image in self.imagePaths]
        self.currentIdx = -1

    def __getitem__(self, idx):
        imagePath = self.imagePaths[idx]
        jsonPath = self.jsonPaths[idx]
        return str(imagePath), str(jsonPath)

    def __len__(self):
        return len(self.imagePaths)

    @pyqtSlot(int)
    def itemAt(self, index: int):
        if 0 <= index < len(self):
            if index != self.currentIdx:
                self.currentIdx = index
                imagePath, jsonPath = self[index]
                self.item.emit(imagePath, jsonPath)
                self.indexChanged.emit(self.currentIdx)

    @pyqtSlot()
    def next(self):
        self.itemAt(self.currentIdx + 1)

    @pyqtSlot()
    def prev(self):
        self.itemAt(self.currentIdx - 1)


class Shape():
    def __init__(self, shape):
        self.label = shape['label']
        self.points = shape['points']
        self.type = shape['shape_type']
        self.group_id = shape['group_id']
        self.flags = shape['flags']
        self.value = shape.get('value', None)

    def __repr__(self) -> str:
        return f'Shape({self.label}, {self.points})'


class Annotation():
    def __init__(self, image_path, image_height, image_width, shapes, patterns: Optional[List[str]] = None):
        self.image_path = image_path
        self.image_width = image_width
        self.image_height = image_height
        self.allShapes = list(map(Shape, shapes))
        self.currentIdx = 0

        self.shapes: List[Shape]
        if patterns is not None:
            self.shapes = []
            patternsCompiled = [re.compile(pattern) for pattern in patterns]
            for shape in self.allShapes:
                for pattern in patternsCompiled:
                    if pattern.match(shape.label):
                        self.shapes.append(shape)
        else:
            self.shapes = self.allShapes

    def __iter__(self):
        for shape in self.shapes:
            yield shape

    def __len__(self):
        return len(self.shapes)

    def __repr__(self) -> str:
        shapes = self.shapes[:5]
        repr = f'Annotation({self.image_path}, {self.image_width}x{self.image_height}, {len(self.shapes)}):\n'
        for shape in shapes:
            repr += f'\t{shape.__repr__()}\n'
        if len(shapes) > 5:
            repr += '...\n'
        return repr

    def __getitem__(self, idx):
        return self.shapes[idx]

    def next(self):
        self.currentIdx = min(self.currentIdx + 1, len(self) - 1)
        return self.shapes[self.currentIdx]

    def prev(self):
        self.currentIdx = max(self.currentIdx - 1, 0)
        return self.shapes[self.currentIdx]

    def keep_labels(self, labels: List[str]):
        self.shapes = [shape for shape in self.shapes if shape.label in labels]

    def remove_labels(self, labels: List[str]):
        self.shapes = [shape for shape in self.shapes if shape.label not in labels]

    @classmethod
    def parse_from_labelme(cls, json_path, *args, **kwargs):
        json_dict = json.load(open(json_path, 'rt'))
        return cls(json_dict['imagePath'],
                   json_dict['imageHeight'],
                   json_dict['imageWidth'],
                   json_dict['shapes'],
                   *args,
                   **kwargs)

    def find(self, labels: List[str], first: bool = False):
        results: List[Shape] = []
        for shape in self.shapes:
            if shape.label in labels:
                results.append(shape)

        if len(results) == 0 and first:
            return None
        elif first:
            return results[0]
        else:
            return results

    def add_shapes(self, shapes: List[Shape]):
        self.shapes.extend(shapes)

    def remove_shapes(self, shapes: List[Shape]):
        self.shapes = [shape for shape in self.shapes if shape not in shapes]

    def to_json(self, path: Path):
        # print(json.dumps(anno_new.__dict__, default=serializer))
        json.dump(self, open(path, 'wt', encoding='utf8'), ensure_ascii=False, indent=4, default=labelme_serializer)


def labelme_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, Annotation):
        d = {
            'version': '4.5.6',
            'flags': {},
            'shapes': obj.allShapes,
            'imageData': None,
            'imagePath': obj.image_path,
            'imageHeight': obj.image_height,
            'imageWidth': obj.image_width,
        }
        return d

    if isinstance(obj, Shape):
        d = {
            'label': obj.label,
            'points': obj.points,
            "group_id": obj.group_id,
            "shape_type": obj.type,
            "flags": obj.flags,
        }
        if obj.value is not None:
            d['value'] = obj.value
        return d

    return obj.__dict__
