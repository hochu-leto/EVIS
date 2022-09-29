from pprint import pprint
from sys import platform

import AdapterCAN
from kvaser_power import Kvaser
from marathon_power import CANMarathon


class CANAdapter:
    isDefined = False
    is_busy = False

    def __init__(self):
        self.id_nones_dict = {}
        self.can_adapters = {}
        print('Ищу адаптеры')
        if platform == "linux" or platform == "linux2":  # linux
            self.search_chanells(Kvaser)
        elif platform == "darwin":  # OS X
            print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
        elif platform == "win32":  # Windows...
            self.search_chanells(Kvaser)
            if not self.can_adapters:
                self.search_chanells(CANMarathon)

    def search_chanells(self, adapter: AdapterCAN):
        print(f'Пробую найти {adapter.__name__}')
        i = 0
        while True:
            can_adapter = adapter(channel=i)
            bit = can_adapter.check_bitrate()  # пробежавшись по битрейту
            if isinstance(bit, str):  # и получив строку, понимаю, что адаптера нет совсем
                print(f'Проблема адаптера {bit}')
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
        if can_id_req in list(self.id_nones_dict.keys()):
            adapter = self.id_nones_dict[can_id_req]
            self.is_busy = True
            ans = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False
            return ans
        answer = 'Проверь соединение с ВАТС'
        for adapter in self.can_adapters.values():
            self.is_busy = True
            answer = adapter.can_request(can_id_req, can_id_ans, message)
            self.is_busy = False
            if not isinstance(answer, str):
                self.id_nones_dict[can_id_req] = adapter
                return answer
        return answer

    def close_canal_can(self):
        for adapter in self.can_adapters.values():
            adapter.close_canal_can()
