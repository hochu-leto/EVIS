'''
класс, к которому обращается программа, он уже определяет в какой операционке работаем, ищет подключенные адаптеры,
(пока только МАРАФОН и Квасер) и определяет скорости кан-шин, к которым они подключены.
Нормально работает пока только с марафоном
'''
from sys import platform

from PyQt6.QtWidgets import QApplication, QMessageBox

import AdapterCAN
from kvaser_power import Kvaser
from marathon_power import CANMarathon
from helper import buf_to_string


class CANAdapter:

    def __init__(self):
        self.isDefined = False
        self.id_nodes_dict = {}  # словарь блоков, где ключ - айди обращения к блоку, а значение - объект адаптера
        self.is_busy = False
        self.adapters_dict = {}  # словарь адаптеров,где ключ - цифра битрейта, а значение - объект адаптера
        self.can_bitrate = CANMarathon.can_bitrate
        # self.find_adapters()

    def find_adapters(self):
        print('Ищу адаптеры')
        if platform == "linux" or platform == "linux2":  # linux - только квасер
            pass
            # -------------------------------- ИСПРАВИТЬ  -----------------------------------
            # self.search_chanells(Kvaser)
        elif platform == "darwin":  # OS X
            print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
        elif platform == "win32":  # Windows... - квасер в приоритете, если нет, то марафон
            # -------------------------------- ИСПРАВИТЬ  -----------------------------------
            self.search_chanells(Kvaser)
            # if not self.can_adapters:
            if not self.isDefined:
                self.search_chanells(CANMarathon)
        if not self.adapters_dict:
            if QApplication.instance() is None:
                app = QApplication([])
            QMessageBox.critical(None, "Ошибка ", 'Адаптер не обнаружен', QMessageBox.StandardButton.Ok)
            return False
        return True

    def search_chanells(self, adapter: AdapterCAN):
        print(f'Пробую найти {adapter.__name__}')
        # i = 0
        # while True:  # хреновая тема

        for i in range(2):      # у нас только два канала может быть
            can_adapter = adapter(channel=i)
            bit = can_adapter.check_bitrate()  # пробежавшись по битрейту
            if isinstance(bit, str):  # и получив строку, понимаю, что адаптера нет совсем
                continue
            # если же битрейт возвращает число, при этом меняется битрейт самого канала
            # или адаптер на 125 имеется, запоминаем его
            self.isDefined = True
            print(f'Нашёл {adapter.__name__} канал {i}, скорость {bit}')
            self.adapters_dict[bit] = can_adapter   # это словарь где ключ - скорость, а значение - экземпляр адаптера

            # i += 1
            # if i > 4:
            #     print('Слишком много каналов')
            #     break

    #   на случай, если оба канала подключены к одной шине,
    #   их битрейты совпадают и они просто будут перезаписаны в словаре

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        # если нужно опросить блок, айди которого уже есть в словаре,
        # просто используем этот адаптер, который привязан к этому айди -
        # так можно опрашивать сразу два кана(а может и три, если такой адаптер найдётся)
        if can_id_req in list(self.id_nodes_dict.keys()):
            adapter = self.id_nodes_dict[can_id_req]
            self.is_busy = True  # даю понять всем, что адаптер занят, чтоб два потока не обращались в одно время
            ans = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False
            return ans
        # если в словаре нет айди блока, бегу по словарю(хотя это можно сделать списком) с имеющимся адаптерами
        # if not self.isDefined:
        #     self.close_canal_can()
        #     self.find_adapters()
        answer = 'Проверь соединение с ВАТС'
        for adapter in self.adapters_dict.values():
            self.is_busy = True
            answer = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False  # освобождаем адаптер
            # если в ответе нет строки(ошибки), значит адаптер имеется,
            # добавляем его в словарь с этим айди блока и возвращаем ответ
            if not isinstance(answer, str):
                self.id_nodes_dict[can_id_req] = adapter
                return answer
        return answer

    def close_canal_can(self):
        for adapter in self.adapters_dict.values():
            adapter.close_canal_can()

    def can_send(self, can_id_req: int, message: list, bitrate=None):
        if bitrate is None:
            bitrate = 125
        if not self.adapters_dict:
            return ''
        if bitrate in self.adapters_dict.keys():
            adapter = self.adapters_dict[bitrate]
            ans = adapter.can_write(can_id_req, message)
            return ans
        return 'Неверный битрейт'

    def can_read(self, can_id_ans: int, bitrate=None):
        if bitrate is None:
            bitrate = 125
        if bitrate in self.adapters_dict.keys():
            adapter = self.adapters_dict[bitrate]
            ans = adapter.can_read(can_id_ans)
            if isinstance(ans, dict):
                for ti, a in ans.items():
                    print(ti, buf_to_string(a))
                    print()
                ans = list(ans.values())
            return ans
        return 'Неверный битрейт'

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):
        adapter = self.id_nodes_dict[can_id_req]
        ans_list = adapter.can_request_long(can_id_req, can_id_ans, l_byte)
        if isinstance(ans_list, list):
            ans_list = ans_list[:l_byte]
        return ans_list
