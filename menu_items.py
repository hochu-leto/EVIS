from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QDialog

from EVOParametr import type_values
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


def change_period(param):
    print(f'Меняю период параметра {param.name}')
    dialog = DialogChange(label=f'Измени период опроса для параметра {param.name} (1-1000)', value=str(param.period))
    reg_ex = QRegularExpression("^([1-9][0-9]{0,2}|1000)$")
    dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
    if dialog.exec() == QDialog.DialogCode.Accepted:
        val = dialog.lineEdit.text()
        if val:
            param.period = int(val)


#  надо продумать как в онлайне добавлять виджеты к параметру,
#  чтоб они изменялись во время опроса и чтоб при загрузке списка параметров,
#  если эти  виджеты уже установлены, они тоже должны быть.
#  Также продумать ка при изменении минимума или максимума изображение виджета также менялось
def set_slider(param):
    pass


def set_bar(param):
    pass
