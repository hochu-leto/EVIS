import sys

import numpy
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QHBoxLayout, QApplication, QDockWidget, QListWidget, QPushButton, \
    QGraphicsProxyWidget, QGridLayout, QSizePolicy, QWidget
from pyqtgraph import PlotWidget, mkPen

import VMU_monitor_ui


class DockDemo(QMainWindow):
    chunkSize = 100
    maxChunks = 10
    pens = [mkPen(color=(0, 255, 0)), mkPen(color=(255, 0, 0)), mkPen(color=(0, 0, 255)),
            mkPen(color=(0, 255, 255)), mkPen(color=(255, 255, 0)), mkPen(color=(255, 0, 255))]

    def __init__(self, params_list=None, parent=None):
        super(DockDemo, self).__init__(parent)
        self.dock_widget = QDockWidget('Dockable', self)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.start_stop_btn = QPushButton('СТОП', parent=self.dockWidgetContents)
        self.start_stop_btn.setObjectName("start_stop_btn")
        self.gridLayout.addWidget(self.start_stop_btn, 0, 0, 1, 1)
        self.clear_btn = QPushButton('СБРОС', parent=self.dockWidgetContents)
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setEnabled(False)
        self.gridLayout.addWidget(self.clear_btn, 0, 7, 1, 1)
        self.plot_widget = PlotWidget(parent=self.dockWidgetContents)
        self.plot_widget.showGrid(x=True, y=True)
        self.gridLayout.addWidget(self.plot_widget, 1, 0, 1, 8)
        self.dock_widget.setWidget(self.dockWidgetContents)
        self.dock_widget.setFloating(False)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                     QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = DockDemo()
    window = VMUMonitorApp()
    window.label.deleteLater()
    window.gridLayout_5.addWidget(demo, 0, 0, 1, 1)
    window.show()  # Показываем окно

    sys.exit(app.exec())
