from sys import platform

import AdapterCAN
from kvaser_power import Kvaser
from marathon_power import CANMarathon


class CANAdapter:

    def __init__(self):
        self.can_adapters = {}
        if platform == "linux" or platform == "linux2":  # linux
            self.search_chanells(Kvaser)
        elif platform == "darwin":  # OS X
            print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
        elif platform == "win32":  # Windows...
            self.search_chanells(Kvaser)
            if not self.can_adapters:
                self.search_chanells(CANMarathon)

    def search_chanells(self, adapter: AdapterCAN):
        i = 0
        while True:
            bit = 125
            can_adapter = adapter(channel=i, bit=bit)
            if isinstance(can_adapter.ch, str):  # если нет адаптера, получаем строку
                bit = can_adapter.check_bitrate  # пробежавшись по битрейту
                if isinstance(bit, str):  # и получив строку, понимаю, что адаптера нет совсем
                    break
            #           если же битрейт возвращает число, при этом меняется битрейт самого канала
            #       или адаптер на 125 имеется, запоминаем его
            self.can_adapters[bit] = can_adapter
            i += 1

    #   на случай, если оба канала подключены к одной шине,
    #   их битрейты совпадают и они просто будут перезаписаны в словаре

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        pass
