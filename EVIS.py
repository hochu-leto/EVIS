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
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QTimer, QEventLoop, QRegExp
from PyQt5.QtGui import QIcon, QColor, QRegExpValidator, QKeyEvent, QPixmap
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow, QTreeWidgetItem, QDialog, \
    QSplashScreen
import pathlib
import VMU_monitor_ui
import my_dialog
from CANAdater import CANAdapter
from EVONode import EVONode
from My_threads import SaveToFileThread, MainThread
from Parametr import Parametr
from work_with_file import full_node_list
from helper import zero_del, NewParamsList, log_uncaught_exceptions

can_adapter = CANAdapter()

dir_path = str(pathlib.Path.cwd())
# файл где все блоки, параметры, ошибки
vmu_param_file = 'table_for_params_new_VMU2.xlsx'
sys.excepthook = log_uncaught_exceptions


# поток для опроса параметров и ошибок
# class AThread(QThread):
#     # сигнал со списком параметров из текущей группы
#     threadSignalAThread = pyqtSignal(list)
#     # сигнал с ошибками
#     err_thread_signal = pyqtSignal(str)
#     max_iteration = 1000
#     iter_count = 1
#     current_params_list = []
#     current_node = EVONode()
#
#     def __init__(self):
#         super().__init__()
#
#     def run(self):
#
#         def emitting():  # передача заполненного списка параметров
#             self.threadSignalAThread.emit(self.ans_list)
#             self.params_counter = 0
#             self.errors_counter = 0
#             self.ans_list = []
#             self.iter_count += 1
#             if self.iter_count > self.max_iteration:  # это нужно для периода опроса от 1 до 1000 и снова
#                 self.iter_count = 1
#
#         def request_node():
#             if not self.len_param_list:
#                 self.threadSignalAThread.emit(['Пустой список'])
#                 return
#             if not self.iter_count == 1:
#                 while not self.iter_count % self.current_params_list[self.params_counter].period == 0:
#                     # если период опроса текущего параметра не кратен текущей итерации,
#                     # заполняем его нулями, чтоб в таблице осталось его старое значение
#                     # и запрашиваем следующий параметр. Это ускоряет опрос параметров с малым периодом опроса
#                     self.ans_list.append(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
#                     self.params_counter += 1
#                     if self.params_counter >= self.len_param_list:
#                         self.params_counter = 0
#                         emitting()
#                         return
#             param = self.current_params_list[self.params_counter].get_value(can_adapter)
#             # если строка - значит ошибка
#             if isinstance(param, str):
#                 self.errors_counter += 1
#                 if self.errors_counter >= self.max_errors:
#                     self.threadSignalAThread.emit([param])
#                     return
#             else:
#                 self.errors_counter = 0
#             # тут всё просто, собираем весь список и отправляем кучкой
#             self.ans_list.append(param)
#             self.params_counter += 1
#             if self.params_counter >= self.len_param_list:
#                 self.params_counter = 0
#                 emitting()
#
#         def request_errors():
#             errors_str = window.err_str
#             # опрос ошибок, на это время опрос параметров отключается
#             timer.stop()
#             for nd in window.current_nodes_list:
#                 errors = nd.check_errors(can_adapter)
#                 for error in errors:
#                     if error and error not in errors_str:
#                         errors_str += f'{nd.name} : {error} \n'
#             window.err_str = errors_str
#             self.err_thread_signal.emit(errors_str)
#             timer.start(send_delay)
#
#         send_delay = 13  # задержка отправки в кан сообщений методом подбора с таким не зависает
#         err_req_delay = 500
#         self.max_errors = 3
#         self.len_param_list = len(self.current_params_list)
#         if self.len_param_list < self.max_errors:
#             self.max_errors = self.len_param_list
#         self.ans_list = []
#         self.params_counter = 0
#         self.errors_counter = 0
#
#         timer = QTimer()
#         timer.timeout.connect(request_node)
#         timer.start(send_delay)
#
#         err_timer = QTimer()
#         err_timer.timeout.connect(request_errors)
#         err_timer.start(err_req_delay)
#
#         loop = QEventLoop()
#         loop.exec_()
#
#
def save_to_eeprom():
    err = ''
    for node in window.current_nodes_list:
        if node.save_to_eeprom:
            err += node.send_val(node.save_to_eeprom, can_adapter, value=1)
    if err:
        QMessageBox.critical(window, "Ошибка ", 'Настройки сохранить не удалось' + '\n' + err, QMessageBox.Ok)
    else:
        QMessageBox.information(window, "Успешный успех!", 'Текущие настройки сохранены в EEPROM', QMessageBox.Ok)
        window.save_eeprom_btn.setEnabled(False)


def want_to_value_change():  # меняем значение параметра
    # остановим поток, если он есть

    current_cell = window.vmu_param_table.currentItem()
    c_row = current_cell.row()
    c_col = current_cell.column()
    c_text = current_cell.text()
    col_name = window.vmu_param_table.horizontalHeaderItem(current_cell.column()).text().strip().upper()
    current_param = window.thread.current_params_list[c_row]

    if col_name == 'ЗНАЧЕНИЕ':
        if window.thread.isRunning():
            window.connect_to_node()

        is_editable = True if Qt.ItemIsEditable & current_cell.flags() else False
        if is_editable:
            dialog = DialogChange(current_param.name, c_text.strip())
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
                # и запускаю поток если он был включен
                # if is_run and window.thread.isFinished():
                window.connect_to_node()

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
                user_node.group_params_dict[NewParamsList].remove(p)
                text = 'удалён из списка Избранное'
                show_empty_params_list(user_node.group_params_dict[NewParamsList])
            else:
                user_node.group_params_dict[NewParamsList].append(new_param)
        else:
            user_node.group_params_dict[NewParamsList] = [new_param]
        QMessageBox.information(window, "Успешный успех!", f'Параметр {current_param.name} {text}', QMessageBox.Ok)


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

    # if not exit_list:
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
    # чтоб во время записи никто не поменял параметр, блокируем это
    # window.vmu_param_table.cellDoubleClicked.disconnect()
    window.tr.adapter = can_adapter
    window.tr.node_to_save = window.thread.current_node
    window.save_to_file_btn.setText(f'Сохраняются настройки блока: {window.tr.node_to_save.name}')
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
            elif err:
                QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
            self.node_nsme_pbar.setValue(0)

            # self.vmu_param_table.cellDoubleClicked.connect(want_to_value_change)
            self.connect_btn.setEnabled(True)
            self.save_to_file_btn.setEnabled(True)
            self.save_to_file_btn.setText(f'Сохранить настройки блока: {self.thread.current_node.name}')
            self.connect_to_node()

    def double_click(self):  # можно подключиться по двойному щелчку по группе параметров
        if not self.thread.isRunning():
            self.connect_to_node()

    def show_new_vmu_params(self):
        row = 0
        for par in self.thread.current_params_list:
            value_item = QTableWidgetItem(zero_del(par.value))
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
                if old_item_name == str(param_list):
                    cur_item = child_item
            items.append(item)

        self.nodes_tree.insertTopLevelItems(0, items)
        # если курсор стоял на блоке, который отсутвует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.nodes_tree.topLevelItem(0)
        self.nodes_tree.setCurrentItem(cur_item)
        # ... и текущий блок,соответсвенно, самый первый
        if self.thread.current_node not in nds:
            self.thread.current_node = nds[0]
        self.show_node_name(self.thread.current_node)

    def show_node_name(self, nd: EVONode):
        # чтоб юзер понимал в каком блоке он находится
        self.node_name_lab.setText(nd.name)
        self.node_s_n_lab.setText(f'Серийный номер: {nd.serial_number}')
        self.node_fm_lab.setText(f'Версия ПО: {nd.cut_firmware()}')
        if self.save_to_file_btn.isEnabled():
            self.save_to_file_btn.setText(f'Сохранить настройки блока: {nd.name}')
        return

    def connect_to_node(self):
        global can_adapter
        # такое бывает при первом подключении или если вырвали адаптер - надо заново его определить
        if not can_adapter.isDefined:
            can_adapter = CANAdapter()
        # наверное, это можно объединить, если вырвали адаптер, список тоже нужно обновлять,\
        # хотя когда теряем кан-шину также есть смысл обновить список подключенных блоков
        # надо это добавить!
        if not self.node_list_defined:
            self.current_nodes_list, check = check_node_online(alt_node_list)
            params_list_changed()
            self.reset_faults.setEnabled(check)
            self.save_to_file_btn.setEnabled(check)
            self.node_list_defined = check

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


class DialogChange(QDialog, my_dialog.Ui_value_changer_dialog):

    def __init__(self, value_name: str, value):
        super().__init__()
        self.setupUi(self)
        self.value_name_lbl.setText(value_name)
        self.lineEdit.setText(value)
        reg_ex = QRegExp("[+-]?([0-9]*[.])?[0-9]+")
        self.lineEdit.setValidator(QRegExpValidator(reg_ex))


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
    window.save_to_file_btn.clicked.connect(save_to_file_pressed)
    window.save_to_file_btn.setEnabled(False)
    # заполняю первый список блоков из файла - максимальное количество всего, что может быть на нижнем уровне
    alt_node_list = full_node_list(pathlib.Path(dir_path, 'Tables', vmu_param_file))
    window.current_nodes_list = alt_node_list
    window.show_nodes_tree(alt_node_list)
    # если со списком блоков всё ок, показываем его в левом окошке и запускаем приложение
    if alt_node_list and params_list_changed():
        window.vmu_param_table.adjustSize()
        window.nodes_tree.adjustSize()
        window.show()  # Показываем окно
        splash.finish(window)
        app.exec_()  # и запускаем приложение
# предлагать сохранить список избранного, если он не пустой при выходе
# позволять изменять название списка по двойному щелчку если он не пустой и сразу дописывать его в таблицу
# сообщать на секунду, что параметр добавлен в новый список
# параметры в новом списке не должны дублироваться - использовать множество
# по двойному щелчку в новом списке параметр из него улетает
# как вообще проверять валидность параметров из списка избранного при следующей загрузке
# - может их вообще нет в этих блоках
