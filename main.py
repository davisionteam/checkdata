from data import Dataset
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow
from argparse import ArgumentParser
from labelocr import LabelOCR
import yaml
WIN_SIZE = (1024, 128)


class App(QMainWindow):

    def __init__(self, config_path: Path, label_dir: Path):
        super().__init__()
        self.dataset = Dataset(label_dir)
        config = yaml.safe_load(open(config_path, 'rt'))
        root = LabelOCR(self.dataset, config)
        self.setCentralWidget(root)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('config_path', type=Path, help='Configuration file')
    parser.add_argument('label_dir', type=Path, help='Directory containing the JSON annotation files')
    args = parser.parse_args()

    app = QApplication([])
    window = App(args.config_path, args.label_dir)
    window.showMaximized()
    app.exec_()
