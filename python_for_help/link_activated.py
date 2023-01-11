from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMainWindow

from VMU_monitor_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def link(self, linkStr):

        QDesktopServices.openUrl(QUrl(linkStr))

    def __init__(self):
        super(MainWindow, self).__init__()

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.label.linkActivated.connect(self.link)
        self.label.setText('<a href="http://stackoverflow.com/">Stackoverflow/</a>')