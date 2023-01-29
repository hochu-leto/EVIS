from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

colors = ['#7fc97f', '#beaed4', '#fdc086', '#ffff99', '#386cb0', '#f0027f', '#bf5b17', '#666666']


class MyDelegate(QItemDelegate):
    def __init__(self, parent=None, *args):
        QItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        if option.state & QStyle.StateFlag.State_Selected:
            # If the item is selected, always draw background red
            painter.setBrush(QBrush(QColor(qRgb(245, 0, 0))))
        else:
            c = index.data(Qt.ItemDataRole.BackgroundRole) # Get the color
            print(c)
            br = QBrush(QColor.fromString(c))
            br.setStyle(Qt.BrushStyle.Dense5Pattern)
            # painter.setBrush(QBrush(QColor.fromString(c)))
            # painter.setColor(QColor.fromString(c))
            painter.setBrush(br)

        # Draw the background rectangle
        painter.drawRect(option.rect)

        # Draw the bottom border
        # option.rect is the shape of the item; top left bottom right
        # e.g. 0, 0, 256, 16 in the parent listwidget
        # painter.setPen(QPen(QColor(qRgb(245, 0, 0))))
        # painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        # Draw the text
        painter.setPen(QPen(QColor(qRgb(0, 0, 0))))
        text = index.data(Qt.ItemDataRole.DisplayRole)
        # Adjust the rect (to pad)
        # option.rect.setLeft(5)
        # option.rect.setRight(option.rect.right()-5)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft, text)

        painter.restore()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        de = MyDelegate(self)
        w = QListWidget()
        w.setItemDelegate(de)
        for n in range(8):
            s = f'Привет {n}'
            i = QListWidgetItem()
            i.setData(Qt.ItemDataRole.DisplayRole, s) # The label
            i.setData(Qt.ItemDataRole.BackgroundRole, colors[n]) # The color
            w.addItem(i)

        self.setCentralWidget(w)

        self.show()


app = QApplication([])
w = MainWindow()
app.exec()
