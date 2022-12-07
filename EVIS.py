"""
Сейчас программа умеет
    - определить ОС
    - определить подключенный адаптер
    - определить какие кан-шины подключены
    - подключиться к ВАТС по двойному щелчку на блоке или группе параметров блока или по кнопке Подключиться
    - запросить серийник и версию ПО блока, если серийник есть, то блок считается подключенным,
        серийник может быть текстовым
    - запросить и удалить ошибки подключенных блоков
    - запросить параметр и изменить параметр
    - сохранение нужного значения параметров в ЕЕПРОМ
    - сохранять все параметры текущего блока в эксель файл - можно параллельно с основным потоком, но лучше отключаться
    - возможность выбрать параметры из разных блоков и сохранить их в отдельный список и
        хранить пользовательский список параметров в файле - Избранное - Новый список
    - сравнение всех параметров из файла с текущими из блоков

следующие шаги
- поиск по имени и описанию параметра
- возможность записи лога текущих параметров из открытого списка и сохранять запись в эксель файл - лог
- графики выбранных текущих параметров
- виджеты по управлению параметром
- хранение профилей блока в отдельном файле эксель с названием_блока_версия_ПО в папках с Название_блока
        в файле список параметров и ошибки. Это позволит оставить пользовательский список Избранное
- добавить в параметр поле со словарём значений -
        если считано подходящее - подставлять значение из словаря (как сохранять??)
- всплывающее меню при правом щелчке по параметру - Добавить в Избранное и Изменить период
- автоматическое определение нужного периода опроса параметра и сохранение этого периода в свойства параметра в файл
- работа в линуксе
- работа с квайзером
- в новом параметре КВУ формировать ВИН номер машины+номера_блоков -
        сделать автоматический опрос номеров и сравнение с тем, что в памяти
- сохранение и парсинг параметров в yaml
- при изменении параметра в инверторе мэи напоминать, что он не действует без сохранения в еепром
- если не подключен к ВАТС, изменение параметров пачкой и при подключении их заброс в блок
- если нет опроса, но изменён параметр, не запускать опрос после изменения
- прерывать опрос только при отправке нового параметра, после сразу запускать
- добавить в кву кнопку считать с ЕЕПРОМ
- покрасить критические ошибки в красный с приставкой - критическая!
- добавить вкладку ПНР, на ней несколько подвкладок со страницами процесса пнр с нужными параметрами
- добавить возможность ОТМЕНы при нажатии любой кнопки управления
- добавить напоминание выключить высокое при калибровке инвертора
- выдавать какую ошибку схватил инвертор, если время кончилось, а положительного ответа от инвертора не поступило
- сделать процесс подключения видимым
- подкрашивать параметры, которые в новый список улетают, чтоб было заметно
- сделать видимым процесс привязки джойстика и установки подвески
- сделать ошибки объектами с описанием, ссылками и выводом нужных параметров

НА ПОДУМАТЬ
- может ли приёмник джойстика отвечать по SDO например, положения кнопок?
- может ли БКУ отвечать по SDO хотя бы серийник?
- продумать реляционную БД для параметров
- на отдельном листе управление для этого блока с виджетами типами - слайдеры, кнопки, чекбоксы - по каким адресам,
  название и так далее.
- добавлять блок в список имеющихся и
выводить в соседнем окошке список определённых для этого блока виджетов (слайдеры, кнопки) + количество этих окошек с
виджетами для каждого блока задаёт пользователь, т.е. он может создать свои нужные виджеты и сохранить их в профиль к
этому блоки, а при загрузке это должно подгрузится - и стандартные и выбранные для того блока пользователем -
полагаю отдельный лист Экселя с выбранными параметрами - виджетами
- ещё кнопка - загрузка параметров из файла - здесь должна быть жёсткая защита - не все редактируемые параметры
 из одного блока можно напрямую заливать в другой. Или их ограничить до минимума или предлагать делать изменение вручную

"""
import sys

from PyQt5.QtCore import pyqtSlot, Qt, QRegExp
from PyQt5.QtGui import QIcon, QColor, QPixmap, QRegExpValidator
from PyQt5.QtWidgets import QMessageBox, QApplication, QMainWindow, QTreeWidgetItem, QDialog, \
    QSplashScreen, QFileDialog
import pathlib

import VMU_monitor_ui
from CANAdater import CANAdapter
from EVONode import EVONode
from My_threads import SaveToFileThread, MainThread, WaitCanAnswerThread, SleepThread
from Parametr import Parametr
from work_with_file import full_node_list, fill_sheet_dict, fill_compare_values, save_params_dict_to_file
from helper import zero_del, NewParamsList, log_uncaught_exceptions, DialogChange, show_empty_params_list, \
    show_new_vmu_params, find_param

can_adapter = CANAdapter()

dir_path = str(pathlib.Path.cwd())
# файл где все блоки, параметры, ошибки
vmu_param_file = 'table_for_params_new_VMU.xlsx'
vmu_param_file = pathlib.Path(dir_path, 'Tables', vmu_param_file)
sys.excepthook = log_uncaught_exceptions
wait_thread = WaitCanAnswerThread()
sleep_thread = SleepThread(4)


def make_compare_params_list():
    file_name = QFileDialog.getOpenFileName(window, 'Файл с нужными параметрами КВУ', dir_path,
                                            "Excel tables (*.xlsx)")[0]
    if file_name and ('.xls' in file_name):
        compare_nodes_dict = fill_sheet_dict(file_name)
        comp_node_name = ''
        if compare_nodes_dict:
            for cur_node in window.thread.current_nodes_list:
                # как минимум, два варианта что этот блок присутствует
                #  - если имя страницы, он же ключ у словаря из файла совпадает с имеющимся сейчас блоком
                #  - если список параметров, хотя бы частично, совпадает со списком параметров имеющегося блока
                if cur_node.name in compare_nodes_dict.keys():
                    fill_compare_values(cur_node, compare_nodes_dict[cur_node.name])
                    comp_node_name += cur_node.name + ', '
                else:
                    for comp_params_dict in compare_nodes_dict.values():
                        if set(cur_node.group_params_dict.keys()) & set(comp_params_dict.keys()):
                            fill_compare_values(cur_node, comp_params_dict)
                            comp_node_name += cur_node.name + ', '
                            break
        show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table,
                               has_compare=window.thread.current_node.has_compare_params)
        if comp_node_name:
            window.log_lbl.setText(f'Загружены параметры сравнения для блока {comp_node_name}')
        else:
            window.log_lbl.setText(f'Не найден блок для загруженных параметров')
    else:
        window.log_lbl.setText('Файл не выбран')
        return False


def save_to_eeprom(node=None):
    if not node:
        node = window.thread.current_node

    if node.save_to_eeprom:
        if window.thread.isRunning():
            window.connect_to_node()
            isRun = True
        else:
            isRun = False

        if node.name == 'Инвертор_МЭИ':
            voltage = find_param(window.current_nodes_list, 'DC_VOLTAGE', 'Инвертор_МЭИ')[0]
            err = voltage.get_value(can_adapter.adapters_dict[125])
            if not isinstance(err, str):
                if err < 30:
                    err = node.send_val(node.save_to_eeprom, can_adapter.adapters_dict[125])
                    sleep_thread.SignalOfProcess.emit(window.progress_bar_fulling)
                    sleep_thread.start()
                    # while sleep_thread.isRunning():
                    #     pass     # херня какая-то
                else:
                    err = 'Высокое не выключено'
                    QMessageBox.critical(window, "Ошибка ",
                                         'Чтоб сохранить параметры Инвертора МЭИ в ЕЕПРОМ\n'
                                         'Выключи высокое напряжение и повтори сохранение',
                                         QMessageBox.Ok)
        else:
            err = node.send_val(node.save_to_eeprom, can_adapter, value=1)

        if err:
            QMessageBox.critical(window, "Ошибка ", 'Настройки сохранить не удалось' + '\n' + err, QMessageBox.Ok)
            window.log_lbl.setText('Настройки в память НЕ сохранены, ошибка ' + err)
        else:
            QMessageBox.information(window, "Успешный успех!", 'Текущие настройки сохранены в EEPROM', QMessageBox.Ok)
            window.log_lbl.setText('Настройки сохранены в EEPROM')
            node.param_was_changed = False
            window.save_eeprom_btn.setEnabled(False)

        if window.thread.isFinished() and isRun:
            window.connect_to_node()
    else:
        QMessageBox.information(window, "Информация", f'В {node.name} параметры сохранять не нужно', QMessageBox.Ok)
        window.save_eeprom_btn.setEnabled(False)


def want_to_value_change():
    #  над разбивать, как минимум, на две функции
    current_cell = window.vmu_param_table.currentItem()
    c_row = current_cell.row()
    c_col = current_cell.column()
    c_text = current_cell.text()
    # возможно, лучше сразу флаги дёрнуть, потом их изменять
    c_flags = current_cell.flags()
    col_name = window.vmu_param_table.horizontalHeaderItem(current_cell.column()).text().strip().upper()
    current_param = window.thread.current_params_list[c_row]

    # меняем значение параметра
    if col_name == 'ЗНАЧЕНИЕ':
        is_editable = True if Qt.ItemIsEditable & current_cell.flags() else False
        if is_editable:
            dialog = DialogChange(label=current_param.name, value=c_text.strip())
            reg_ex = QRegExp("[+-]?([0-9]*[.])?[0-9]+")
            dialog.lineEdit.setValidator(QRegExpValidator(reg_ex))
            if dialog.exec_() == QDialog.Accepted:
                val = dialog.lineEdit.text()
                val = val if val and val != '-' else '0'
                if window.thread.isRunning():  # отключаем поток, если он был включен
                    window.connect_to_node()
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
                            window.thread.current_node.param_was_changed = True
                            if window.thread.current_node.name == 'Инвертор_МЭИ':
                                QMessageBox.information(window, "Информация", f'Параметр будет работать, \n'
                                                                              f'только после сохранения в ЕЕПРОМ',
                                                        QMessageBox.Ok)
                    else:
                        next_cell.setBackground(QColor(254, 0, 0, 30))
                    # если поток был запущен до изменения, то запускаем его снова
                    if window.thread.isFinished():
                        # и запускаю поток
                        window.connect_to_node()

                else:  # здесь может быть логика сохранения параметров, если их меняют пачкой
                    QMessageBox.information(window, "Информация", f'Подключение прервано, \n'
                                                                  f'Для изменения параметра\n'
                                                                  f'требуется подключение к ВАТС',
                                            QMessageBox.Ok)
        else:  # здесь может быть логика сохранения параметров, если их меняют пачкой
            QMessageBox.information(window, "Информация", f'Этот параметр нельзя изменить\n'
                                                          f' Изменяемые параметры подкрашены зелёным',
                                    QMessageBox.Ok)
            # сбрасываю фокус с текущей ячейки, чтоб выйти красиво, при запуске потока и
            # обновлении значения она снова станет редактируемой, пользователь не замечает изменений
        window.vmu_param_table.item(c_row, c_col).setFlags(c_flags & ~Qt.ItemIsEditable)
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
                show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table)
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
    show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table,
                           has_compare=window.thread.current_node.has_compare_params)
    # и запускаю поток, если он был запущен
    if is_run and window.thread.isFinished():
        window.connect_to_node()
    return True


def check_node_online(all_node_list: list):
    exit_list = []
    has_invertor = False
    # из всех возможных блоков выбираем те, которые отвечают на запрос серийника
    for nd in all_node_list:
        node_serial = nd.get_serial_number(can_adapter)
        print(nd.name, node_serial)
        if node_serial:
            nd.firmware_version = nd.get_firmware_version(can_adapter)
            # тут выясняется, что на старых машинах, где Инвертор_Цикл+ кто-то отвечает по ID Инвертор_МЭИ,
            # может и китайские рейки, нет особого желания разбираться. Вообщем это костыль, чтоб он не вылазил
            if 'Инвертор_Цикл+' in nd.name:
                has_invertor = True
            elif 'Инвертор_МЭИ' in nd.name:
                window.invertor_mpei_box.setEnabled(True)
            elif 'КВУ_ТТС' in nd.name:
                window.joy_bind_btn.setEnabled(True)
                window.susp_zero_btn.setEnabled(True)
            exit_list.append(nd)
    if has_invertor:
        for nd in exit_list:
            if 'Инвертор_МЭИ' in nd.name:
                exit_list.remove(nd)
                break
    # на случай если только избранное найдено - значит ни один блок не ответил
    if exit_list[0].cut_firmware() == 'EVOCARGO':
        return all_node_list.copy(), False

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
    for nod in window.current_nodes_list:
        nod.erase_errors(can_adapter)
    #     for err in nod.erase_errors(can_adapter):
    #         if err:
    #             window.thread.errors_str += f'{nod.name}: {err} \n'
    # window.errors_browser.setText(window.thread.errors_str)
    window.show_error_tree({})
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
        self.all_params_dict = {}
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
        # global can_adapter
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
                # self.current_nodes_list = []
                # можно было бы избавиться от этой переменной, проверять, что список не пустой, но пусть будет
                # self.node_list_defined = False
                can_adapter.isDefined = False
        else:
            show_new_vmu_params(params_list=self.thread.current_params_list,
                                table=self.vmu_param_table,
                                has_compare_params=self.thread.current_node.has_compare_params)

    @pyqtSlot(dict)  # добавляем ошибки в окошко
    def add_new_errors(self, err_dict: dict):
        self.show_error_tree(err_dict)

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
                dialog = DialogChange(label='Можно изменить название списка', value=NewParamsList)
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

    def show_error_tree(self, nds: dict):
        cur_item = ''
        # запоминаю где сейчас курсор - тупо по тексту
        try:
            old_item_name = window.errors_tree.currentItem().text(0)
        except AttributeError:
            old_item_name = ''

        self.errors_tree.clear()
        self.errors_tree.setColumnCount(1)
        self.errors_tree.header().close()
        items = []
        #   ругается, что ндс - нифига не словарь
        for nod, nod_err in nds.items():
            if nod_err:
                # создаю основные вкладки - названия блоков
                item = QTreeWidgetItem()
                item_name = f'{nod}({len(nod_err)})'
                item.setText(0, item_name)
                if old_item_name == item_name:
                    # если если ранее выбранный блок среди имеющихся, запоминаю его
                    cur_item = item
                for err in nod_err:
                    # подвкладки - ошибки
                    child_item = QTreeWidgetItem()
                    child_item.setText(0, str(err))
                    item.addChild(child_item)
                    # если ранее курсор стоял на группе, запоминаю ее
                    if old_item_name == str(err):  # не работает для рулевых - нужно запоминать и имя блока тоже
                        cur_item = child_item
                items.append(item)

        if not items:
            item = QTreeWidgetItem()
            item.setText(0, 'Ошибок нет')
            items.append(item)
        self.errors_tree.insertTopLevelItems(0, items)
        # если курсор стоял на блоке, который отсутствует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.errors_tree.topLevelItem(0)
        if cur_item.childCount():
            self.errors_tree.setCurrentItem(cur_item)

    def show_node_name(self, nd: EVONode):
        # чтоб юзер понимал в каком блоке он находится
        self.node_name_lab.setText(nd.name)
        self.node_s_n_lab.setText(f'Серийный номер: {nd.serial_number}')
        self.node_fm_lab.setText(f'Версия ПО: {nd.cut_firmware()}')
        if self.save_to_file_btn.isEnabled():
            self.save_to_file_btn.setText(f'Сохранить настройки блока:\n {nd.name} в файл')
        return

    def connect_to_node(self):
        # такое бывает при первом подключении или если вырвали адаптер - надо заново его определить
        if not can_adapter.isDefined:
            self.log_lbl.setText('Определяется подключенный адаптер...')
            if not can_adapter.find_adapters():
                self.log_lbl.setText('Адаптер не подключен')
                return
        # если у нас вообще нет адаптеров, надо выходить
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
        ln = len(window.current_nodes_list)
        user_node_dict = self.current_nodes_list[ln - 1].group_params_dict

        for node in window.thread.current_nodes_list:
            if node.param_was_changed:
                msg = QMessageBox(self)
                msg.setWindowTitle("Параметры не сохранены")
                msg.setIcon(QMessageBox.Information)
                msg.setText(f"В блоке {node.name} были изменены параметры,\n"
                            f" но они не сохранены в EEPROM,\n"
                            f" нужно ли их сохранить в память?")

                buttonAceptar = msg.addButton("Сохранить", QMessageBox.YesRole)
                msg.addButton("Не сохранять", QMessageBox.RejectRole)
                msg.setDefaultButton(buttonAceptar)
                msg.exec_()
                if msg.clickedButton() == buttonAceptar:
                    save_to_eeprom(node)

        if NewParamsList in user_node_dict.keys():
            if user_node_dict[NewParamsList]:
                dialog = DialogChange(label=f'В {NewParamsList} добавлены параметры \n'
                                            f' нужно сохранить этот список?', value=NewParamsList)
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
        msg.addButton("Отменить", QMessageBox.RejectRole)  # buttonCancelar =
        msg.setDefaultButton(buttonAceptar)
        msg.exec_()

        if msg.clickedButton() == buttonAceptar:
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
                del self.thread
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
        else:
            event.ignore()

    def change_tab(self):
        if self.main_tab.currentWidget() == self.management_tab:
            if self.thread.isRunning():
                self.connect_to_node()
                print('Поток остановлен')
            print('Вкладка управление')
        elif self.main_tab.currentWidget() == self.params_tab:
            self.connect_to_node()
            print('Вкладка параметры, поток запущен')
        elif self.main_tab.currentWidget() == self.grafics_tab:
            print('Графики не готовы')
        else:
            print('Неизвестное состояние')


def mpei_calibrate():
    param_list_for_calibrate = ['FAULTS', 'DC_VOLTAGE', 'SPEED_RPM', 'FIELD_CURRENT',
                                'PHA_CURRENT', 'PHB_CURRENT', 'PHC_CURRENT']  # 'STATOR_CURRENT', 'TORQUE',
    wait_thread.adapter = can_adapter.adapters_dict[125]
    wait_thread.id_for_read = 0x381
    wait_thread.answer_byte = 4
    wait_thread.answer_dict = {0x0A: 'Калибровка прошла успешно!',
                               0x0B: 'Калибровка не удалась',
                               0x0C: 'Настройки сохранены в ЕЕПРОМ'}
    for p_name in param_list_for_calibrate:
        wait_thread.imp_par_list.append(find_param(window.current_nodes_list, p_name, node_name='Инвертор_МЭИ')[0])

    dialog = DialogChange(label='Процесс калибровки',
                          text='Команда на калибровку отправлена',
                          table=wait_thread.imp_par_list)
    dialog.setWindowTitle('Калибровка Инвертора МЭИ')
    dialog.text_browser.setEnabled(False)
    dialog.text_browser.setStyleSheet("font: bold 14px;")

    @pyqtSlot(list, list)
    def check_dialog_mess(st, list_of_params):
        if wait_thread.isRunning():
            dialog.change_mess(st, list_of_params)
        else:
            print('Поток калибровки остановлен')
            for node in window.thread.current_nodes_list:
                if node.name == 'Инвертор_МЭИ':
                    # передавать надо исключительно в первый кан
                    if node.request_id in window.thread.adapter.id_nodes_dict.keys():
                        adapter_can1 = window.thread.adapter.id_nodes_dict[node.request_id]
                        faults = node.check_errors(adapter=adapter_can1)
                        if not faults:
                            st.append('Ошибок во время калибровки не появилось')
                        else:
                            faults.insert(0, 'Во время калибровки возникли ошибки: ')
                            st += faults
                        dialog.change_mess(st)

    wait_thread.SignalOfProcess.connect(check_dialog_mess)

    s = window.thread.invertor_command('BEGIN_POSITION_SENSOR_CALIBRATION', wait_thread)
    if not s:
        wait_thread.start()
        if dialog.exec_():
            wait_thread.quit()
            wait_thread.wait()
            print('Поток калибровки остановлен')


def mpei_invert():
    m = window.thread.invertor_command('INVERT_ROTATION')
    window.log_lbl.setText(m)


def mpei_power_on():
    m = window.thread.invertor_command('POWER_ON')
    window.log_lbl.setText(m)


def mpei_power_off():
    m = window.thread.invertor_command('POWER_OFF')
    window.log_lbl.setText(m)


def mpei_reset_device():
    m = window.thread.invertor_command('RESET_DEVICE')
    window.log_lbl.setText(m)


def mpei_reset_params():
    m = window.thread.invertor_command('RESET_PARAMETERS')
    window.log_lbl.setText(m)


def joystick_bind():
    if not can_adapter.isDefined:
        if not can_adapter.find_adapters():
            return
    if 250 in can_adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед привязкой проверь,\n что джойстик ВЫКЛЮЧЕН',
                                QMessageBox.Ok)
        adapter = can_adapter.adapters_dict[250]

        dialog = DialogChange(text='Команда на привязку отправлена')
        dialog.setWindowTitle('Привязка джойстика')
        dialog.text_browser.setEnabled(False)
        dialog.text_browser.setStyleSheet("font: bold 14px;")

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.wait_time = 20  # время в секундах для включения и прописки джойстика
        wait_thread.req_delay = 250  # время в миллисекундах на
        wait_thread.max_err = 80  # потому что приёмник джойстика не отвечает постоянно, а только трижды
        wait_thread.adapter = adapter
        wait_thread.id_for_read = 0x18FF87A7
        wait_thread.answer_dict = {
            0: 'принята команда привязки',
            1: 'приемник переведен в режим привязки, ожидание включения пульта ДУ',
            2: 'привязка завершена',
            254: 'ошибка',
            255: 'команда недоступна'}

        bind_command = adapter.can_write(0x18FF86A5, [0] * 8)

        if not bind_command:
            wait_thread.start()
            if dialog.exec_():
                wait_thread.quit()
                wait_thread.wait()
                print('Поток остановлен')
        else:
            QMessageBox.critical(window, "Ошибка ", 'Команда привязки не отправлена\n' + bind_command, QMessageBox.Ok)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.Ok)


@pyqtSlot(str)
def set_log_lbl(s: str):
    window.log_lbl.setText(s)


def suspension_to_zero():
    if not can_adapter.isDefined:
        if not can_adapter.find_adapters():
            return
    if 250 in can_adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед выравниванием проверь что:\n'
                                                      ' - тумблер АВТО включен ВВЕРХ\n'
                                                      ' - остальные тумблеры в нейтральном положении',
                                QMessageBox.Ok)
        adapter = can_adapter.adapters_dict[250]
        command_zero_suspension = adapter.can_write(0x18FF83A5, [1, 0x7D, 0x7D, 0x7D, 0x7D])
        if not command_zero_suspension:
            QMessageBox.information(window, "Информация", 'Машина должна выйти в среднее положение\n'
                                                          'И теперь будет работать в режиме АВТО\n'
                                                          'Чтобы его отключить  - тумблер АВТО в среднее положение\n'
                                                          'Или перезагрузить КВУ',
                                    QMessageBox.Ok)
            window.log_lbl.setText('Машина должна выйти в среднее положение')
        else:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{command_zero_suspension}', QMessageBox.Ok)
            window.log_lbl.setText(command_zero_suspension)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication([])
    splash = QSplashScreen()
    splash.setPixmap(QPixmap('pictures/EVO-EVIS_l.jpg'))
    splash.show()
    window = VMUMonitorApp()
    window.setWindowTitle('Electric Vehicle Information System')
    #
    window.main_tab.currentChanged.connect(window.change_tab)
    # подключаю сигналы нажатия на окошки
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    window.nodes_tree.doubleClicked.connect(window.double_click)
    window.vmu_param_table.cellDoubleClicked.connect(want_to_value_change)
    # и сигналы нажатия на кнопки
    # -----------------Инвертор---------------------------
    window.invert_btn.clicked.connect(mpei_invert)
    window.calibrate_btn.clicked.connect(mpei_calibrate)
    window.power_on_btn.clicked.connect(mpei_power_on)
    window.power_off_btn.clicked.connect(mpei_power_off)
    window.reset_device_btn.clicked.connect(mpei_reset_device)
    window.reset_param_btn.clicked.connect(mpei_reset_params)
    window.invertor_mpei_box.setEnabled(False)
    window.susp_zero_btn.setEnabled(False)
    window.joy_bind_btn.setEnabled(False)
    # ------------------Кнопки вспомогательные----------------
    window.joy_bind_btn.clicked.connect(joystick_bind)
    window.susp_zero_btn.clicked.connect(suspension_to_zero)
    # ------------------Главные кнопки-------------------------
    window.connect_btn.clicked.connect(window.connect_to_node)
    window.save_eeprom_btn.clicked.connect(save_to_eeprom)
    window.reset_faults.clicked.connect(erase_errors)
    window.compare_btn.clicked.connect(make_compare_params_list)
    window.save_to_file_btn.clicked.connect(save_to_file_pressed)
    window.save_to_file_btn.setEnabled(False)
    # заполняю первый список блоков из файла - максимальное количество всего, что может быть на нижнем уровне
    alt_node_list = full_node_list(vmu_param_file).copy()
    window.current_nodes_list = alt_node_list.copy()
    window.thread.current_nodes_list = window.current_nodes_list
    # показываю дерево с блоками и что ошибок нет
    window.show_error_tree({})
    window.show_nodes_tree(alt_node_list)
    # если со списком блоков всё ок, показываем его в левом окошке и запускаем приложение
    if alt_node_list and params_list_changed():
        if can_adapter.find_adapters():
            window.connect_to_node()
        else:
            window.log_lbl.setText('Адаптер не подключен')
        window.show()  # Показываем окно
        splash.finish(window)  # Убираем заставку
        app.exec_()  # и запускаем приложение

'''
сейчас есть несколько проблем
- чем больше параметров в окне с калибровкой инв, тем больше вероятность просрать от него информацию об успешной калибровке
    сейчас это решено уменьшением параметров до 4, но есть мысль, что нужно изменить индивидупльный  опрос параметров на
     считывание всего всего буфера из памяти адаптера и его разбора - долго и сложно
- периодически параметры в списке калибровке дублируются дважды один и тот же может быть
- не отправляется команда на привязку джойстика
- надо придумать какие нужны файлы и как они должны храниться для списка параметров и ошибок по блокам
    в блоках по версиям ПО. То, что делает Антон не подходит для всех блоков, Тип json хорош, но его нужно переделывать
- 
'''
