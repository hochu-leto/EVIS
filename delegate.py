import sys

from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QTreeWidget, QTreeWidgetItem


class SelectionColorDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super(SelectionColorDelegate, self).__init__(parent)

    def initStyleOption(self, option, index):
        # let the base class initStyleOption fill option with the default values
        super(SelectionColorDelegate, self).initStyleOption(option, index)
        # override what you need to change in option
        if option.state & QStyle.StateFlag.State_Selected:
            option.state &= ~ QStyle.StateFlag.State_Selected
            option.backgroundBrush = QBrush(QColor(100, 200, 100, 200))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    treeWidget = QTreeWidget()
    treeWidget.setColumnCount(2)
    for i in range(5):
        item = QTreeWidgetItem(["Item %d" % i, "data"])
        treeWidget.addTopLevelItem(item)
        for j in range(3):
            subItem = QTreeWidgetItem(["SubItem %d, %d" % (i, j), "subdata"])
            item.addChild(subItem)
        treeWidget.expandItem(item)

    treeWidget.setItemDelegate(SelectionColorDelegate(treeWidget))
    treeWidget.show()

    app.exec()
    sys.exit()