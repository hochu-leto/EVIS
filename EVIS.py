"""
Сейчас программа умеет
    подключается к машине по двойному щелчку на параметре или по кнопке

    Определяет все имеющиеся блоки по обоим КАН шинам
    При потере адаптера заново определяет все блоки
    Считывает все параметры из всех подключенных блоков
    Считывает все ошибки из всех подключенных блоков

    блок может сам
    запросить и удалить ошибки
    запросить серийник и версию ПО

    параметр как отдельный самостоятельный объект, может сам
    запросить параметр
    изменить параметр
    сохранение нужного значения параметра в блок - только для записываемых параметров - а как для старого кву

    сохраняет все параметры текущего блока в эксель файл - можно парраллельно с основным потоком, но лучше отключаться

следующие шаги
-  линуксе по квайзеру в виндовз сама определяет подключенный адаптер
- возможность выбрать параметры из разных блоков и сохранить их в отдельный список и
        хранить пользовательский список параметров в файле
        (вопрос как определять что этот список к этому блоку или к этой машине -
        при подключении к машине определить есть параметры из пользовательского списка на данной машине - как?)
- сравнение всех параметров из файла с текущими из блоков
- опрос и удаление ошибок ТАБа
- возможность записи текущих параметров из открытого списка и сохранять запись в эксель файл
- виджеты по управлению параметром
- поиск по имени и описанию параметра
 -- здесь нужно научиться парсить файлы с параметрами из старых программ
        - рткон и бурр-сеттингс, чтоб можно было сравнивать с текущими
- графики выбранных текущих параметров
- автоматическое определение нужного периода опроса параметра и сохранение этого периода в свойства параметра в файл

НА ПОДУМАТЬ
- продумать реляционную БД для параметров
- могут быть ещё и БМС БЗУ ИСН и иже с ними, хрен знает какие ещё блоки могут быть
использованы,  какими протоколами. Это должна быть расширяемая тема - объект EVO_Node
- у сущности должны быть свойства - ключевые параметры, описаны в листе с названием, размерностями и используемым виджетом
- на отдельном листе список ошибок, и что с ними делать, возможно даже список параметров,
которые следует проверять при этой ош ибке, какие-то рекомендации по ремонту, схемы, ссылки
- на отдельном листе управление для этого блока с виджетами типами - слайдеры, кнопки, чекбоксы - по каким адресам,
  название и так далее.
- добавлять блок в список имеющихся и
выводить в соседнем окошке список определённых для этого блока виджетов (слайдеры, кнопки) + количество этих окошек с
виджетами для каждого блока задаёт пользователь, т.е. он может создать свои нужные виджеты и сохранить их в профиль к
этому блоки, а при загрузке это должно подгрузится - и стандартные и выбранные для того блока пользователем -
полагаю отдельный лист Экселя с выбранными параметрами - виджетами
- Должно быть две кнопки - запись текущих параметров в Эксель файл и запись всех параметров текущего блока
- ещё кнопка - загрузка параметров из файла - здесь должна быть жёсткая защита - не все редактируемые параметры
 из одного блока можно напрямую заливать в другой. Или их ограничить до минимума или предлагать делать изменение вручную
- На каждый блок в экселе - лист со свойствами, лист со всеми возможными параметрами + один лист с заголовками
и подзаголовком параметры для каждой страницы - парсить как для БУРР

"""
import sys
from PyQt5.QtCore import pyqtSlot, Qt, QRegExp
from PyQt5.QtGui import QIcon, QColor, QPixmap, QRegExpValidator
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow, QTreeWidgetItem, QDialog, \
    QSplashScreen
import pathlib

import VMU_monitor_ui
from CANAdater import CANAdapter
from EVONode import EVONode
from My_threads import SaveToFileThread, MainThread, save_params_dict_to_file
from Parametr import Parametr
from work_with_file import full_node_list
from helper import zero_del, NewParamsList, log_uncaught_exceptions, DialogChange, InfoMessage

can_adapter = CANAdapter()

dir_path = str(pathlib.Path.cwd())
# файл где все блоки, параметры, ошибки
vmu_param_file = 'table_for_params_new_VMU2.xlsx'
vmu_param_file = pathlib.Path(dir_path, 'Tables', vmu_param_file)
sys.excepthook = log_uncaught_exceptions


def modify_file():
    window.log_lbl.setText('ВСЁ ПОЧИНИЛОСЬ!!!!')

    # save_params_dict_to_file(window.thread.current_node.group_params_dict, 'first_file.xlsx',
    # window.thread.current_node.name)


def save_to_eeprom():
    err = ''
    for node in window.current_nodes_list:
        if node.save_to_eeprom:
            err += node.send_val(node.save_to_eeprom, can_adapter, value=1)
    if err:
        QMessageBox.critical(window, "Ошибка ", 'Настройки сохранить не удалось' + '\n' + err, QMessageBox.Ok)
        window.log_lbl.setText('Настройки в память НЕ сохранены, ошибка ' + err)
    else:
        QMessageBox.information(window, "Успешный успех!", 'Текущие настройки сохранены в EEPROM', QMessageBox.Ok)
        window.log_lbl.setText('Настройки сохранены в EEPROM')
        window.save_eeprom_btn.setEnabled(False)


def want_to_value_change():
    #  над разбивать, как минимум, на две функции
    current_cell = window.vmu_param_table.currentItem()
    c_row = current_cell.row()
    c_col = current_cell.column()
    c_text = current_cell.text()
    col_name = window.vmu_param_table.horizontalHeaderItem(current_cell.column()).text().strip().upper()
    current_param = window.thread.current_params_list[c_row]

    # меняем значение параметра
    if col_name == 'ЗНАЧЕНИЕ':
        # остановим поток, если он есть
        if window.thread.isRunning():
            window.connect_to_node()

        is_editable = True if Qt.ItemIsEditable & current_cell.flags() else False
        if is_editable:
            dialog = DialogChange(current_param.name, c_text.strip())
            reg_ex = QRegExp("[+-]?([0-9]*[.])?[0-9]+")
            dialog.lineEdit.setValidator(QRegExpValidator(reg_ex))
            if dialog.exec_() == QDialog.Accepted:
                val = dialog.lineEdit.text()
                val = val if val and val != '-' else '0'
                # отправляю параметр, полученный из диалогового окна
                current_param.set_val(can_adapter, float(val))
                # и сразу же проверяю записался ли он в блок
                value_data = current_param.get_value(can_adapter)
                if isinstance(value_data, str):
                    new_val = ''
                else:
                    new_val = zero_del(value_data).strip()
                next_cell = window.vmu_param_table.item(c_row, c_col + 1)
                # и сравниваю их - соседняя ячейка становится зеленоватой, если ОК и красноватой если не ОК
                if val == new_val:
                    next_cell.setBackground(QColor(0, 254, 0, 30))
                    if window.thread.current_node.save_to_eeprom:
                        window.save_eeprom_btn.setEnabled(True)
                else:
                    next_cell.setBackground(QColor(254, 0, 0, 30))
                    # сбрасываю фокус с текущей ячейки, чтоб выйти красиво, при запуске потока и
                    # обновлении значения она снова станет редактируемой, пользователь не замечает изменений
                window.vmu_param_table.item(c_row, c_col).setFlags(current_cell.flags() & ~Qt.ItemIsEditable)
                # и запускаю поток
                window.connect_to_node()
    # добавляю параметр в Избранное/Новый список
    # пока редактирование старых списков не предусмотрено
    elif col_name == 'ПАРАМЕТР':
        user_node = window.current_nodes_list[len(window.current_nodes_list) - 1]
        new_param = Parametr(current_param.to_dict(), current_param.node)
        if window.thread.current_node != user_node:
            new_param.name = f'{new_param.name}#{new_param.node.name}'
        text = 'добавлен в список Избранное'
        if NewParamsList in user_node.group_params_dict.keys():
            p = None
            for par in user_node.group_params_dict[NewParamsList]:
                if par.name in new_param.name:
                    p = par
            if p:
                if window.thread.current_node == user_node and window.thread.isRunning():
                    window.connect_to_node()
                    user_node.group_params_dict[NewParamsList].remove(p)
                    window.connect_to_node()
                else:
                    user_node.group_params_dict[NewParamsList].remove(p)
                show_empty_params_list(window.thread.current_params_list, 'vmu_param_table')
                text = 'удалён из списка Избранное'
            else:
                user_node.group_params_dict[NewParamsList].append(new_param)
        else:
            user_node.group_params_dict[NewParamsList] = [new_param]
            item = QTreeWidgetItem()
            item.setText(0, NewParamsList)
            rowcount = window.nodes_tree.topLevelItemCount() - 1
            window.nodes_tree.topLevelItem(rowcount).addChild(item)
            window.nodes_tree.show()
        window.log_lbl.setText(f'Параметр {current_param.name} {text}')
        # info_m = InfoMessage(f'Параметр {current_param.name} {text}')
        # info_m.exec_()


def params_list_changed():  # если мы в левом окошке выбираем разные блоки или группы параметров
    is_run = False
    current_group_params = ''
    try:
        current_node_text = window.nodes_tree.currentItem().parent().text(0)
        current_group_params = window.nodes_tree.currentItem().text(0)
    except AttributeError:
        current_node_text = window.nodes_tree.currentItem().text(0)
    # определяю что за блок выбран
    for nod in window.current_nodes_list:
        if current_node_text in nod.name:
            window.thread.current_node = nod
            # если не выбрана какая-то конкретная, то выбираю первую группу блока
            if current_group_params:
                window.thread.current_params_list = nod.group_params_dict[current_group_params]
            else:
                window.thread.current_params_list = nod.group_params_dict[list(nod.group_params_dict.keys())[0]]
            break
    # тормозим поток
    if window.thread.isRunning():
        is_run = True
        window.connect_to_node()
    # отображаем имя блока, серийник и всё такое и обновляю список параметров в окошке справа
    window.show_node_name(window.thread.current_node)
    show_empty_params_list(window.thread.current_params_list, 'vmu_param_table')
    # и запускаю поток, если он был запущен
    if is_run and window.thread.isFinished():
        window.connect_to_node()
    return True


def show_empty_params_list(list_of_params: list, table='vmu_param_table'):
    show_table = getattr(window, table)
    show_table.setRowCount(0)
    show_table.setRowCount(len(list_of_params))
    row = 0
    # пока отображаю только три атрибута + само значение отображается позже
    for par in list_of_params:
        name = par.name
        unit = par.unit
        description = par.description

        if par.editable:
            color_opacity = 30
        else:
            color_opacity = 0
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        name_item.setBackground(QColor(0, 192, 0, color_opacity))
        show_table.setItem(row, 0, name_item)

        desc_item = QTableWidgetItem(description)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
        # desc_item.setBackground(QColor(0, 192, 0, color_opacity))
        show_table.setItem(row, 1, desc_item)

        value_item = QTableWidgetItem('')
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, 2, value_item)

        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, show_table.columnCount() - 1, unit_item)

        row += 1
    show_table.resizeColumnsToContents()


def check_node_online(all_node_list: list):
    exit_list = []
    # из всех возможных блоков выбираем те, которые отвечают на запрос серийника
    for nd in all_node_list:
        node_serial = nd.get_serial_number(can_adapter)
        if not isinstance(node_serial, str):
            nd.firmware_version = nd.get_firmware_version(can_adapter)
            exit_list.append(nd)

    if exit_list[0].cut_firmware() == 'EVOCARGO':
        return all_node_list, False

    window.nodes_tree.currentItemChanged.disconnect()
    window.show_nodes_tree(exit_list)
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    return exit_list, True


def erase_errors():
    is_run = False
    # останавливаем поток
    if window.thread.isRunning():
        is_run = True
        window.connect_to_node()
    # и трём все ошибки
    window.thread.errors_str = ''
    for nod in window.current_nodes_list:
        # метод удаления ошибок должен вернуть список ошибок, если они остались
        for err in nod.erase_errors(can_adapter):
            if err:
                window.thread.errors_str += f'{nod.name}: {err} \n'
    window.errors_browser.setText(window.thread.errors_str)
    # запускаем поток снова, если был остановлен
    if is_run and window.thread.isFinished():
        window.connect_to_node()


def save_to_file_pressed():  # если нужно записать текущий блок в файл
    # останавливаем поток
    if window.thread.isRunning():
        window.connect_to_node()
    window.connect_btn.setEnabled(False)
    window.save_to_file_btn.setEnabled(False)
    window.tr.adapter = can_adapter
    window.tr.node_to_save = window.thread.current_node
    window.save_to_file_btn.setText(f'Сохраняются настройки блока:\n {window.tr.node_to_save.name}')
    # запускаем параллельный поток сохранения
    window.tr.run()


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):
    record_vmu_params = False
    node_list_defined = False
    err_str = ''

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        self.current_nodes_list = []
        self.setWindowIcon(QIcon('pictures/icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread = MainThread()
        self.thread.current_nodes_list = self.current_nodes_list
        self.thread.threadSignalAThread.connect(self.add_new_vmu_params)
        self.thread.err_thread_signal.connect(self.add_new_errors)
        self.thread.adapter = can_adapter
        #  И для сохранения
        self.tr = SaveToFileThread()
        self.tr.adapter = can_adapter
        self.tr.SignalOfReady.connect(self.progress_bar_fulling)

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        global can_adapter
        # выясняем что вернул опрос параметров. Если параметр один и он текст - это ошибка подключения
        if len(list_of_params) < 2 and isinstance(list_of_params[0], str):
            err = str(list_of_params[0])
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
                QMessageBox.critical(self, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
            self.connect_btn.setText("Подключиться")
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
            if err == 'Адаптер не подключен':
                self.current_nodes_list = []
                # можно было бы избавиться от этой переменной, проверять, что список не пустой, но пусть будет
                self.node_list_defined = False
                can_adapter.isDefined = False
        else:
            self.show_new_vmu_params()

    @pyqtSlot(str)  # добавляем ошибки в окошко
    def add_new_errors(self, list_of_errors: str):
        self.errors_browser.setText(list_of_errors)

    @pyqtSlot(int, str, bool)
    def progress_bar_fulling(self, percent: int, err: str, is_finished: bool):
        # рисуем змейку прогресса
        window.node_nsme_pbar.setValue(percent)
        # выходим из потока если есть строка ошибки или файл сохранён
        if is_finished or err:
            self.tr.quit()
            self.tr.wait()

            if is_finished:
                QMessageBox.information(window, "Успешный успех!", 'Файл сохранён ' + '\n' + err, QMessageBox.Ok)
                self.log_lbl.setText('Сохранён файл с настройками ' + err)
            elif err:
                QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
                self.log_lbl.setText('Файл не сохранён, ошибка ' + err)
            self.node_nsme_pbar.setValue(0)

            self.connect_btn.setEnabled(True)
            self.save_to_file_btn.setEnabled(True)
            self.save_to_file_btn.setText(f'Сохранить настройки блока: \n {self.thread.current_node.name} в файл')
            self.connect_to_node()

    def double_click(self):  # можно подключиться по двойному щелчку по группе параметров
        # для Нового списка даю возможность изменить его название
        if self.nodes_tree.currentItem().text(0) == NewParamsList:
            if self.thread.current_params_list:
                dialog = DialogChange('Можно изменить название списка', NewParamsList)
                if dialog.exec_() == QDialog.Accepted:
                    val = dialog.lineEdit.text()
                    if val and val != NewParamsList:
                        # берём последний в списке блоков блок - Это Избранное
                        user_node = self.current_nodes_list[len(window.current_nodes_list) - 1]
                        # создаём в его словаре параметров ещё одну пару - копию нового списка
                        user_node.group_params_dict[val] = user_node.group_params_dict[NewParamsList].copy()
                        # а Новый список удаляем
                        del user_node.group_params_dict[NewParamsList]
                        # создаём новый итем для дерева
                        child_item = QTreeWidgetItem()
                        child_item.setText(0, val)
                        self.nodes_tree.currentItem().parent().addChild(child_item)
                        # а старый итем стираем
                        # может, это и неправильно и надо использовать модель-виев, но я пока не дорос
                        self.nodes_tree.currentItem().parent().removeChild(self.nodes_tree.currentItem())
                        self.log_lbl.setText(f'Добавление списка {val} в файл')
                        save_params_dict_to_file(self.thread.current_node.group_params_dict, vmu_param_file)
                    else:
                        print('Некорректное имя списка')
                        self.log_lbl.setText('Некорректное имя списка')
            else:
                print('Список пуст')
                self.log_lbl.setText('Список пуст')
        # для всех остальных - просто подключаемся
        if not self.thread.isRunning():
            self.connect_to_node()

    def show_new_vmu_params(self):
        row = 0
        for par in self.thread.current_params_list:
            v_name = par.value if isinstance(par.value, str) else zero_del(par.value)
            value_item = QTableWidgetItem(v_name)
            if par.editable:
                flags = (value_item.flags() | Qt.ItemIsEditable)
            else:
                flags = value_item.flags() & ~Qt.ItemIsEditable
            value_item.setFlags(flags)
            # подкрашиваем в голубой в зависимости от периода опроса
            color_opacity = int((150 / window.thread.max_iteration) * par.period) + 3
            value_item.setBackground(QColor(0, 255, 255, color_opacity))
            self.vmu_param_table.setItem(row, 2, value_item)
            row += 1
        self.vmu_param_table.resizeColumnsToContents()

    def show_nodes_tree(self, nds: list):
        cur_item = ''
        # запоминаю где сейчас курсор - тупо по тексту
        try:
            old_item_name = window.nodes_tree.currentItem().text(0)
        except AttributeError:
            old_item_name = ''

        self.nodes_tree.clear()
        self.nodes_tree.setColumnCount(1)
        self.nodes_tree.header().close()
        items = []

        for nd in nds:
            # создаю основные вкладки - названия блоков
            item = QTreeWidgetItem()
            item.setText(0, nd.name)
            if old_item_name == nd.name:
                # если если ранее выбранный блок среди имеющихся, запоминаю его
                cur_item = item
            for param_list in nd.group_params_dict.keys():
                # подвкладки - названия групп параметров
                child_item = QTreeWidgetItem()
                child_item.setText(0, str(param_list))
                item.addChild(child_item)
                # если ранее курсор стоял на группе, запоминаю ее
                if old_item_name == str(param_list):  # не работает для рулевых - нужно запоминать и имя блока тоже
                    cur_item = child_item
            items.append(item)

        self.nodes_tree.insertTopLevelItems(0, items)
        # если курсор стоял на блоке, который отсутствует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.nodes_tree.topLevelItem(0)
        self.nodes_tree.setCurrentItem(cur_item)
        # ... и текущий блок,соответственно, самый первый
        if self.thread.current_node not in nds:
            self.thread.current_node = nds[0]
        self.show_node_name(self.thread.current_node)

    def show_node_name(self, nd: EVONode):
        # чтоб юзер понимал в каком блоке он находится
        self.node_name_lab.setText(nd.name)
        self.node_s_n_lab.setText(f'Серийный номер: {nd.serial_number}')
        self.node_fm_lab.setText(f'Версия ПО: {nd.cut_firmware()}')
        if self.save_to_file_btn.isEnabled():
            self.save_to_file_btn.setText(f'Сохранить настройки блока:\n {nd.name} в файл')
        return

    def connect_to_node(self):
        global can_adapter
        # такое бывает при первом подключении или если вырвали адаптер - надо заново его определить
        if not can_adapter.isDefined:
            self.log_lbl.setText('Определяется подключенный адаптер...')
            can_adapter = CANAdapter()
        # наверное, это можно объединить, если вырвали адаптер, список тоже нужно обновлять,\
        # хотя когда теряем кан-шину также есть смысл обновить список подключенных блоков
        # надо это добавить!
        if not self.node_list_defined:
            self.log_lbl.setText('Определяются имеющиеся на шине CAN блоки...')
            self.current_nodes_list, check = check_node_online(alt_node_list)
            self.thread.current_nodes_list = self.current_nodes_list
            params_list_changed()
            self.reset_faults.setEnabled(check)
            self.save_to_file_btn.setEnabled(check)
            self.node_list_defined = check
            self.log_lbl.setText(f'Обнаружено {check * len(self.current_nodes_list)} блоков')

        if not self.thread.isRunning():
            self.thread.iter_count = 1
            self.thread.start()
            self.connect_btn.setText("Отключиться")
        else:
            self.thread.quit()
            self.thread.wait()
            self.connect_btn.setText("Подключиться")
            can_adapter.close_canal_can()

    def closeEvent(self, event):
        # может, есть смысл сделать из этого функцию, дабы не повторять дважды
        user_node_dict = self.current_nodes_list[len(window.current_nodes_list) - 1].group_params_dict

        if NewParamsList in user_node_dict.keys():
            if user_node_dict[NewParamsList]:
                dialog = DialogChange(f'В {NewParamsList} добавлены параметры \n'
                                      f' нужно сохранить этот список?', NewParamsList)
                if dialog.exec_() == QDialog.Accepted:
                    val = dialog.lineEdit.text()
                    self.log_lbl.setText(f'Добавление списка {val} в файл')
                    if val and val != NewParamsList:
                        user_node_dict[val] = user_node_dict[NewParamsList].copy()
                        del user_node_dict[NewParamsList]
                        save_params_dict_to_file(user_node_dict, vmu_param_file)
                    else:
                        self.log_lbl.setText('Некорректное имя списка')
            else:
                self.log_lbl.setText('Список не сохранён')
        msg = QMessageBox(self)
        msg.setWindowTitle("Выход")
        msg.setIcon(QMessageBox.Question)
        msg.setText("Вы уверены, что хотите закрыть приложение?")

        buttonAceptar = msg.addButton("Да", QMessageBox.YesRole)
        buttonCancelar = msg.addButton("Отменить", QMessageBox.RejectRole)
        msg.setDefaultButton(buttonAceptar)
        msg.exec_()

        if msg.clickedButton() == buttonAceptar:
            if self.thread:
                self.thread.quit()
                self.thread.wait()
                del self.thread
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
        else:
            event.ignore()


if __name__ == '__main__':

    app = QApplication([])
    splash = QSplashScreen()
    splash.setPixmap(QPixmap('pictures/EVO-EVIS_l.jpg'))
    splash.show()
    window = VMUMonitorApp()
    window.setWindowTitle('Electric Vehicle Information System')
    # подключаю сигналы нажатия на окошки
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    window.nodes_tree.doubleClicked.connect(window.double_click)
    window.vmu_param_table.cellDoubleClicked.connect(want_to_value_change)
    # и сигналы нажатия на кнопки
    window.connect_btn.clicked.connect(window.connect_to_node)
    window.save_eeprom_btn.clicked.connect(save_to_eeprom)
    window.reset_faults.clicked.connect(erase_errors)
    window.pushButton.clicked.connect(modify_file)
    window.save_to_file_btn.clicked.connect(save_to_file_pressed)
    window.save_to_file_btn.setEnabled(False)
    # заполняю первый список блоков из файла - максимальное количество всего, что может быть на нижнем уровне
    alt_node_list = full_node_list(vmu_param_file).copy()
    window.current_nodes_list = alt_node_list.copy()
    window.thread.current_nodes_list = window.current_nodes_list

    window.show_nodes_tree(alt_node_list)
    # если со списком блоков всё ок, показываем его в левом окошке и запускаем приложение
    if alt_node_list and params_list_changed():
        window.vmu_param_table.adjustSize()
        window.nodes_tree.adjustSize()
        if can_adapter.isDefined:
            window.connect_to_node()
        window.show()  # Показываем окно
        splash.finish(window)
        app.exec_()  # и запускаем приложение

# команды управления инвертором мэи в отдельной список с периодом 1001 - НЕ прокатило
# отдельное окошко с варнингами
# почему периодически после опроса всех блоков выдаёт - проверь связь с ватс и только перезагрузка
# сравнение с ранее сохранёнными параметрами
# не раскрывать таблицу во всю ширину
# сбрасывать список блоков на все блоки, когда пропал адаптер - наверное, нужно использовать копи
#
