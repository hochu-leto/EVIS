# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VMU_monitor_fake.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1086, 870)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setDocumentMode(False)
        MainWindow.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_2.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.node_fm_lab = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node_fm_lab.sizePolicy().hasHeightForWidth())
        self.node_fm_lab.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.node_fm_lab.setFont(font)
        self.node_fm_lab.setObjectName("node_fm_lab")
        self.horizontalLayout_2.addWidget(self.node_fm_lab)
        self.node_name_lab = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node_name_lab.sizePolicy().hasHeightForWidth())
        self.node_name_lab.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.node_name_lab.setFont(font)
        self.node_name_lab.setAlignment(QtCore.Qt.AlignCenter)
        self.node_name_lab.setObjectName("node_name_lab")
        self.horizontalLayout_2.addWidget(self.node_name_lab)
        self.node_s_n_lab = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node_s_n_lab.sizePolicy().hasHeightForWidth())
        self.node_s_n_lab.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.node_s_n_lab.setFont(font)
        self.node_s_n_lab.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.node_s_n_lab.setObjectName("node_s_n_lab")
        self.horizontalLayout_2.addWidget(self.node_s_n_lab)
        self.gridLayout_2.addWidget(self.groupBox, 0, 1, 1, 2)
        self.connect_btn = QtWidgets.QPushButton(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connect_btn.sizePolicy().hasHeightForWidth())
        self.connect_btn.setSizePolicy(sizePolicy)
        self.connect_btn.setMinimumSize(QtCore.QSize(0, 0))
        self.connect_btn.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.connect_btn.setFont(font)
        self.connect_btn.setObjectName("connect_btn")
        self.gridLayout_2.addWidget(self.connect_btn, 7, 0, 1, 1)
        self.reset_faults = QtWidgets.QPushButton(self.groupBox_3)
        self.reset_faults.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reset_faults.sizePolicy().hasHeightForWidth())
        self.reset_faults.setSizePolicy(sizePolicy)
        self.reset_faults.setObjectName("reset_faults")
        self.gridLayout_2.addWidget(self.reset_faults, 8, 0, 1, 1)
        self.nodes_tree = QtWidgets.QTreeWidget(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nodes_tree.sizePolicy().hasHeightForWidth())
        self.nodes_tree.setSizePolicy(sizePolicy)
        self.nodes_tree.setObjectName("nodes_tree")
        self.nodes_tree.headerItem().setText(0, "1")
        self.gridLayout_2.addWidget(self.nodes_tree, 0, 0, 6, 1)
        self.errors_browser = QtWidgets.QTextBrowser(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.errors_browser.sizePolicy().hasHeightForWidth())
        self.errors_browser.setSizePolicy(sizePolicy)
        self.errors_browser.setObjectName("errors_browser")
        self.gridLayout_2.addWidget(self.errors_browser, 7, 1, 2, 3)
        self.vmu_param_table = QtWidgets.QTableWidget(self.groupBox_3)
        self.vmu_param_table.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.vmu_param_table.sizePolicy().hasHeightForWidth())
        self.vmu_param_table.setSizePolicy(sizePolicy)
        self.vmu_param_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.vmu_param_table.setObjectName("vmu_param_table")
        self.vmu_param_table.setColumnCount(4)
        self.vmu_param_table.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.vmu_param_table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.vmu_param_table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.vmu_param_table.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.vmu_param_table.setHorizontalHeaderItem(3, item)
        self.gridLayout_2.addWidget(self.vmu_param_table, 1, 1, 5, 3)
        self.emergy_btn = QtWidgets.QPushButton(self.groupBox_3)
        self.emergy_btn.setObjectName("emergy_btn")
        self.gridLayout_2.addWidget(self.emergy_btn, 6, 0, 1, 1)
        self.gridLayout_2.setColumnStretch(1, 2)
        self.gridLayout_2.setColumnStretch(2, 3)
        self.gridLayout_2.setRowStretch(0, 9)
        self.horizontalLayout.addWidget(self.groupBox_3)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Теневая для диностенда"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Параметры"))
        self.groupBox.setTitle(_translate("MainWindow", "Текущий блок"))
        self.node_fm_lab.setText(_translate("MainWindow", "Версия ПО: "))
        self.node_name_lab.setText(_translate("MainWindow", "Блок"))
        self.node_s_n_lab.setText(_translate("MainWindow", "Серийный номер: "))
        self.connect_btn.setText(_translate("MainWindow", "Подключиться"))
        self.reset_faults.setText(_translate("MainWindow", "Сброс ошибок"))
        item = self.vmu_param_table.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Параметр"))
        item = self.vmu_param_table.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Описание"))
        item = self.vmu_param_table.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Значение"))
        item = self.vmu_param_table.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "Размерность"))
        self.emergy_btn.setText(_translate("MainWindow", "PushButton"))
