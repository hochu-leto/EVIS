# subclass
import sys

from PyQt6 import QtWidgets, QtCore


class CheckableComboBox(QtWidgets.QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    def __init__(self, parent=None, parametr=None):
        super(CheckableComboBox, self).__init__(parent)
        self.view().pressed.connect(self.checkHandele)
        # self.currentIndexChanged.connect(self.checkHandele)
        # print(item.__dir__())

    def addItem(self, item, **kwargs):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1)
        # item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        # item.emitDataChanged()
        # item.model().itemChanged.connect(self.checkHandele)
        # print(item.__dir__())

    def itemChecked(self, index):
        print(index)
        item = self.model().item(index,0)
        return item.checkState() == QtCore.Qt.CheckState.Checked

    def checkHandele(self, index):
        # print(f'{state.text()=}, {state.row()=}, {state.checkState()=}')
        print(f'{index.row()=}')
        # getting the item
        item = self.model().itemFromIndex(index)
        # checking if item is checked
        if item.checkState() == QtCore.Qt.CheckState.Checked:
            # making it unchecked
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        # if not checked
        else:
            # making the item checked
            item.setCheckState(QtCore.Qt.CheckState.Checked)

# the basic main()
app = QtWidgets.QApplication(sys.argv)
dialog = QtWidgets.QMainWindow()
mainWidget = QtWidgets.QWidget()
dialog.setCentralWidget(mainWidget)
ComboBox = CheckableComboBox(mainWidget)
for i in range(16):
    ComboBox.addItem("Combobox Item " + str(i))
ComboBox.setCurrentText('Combobox Item 8')
dialog.show()
sys.exit(app.exec())