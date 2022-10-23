'''
класс, к которому обращается программа, он уже определяет в какой операционке работаем, ищет подключенные адаптеры,
(пока только МАРАФОН и Квасер) и определяет скорости кан-шин, к которым они подключены.
Нормально работает пока только с марафоном
'''
from sys import platform

import AdapterCAN
from kvaser_power import Kvaser
from marathon_power import CANMarathon


class CANAdapter:
    isDefined = False

    def __init__(self):
        self.is_busy = False
        self.id_nones_dict = {}  # словарь блоков, где ключ - айди обращения к блоку, а значение - объект адаптера
        self.can_adapters = {}  # словарь адаптеров,где ключ - цифра битрейта, а значение - объект адаптера
        print('Ищу адаптеры')
        self.find_adapters()

    def find_adapters(self):
        if platform == "linux" or platform == "linux2":  # linux - только квасер
            self.search_chanells(Kvaser)
        elif platform == "darwin":  # OS X
            print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
        elif platform == "win32":  # Windows... - квасер в приоритете, если нет, то марафон
            # -------------------------------- ИСПРАВИТЬ  -----------------------------------
            # self.search_chanells(Kvaser)
            # if not self.can_adapters:
            self.search_chanells(CANMarathon)

    def search_chanells(self, adapter: AdapterCAN):
        print(f'Пробую найти {adapter.__name__}')
        i = 0
        while True:
            can_adapter = adapter(channel=i)
            bit = can_adapter.check_bitrate()  # пробежавшись по битрейту
            if isinstance(bit, str):  # и получив строку, понимаю, что адаптера нет совсем
                break
            #       если же битрейт возвращает число, при этом меняется битрейт самого канала
            #       или адаптер на 125 имеется, запоминаем его
            self.isDefined = True
            print(f'Нашёл {adapter.__name__} канал {i}, скорость {bit}')

            self.can_adapters[bit] = can_adapter
            i += 1

    #   на случай, если оба канала подключены к одной шине,
    #   их битрейты совпадают и они просто будут перезаписаны в словаре

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):

        # если нужно опросить блок, айди которого уже есть в словаре,
        # просто используем этот адаптер, который привязан к этому айди -
        # так можно опрашивать сразу два кана(а может и три, если такой адаптер найдётся)
        if can_id_req in list(self.id_nones_dict.keys()):
            adapter = self.id_nones_dict[can_id_req]
            self.is_busy = True  # даю понять всем, что адаптер занят, чтоб два потока не обращались в одно время
            ans = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False
            return ans
        answer = 'Проверь соединение с ВАТС'
        # если в словаре нет айди блока, бегу по словарю(хотя это можно сделать списком) с имеющимся адаптерами
        if not self.isDefined:
            self.find_adapters()
        for adapter in self.can_adapters.values():
            self.is_busy = True
            answer = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False  # освобождаем адаптер
            # если в ответе нет строки(ошибки), значит адаптер имеется,
            # добавляем его в словарь с этим айди блока и возвращаем ответ
            if not isinstance(answer, str):
                self.id_nones_dict[can_id_req] = adapter
                return answer
        return answer

    def close_canal_can(self):
        for adapter in self.can_adapters.values():
            adapter.close_canal_can()

    def can_send(self, can_id_req: int, message: list, bitrate=None):
        if bitrate is None:
            bitrate = 125
        if bitrate in self.can_adapters.keys():
            adapter = self.can_adapters[bitrate]
            ans = adapter.can_write(can_id_req, message)
            return ans
        return 'Неверный битрейт'

    def can_read(self, can_id_ans: int, bitrate=None):
        if bitrate is None:
            bitrate = 125
        if bitrate in self.can_adapters.keys():
            adapter = self.can_adapters[bitrate]
            ans = adapter.can_read(can_id_ans)
            return ans
        return 'Неверный битрейт'
