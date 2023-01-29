import random
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QStyledItemDelegate,
    QTableView,
    QWidget,
)

OPTIONS = {
    "human": ["header", "body", "hand", "foot"],
    "plant": ["root", "leaf", "flower"],
}


class Delegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.currentTextChanged.connect(self.handle_commit_close_editor)
        return editor

    def setEditorData(self, editor, index):
        if index.column() == 0:
            option = index.data()
            editor.clear()
            editor.addItems(list(OPTIONS.keys()))
            editor.setCurrentText(option)

        elif index.column() == 1:
            option = index.sibling(index.row(), 0).data()
            options = OPTIONS.get(option, [])
            editor.clear()
            editor.addItems(options)

    def setModelData(self, editor, model, index):
        if index.column() == 0:
            option = editor.currentText()
            model.setData(index, option, Qt.DisplayRole)
            options = OPTIONS.get(option, [])
            model.setData(
                index.sibling(index.row(), 1),
                options[0] if options else "",
                Qt.DisplayRole,
            )
        elif index.column() == 1:
            option = editor.currentText()
            model.setData(index, option, Qt.DisplayRole)

    def handle_commit_close_editor(self):
        editor = self.sender()
        if isinstance(editor, QWidget):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor)


def main():
    app = QApplication(sys.argv)

    app.setStyle("fusion")

    model = QStandardItemModel(0, 2)

    for i in range(4):
        option = random.choice(list(OPTIONS.keys()))
        item_1 = QStandardItem(option)
        item_2 = QStandardItem(random.choice(list(OPTIONS[option])))
        model.appendRow([item_1, item_2])

    view = QTableView()
    view.setModel(model)
    view.resize(640, 480)
    view.show()

    delegate = Delegate(view)
    view.setItemDelegate(delegate)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()