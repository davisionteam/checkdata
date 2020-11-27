import sys
from pathlib import Path
from typing import List

from PyQt5.QtCore import (QEvent, QObject, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                             QSizePolicy, QVBoxLayout, QWidget)

from widgets.card_viewer import CardViewer
from widgets.class_editor import ClassEditor
from widgets.index_widget import IndexWidget
from widgets.textline_editor import TextLineEditor

WIN_SIZE = (1024, 128)


class Dataset(QObject):
    new_card = pyqtSignal(str, str)

    def __init__(self, acc_dir: Path):
        super().__init__()
        ext_list = ['jpg', 'jpeg', 'png']
        ext_list.extend([x.upper() for x in ext_list])
        ext_list = [f'**/*.{ext}' for ext in ext_list]

        self.acc_images: List[Path] = sum([sorted(list(acc_dir.glob(pattern))) for pattern in ext_list], [])
        self.acc_jsons = [image.with_suffix('.json') for image in self.acc_images]
        # self.acc_json_diff = [image.with_name(image.stem + '_checked.json') for image in self.acc_images]
        self.accs = list(zip(self.acc_images, self.acc_jsons))
        # for image_path, json_path, json_diff_path in zip(self.acc_images, self.acc_jsons, self.acc_json_diff):
        #     acc_file = ImageDir(image_path, json_path, json_diff_path)
        #     if len(acc_file) > 0:
        #         self.accs.append(acc_file)
        self.current_card_idx = -1

    def __getitem__(self, idx):
        return self.accs[idx]

    def __len__(self):
        return len(self.accs)

    @pyqtSlot(int)
    def on_request_card_index(self, index: int):
        if 0 <= index < len(self):
            self.current_card_idx = index
            image_path, json_path = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path)

    @pyqtSlot()
    def on_request_next_card(self):
        if self.current_card_idx >= len(self):
            print('End!')
            return None
        else:
            self.current_card_idx += 1
            image_path, json_path = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path)

    @pyqtSlot()
    def on_request_prev_card(self):
        if self.current_card_idx < 0:
            print('End!')
        else:
            self.current_card_idx -= 1
            image_path, json_path = list(map(str, self.accs[self.current_card_idx]))
            self.new_card.emit(image_path, json_path)


class App(QMainWindow):

    next_line_signal = pyqtSignal()
    prev_line_signal = pyqtSignal()
    next_card_signal = pyqtSignal()
    prev_card_signal = pyqtSignal()

    def __init__(self, acc_dir):
        super().__init__()
        self.dataset = Dataset(acc_dir)

        left_layout = QVBoxLayout()

        index_selector = IndexWidget(self.dataset)
        index_selector.on_change.connect(self.dataset.on_request_card_index)
        left_layout.addWidget(index_selector)

        card_viewer = CardViewer()
        left_layout.addWidget(card_viewer)

        right_layout = QVBoxLayout()
        class_editor = ClassEditor()
        right_layout.addWidget(class_editor)

        textline_editor = TextLineEditor()
        right_layout.addWidget(textline_editor)

        card_viewer.next_textline_handler.connect(textline_editor.on_new_textline)
        card_viewer.next_textline_handler.connect(class_editor.on_new_textline)
        card_viewer.next_card_signal.connect(index_selector.update_card_index)
        card_viewer.prev_card_signal.connect(index_selector.update_card_index)
        card_viewer.next_card_signal.connect(self.dataset.on_request_next_card)
        card_viewer.prev_card_signal.connect(self.dataset.on_request_prev_card)
        self.dataset.new_card.connect(index_selector.update_card_index)
        self.dataset.new_card.connect(card_viewer.on_set_card)
        textline_editor.on_change.connect(card_viewer.on_update_textline_label)
        textline_editor.on_done.connect(card_viewer.on_next_textline)
        class_editor.on_class_name_change.connect(card_viewer.on_update_textline_classname)
        self.next_line_signal.connect(card_viewer.on_next_textline)
        self.prev_line_signal.connect(card_viewer.on_prev_textline)
        self.next_card_signal.connect(self.dataset.on_request_next_card)
        self.prev_card_signal.connect(self.dataset.on_request_prev_card)

        root = QWidget()
        layout = QHBoxLayout(root)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(left_widget)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        # right_widget.setFixedWidth(800)
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(right_widget)
        root.adjustSize()
        self.setCentralWidget(root)
        self.adjustSize()
        # self.showMaximized()
        self.installEventFilter(self)

        # set the first line of the first card
        self.dataset.on_request_next_card()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress):
            if event.key() == Qt.Key_Down:
                self.next_line_signal.emit()
            elif event.key() == Qt.Key_Up:
                self.prev_line_signal.emit()
            elif event.key() == Qt.Key_PageDown:
                self.next_card_signal.emit()
            elif event.key() == Qt.Key_PageUp:
                self.prev_card_signal.emit()
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication([])
    window = App(Path(sys.argv[1]))
    window.show()
    # window.fixedText.setFocus()
    app.exec_()
