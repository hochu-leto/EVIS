from PyQt6 import QtWidgets
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QDialog

from EVOParametr import type_values
from EVOWidgets import MyColorBar
from helper import DialogChange


def change_min(param):
    print(f'Задаю минимум для параметра {param.name}')
    dialog = DialogChange(label=f'Измени минимальное значение для {param.name}', value=str(param.min_value))
    reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
    dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
    if dialog.exec() == QDialog.DialogCode.Accepted:
        val = dialog.lineEdit.text()
        if val:
            val = float(val)
            if val < type_values[param.type]['min'] or \
                    val > param.max_value or \
                    val > param.value:
                val = param.min_value
            param.min_value = val


def change_max(param):
    print(f'Задаю максимум для параметра {param.name}')
    dialog = DialogChange(label=f'Измени максимальное значение для {param.name}', value=str(param.max_value))
    reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
    dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
    if dialog.exec() == QDialog.DialogCode.Accepted:
        val = dialog.lineEdit.text()
        if val:
            val = float(val)
            if val > type_values[param.type]['max'] or \
                    val < param.min_value or \
                    val < param.value:
                val = param.max_value
            param.max_value = val


def change_limit(param):
    print(f'Задаю пределы для параметра {param.name}')
    value_changer_dialog = DialogChange()

    reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
    max_lbl = QtWidgets.QLabel(value_changer_dialog)
    # max_lbl.setObjectName("max_lbl")
    max_lbl.setText('Задай максимальное значение параметра')
    value_changer_dialog.max_line_edit = QtWidgets.QLineEdit(value_changer_dialog)
    # max_line_edit.setObjectName("max_line_edit")
    value_changer_dialog.max_line_edit.setText(str(param.max_value))
    value_changer_dialog.max_line_edit.setValidator(QRegularExpressionValidator(reg_ex))

    min_lbl = QtWidgets.QLabel(value_changer_dialog)
    # min_lbl.setObjectName("min_lbl")
    min_lbl.setText('Задай минимальное значение параметра')
    value_changer_dialog.min_line_edit = QtWidgets.QLineEdit(value_changer_dialog)
    # min_line_edit.setObjectName("min_line_edit")
    value_changer_dialog.min_line_edit.setText(str(param.min_value))
    value_changer_dialog.min_line_edit.setValidator(QRegularExpressionValidator(reg_ex))

    value_changer_dialog.set_widgets(widgets_list=[max_lbl, value_changer_dialog.max_line_edit,
                                                   min_lbl, value_changer_dialog.min_line_edit])

    if value_changer_dialog.exec() == QDialog.DialogCode.Accepted:
        min_val = value_changer_dialog.min_line_edit.text()
        if min_val:
            val = float(min_val)
            if val < type_values[param.type]['min'] or \
                    val > param.max_value or \
                    val > param.value:
                val = param.min_value
            param.min_value = val
        max_val = value_changer_dialog.max_line_edit.text()
        if max_val:
            val = float(max_val)
            if val > type_values[param.type]['max'] or \
                    val < param.min_value or \
                    val < param.value:
                val = param.max_value
            param.max_value = val


def change_period(param):
    print(f'Меняю период параметра {param.name}')
    dialog = DialogChange(label=f'Измени период опроса для параметра {param.name} (1-1000)', value=str(param.period))
    reg_ex = QRegularExpression("^([1-9][0-9]{0,2}|1000)$")
    dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
    if dialog.exec() == QDialog.DialogCode.Accepted:
        val = dialog.lineEdit.text()
        if val:
            param.period = int(val)

