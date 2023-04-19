'''
класс, к которому обращается программа, он уже определяет в какой операционке работаем, ищет подключенные адаптеры,
(пока только МАРАФОН и Квасер) и определяет скорости кан-шин, к которым они подключены.
Нормально работает пока только с марафоном
'''
import os
import pathlib
from sys import platform
os.environ['KVDLLPATH'] = str(pathlib.Path(pathlib.Path.cwd(), 'Kvaser_Driver_and_dll'))

from canlib import canlib
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget
from canlib.canlib.exceptions import CanError, CanGeneralError

import AdapterCAN
from Kvaser_channel import KvaserChannel1, KvaserChannel2, hardware_kvaser_channels, KvaserChannel
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
            text = ''
            if not self.search_kvaser_channels():
                self.search_channels(CANMarathon)
            # self.adapters_dict[125] = Kvaser(channel=0, bit=125)
            # self.adapters_dict[250] = Kvaser(channel=0, bit=250)
            # self.adapters_dict[250] = KvaserChannel1()
            # self.adapters_dict[125] = KvaserChannel2()
            # self.isDefined = True
        # - работает только для последнего адаптера
        # self.adapters_dict[250].canal_open()
        if not self.adapters_dict:
            if QApplication.instance() is None:
                app = QApplication([])
            # QMessageBox.critical(None, "Ошибка ", 'Адаптер не обнаружен', QMessageBox.StandardButton.Ok)
            # QMessageBox.critical(None, "Ошибка ", text, QMessageBox.StandardButton.Ok)
            QMessageBox.critical(QWidget(), "Ошибка ", text, QMessageBox.StandardButton.Ok)
            return False
        return True

    def search_kvaser_channels(self):
        channel_dict = hardware_kvaser_channels()
        print(channel_dict)
        if channel_dict:
            self.isDefined = True
            for channel, bit in channel_dict.items():
                self.adapters_dict[bit] = KvaserChannel(channel=channel, bitrate=bit)
        return True if self.adapters_dict else False

    def search_channels(self, adapter: AdapterCAN, chanel_count=2) -> str:
        print(f'Пробую найти {adapter.__name__}')
        text = adapter.__name__
        bit_dict = adapter.can_bitrate.copy()
        for i in range(chanel_count):  # у нас только два канала может быть
            text += f'\n канал {i}'
            can_adapter = adapter(channel=i)
            bit = can_adapter.check_bitrate(bitrate_dict=bit_dict)  # пробежавшись по битрейту
            if isinstance(bit, str):  # и получив строку, понимаю, что адаптера нет совсем
                text += bit
                continue
            # если же битрейт возвращает число, при этом меняется битрейт самого канала
            self.isDefined = True
            print(f'Нашёл {adapter.__name__} канал {i}, скорость {bit}')
            text = can_adapter.text
            self.adapters_dict[bit] = can_adapter  # это словарь где ключ - скорость, а значение - экземпляр адаптера
            del bit_dict[bit]
        return text

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        # если нужно опросить блок, айди которого уже есть в словаре,
        # просто используем этот адаптер, который привязан к этому айди -
        # так можно опрашивать сразу два кана(а может и три, если такой адаптер найдётся)
        answer = 'Проверь соединение с ВАТС'
        if self.id_nodes_dict:
            if can_id_req in list(self.id_nodes_dict.keys()):
                adapter = self.id_nodes_dict[can_id_req]
                self.is_busy = True  # даю понять всем, что адаптер занят, чтоб два потока не обращались в одно время
                ans = adapter.can_request(can_id_req, can_id_ans, message)
                self.is_busy = False
                if isinstance(ans, CanGeneralError):    # CanError):
                    match ans.status:
                        case canlib.Error.HARDWARE | canlib.Error.INTERNAL:
                            self.id_nodes_dict.clear()
                            for ad in self.adapters_dict:
                                try:
                                    ad.busOff()
                                    ad.close()
                                except canlib.canError:
                                    continue
                            self.adapters_dict.clear()
                            self.isDefined = False
                return ans.__str__()
            # если в словаре нет айди блока, бегу по словарю(хотя это можно сделать списком) с имеющимся адаптерами
            for adapter in self.adapters_dict.values():
                self.is_busy = True
                answer = adapter.can_request(can_id_req, can_id_ans, message)
                self.is_busy = False  # освобождаем адаптер
                # если в ответе нет строки(ошибки), значит адаптер имеется,
                # добавляем его в словарь с этим айди блока и возвращаем ответ
                if not isinstance(answer, str):
                    self.id_nodes_dict[can_id_req] = adapter
                    return answer
        else:
            if not self.search_kvaser_channels():
                self.search_channels(CANMarathon)
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
                # for ti, a in ans.items():
                #     print(ti, buf_to_string(a))
                #     print()
                ans = list(ans.values())
            return ans
        return 'Неверный битрейт'

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):
        adapter = self.id_nodes_dict[can_id_req]
        ans_list = adapter.can_request_long(can_id_req, can_id_ans, l_byte)
        if isinstance(ans_list, list):
            ans_list = ans_list[:l_byte]
        return ans_list
