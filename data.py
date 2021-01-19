from pathlib import Path
from typing import List
from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)


class Dataset(QObject):
    item = pyqtSignal(str, str)

    def __init__(self, acc_dir: Path):
        super().__init__()
        extList = ['jpg', 'jpeg', 'png']
        extList.extend([x.upper() for x in extList])
        extList = [f'**/*.{ext}' for ext in extList]

        self.imagePaths: List[Path] = sum([sorted(list(acc_dir.glob(pattern))) for pattern in extList], [])
        self.jsonPaths = [image.with_suffix('.json') for image in self.imagePaths]
        self.currentIdx = 0

    def __getitem__(self, idx):
        imagePath = self.imagePaths[idx]
        jsonPath = self.jsonPaths[idx]
        return str(imagePath), str(jsonPath)

    def __len__(self):
        return len(self.imagePaths)

    @pyqtSlot(int)
    def itemAt(self, index: int):
        if 0 <= index < len(self):
            self.currentIdx = index
            imagePath, jsonPath = self[index]
            self.item.emit(imagePath, jsonPath)

    @pyqtSlot()
    def next(self):
        if self.currentIdx + 1 < len(self):
            self.itemAt(self.currentIdx + 1)

    @pyqtSlot()
    def prev(self):
        if self.currentIdx - 1 >= 0:
            self.itemAt(self.currentIdx - 1)
