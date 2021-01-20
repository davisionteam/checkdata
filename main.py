from data import Dataset
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow

from labelocr import LabelOCR
import yaml
WIN_SIZE = (1024, 128)


class App(QMainWindow):

    def __init__(self, label_dir: Path, config_path: Path):
        super().__init__()
        self.dataset = Dataset(label_dir)
        config = yaml.safe_load(open(config_path, 'rt'))
        root = LabelOCR(self.dataset, config)
        self.setCentralWidget(root)


if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]), Path(sys.argv[2]))
    window.showMaximized()
    # window.fixedText.setFocus()
    app.exec_()
