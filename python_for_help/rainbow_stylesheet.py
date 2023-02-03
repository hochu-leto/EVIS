import os
import sys
import qrainbowstyle

# set the environment variable to use a specific wrapper
# it can be set to pyqt, pyqt5, or pyside2
# you do not need to use QtPy to set this variable
os.environ['QT_API'] = 'pyqt5'

# import from QtPy instead of doing it directly
# note that QtPy always uses PyQt5 API
from qtpy import QtWidgets

# create the application and the main window
app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()

# setup stylesheet
# the default system in qrainbowstyle uses qtpy environment variable
app.setStyleSheet(qrainbowstyle.load_stylesheet())

# run
window.show()
app.exec_()
