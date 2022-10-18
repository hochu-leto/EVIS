"""
тот самый объект параметра, который имеет все нужные поля, умеет запрашивать своё значение и записывать в блок нужное
"""
import ctypes
from time import sleep

import CANAdater
from EVONode import EVONode
from helper import bytes_to_float, int_to_hex_str, float_to_int, empty_par


# здесь когда-то будет возможность читать текст из посылки, пока нет
def can_to_char(value):
    # задел под чтение стрингов
    # value = adapter.can_request(self.request_id, self.answer_id, [0x60, 0, 0, 0, 0, 0, 0, 0])
    # time.sleep(1)
    # print(self.name, end='    ')
    # for byte in value:
    #     print(hex(byte), end=' ')
    # print()
    pass


type_values = {
    'UNSIGNED8': {'min': 0, 'max': 255, 'type': 0x2F, 'func': ctypes.c_uint8},
    'SIGNED8': {'min': -128, 'max': 127, 'type': 0x2F, 'func': ctypes.c_int8},
    'UNSIGNED16': {'min': 0, 'max': 65535, 'type': 0x2B, 'func': ctypes.c_uint16},
    'SIGNED16': {'min': -32768, 'max': 32767, 'type': 0x2B, 'func': ctypes.c_int16},
    'UNSIGNED32': {'min': 0, 'max': 4294967295, 'type': 0x23, 'func': ctypes.c_uint32},
    'SIGNED32': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_int32},
    'FLOAT': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_uint8},
    'VISIBLE_STRING': {'min': 0, 'max': 255, 'type': 0x21, 'func': can_to_char}

}


# слоты для ускорения работы
class Parametr:
    __slots__ = ('address', 'type',
                 'editable', 'unit', 'description',
                 'group', 'size', 'value', 'name',
                 'scale', 'scaleB', 'period', 'degree',
                 'min_value', 'max_value', 'widget',
                 'node', 'req_list', 'set_list')

    def __init__(self, param=None, node=None):
        if param is None:
            param = empty_par
        if node is None:
            node = EVONode

        def check_value(value, name: str):
            v = value if name not in list(param.keys()) \
                         or str(param[name]) == 'nan' \
                         or param[name] == 0 \
                else (param[name] if not isinstance(param[name], str)
                      else (param[name] if param[name].isdigit()
                            else value))
            return v

        def check_string(name: str, s=''):
            st = param[name] if name in list(param.keys()) \
                                and param[name] \
                                and str(param[name]) != 'nan' else s
            return st.strip() if isinstance(st, str) else st

        self.address = check_string('address', '0x000000')
        self.type = check_string('type')
        self.type = self.type if self.type in type_values.keys() else 'UNSIGNED32'
        self.editable = True if check_string('editable') else False
        self.unit = check_string('unit')  # единицы измерения
        self.description = check_string('description')  # описание параметра по русски
        self.group = check_string('group')  # неиспользуемое поле в подарок от Векторов
        self.size = check_string('size')  # это какой-то атавизм от блоков БУРР
        self.value = 0
        self.name = check_string('name', 'NoName')
        self.scale = float(check_value(1, 'scale'))  # на что домножаем число из КАНа
        self.scaleB = float(check_value(0, 'scaleB'))  # вычитаем это из полученного выше числа
        self.period = int(check_value(1, 'period'))  # период опроса параметра 1=каждый цикл 1000=очень редко
        self.period = 1000 if self.period > 1001 else self.period  # проверять горячие буквы, что входят в
        # статические параметры, чтоб период был = 1001
        self.degree = int(check_value(0, 'degree'))  # степень 10 на которую делится параметр из КАНа

        self.min_value = check_value(type_values[self.type]['min'], 'min_value')
        self.max_value = check_value(type_values[self.type]['max'], 'max_value')
        # из editable и соответствующего списка
        self.widget = 'QtWidgets'
        # что ставить, если node не передали - emptyNode - который получается, если в EVONode ничего не передать
        self.node = node
        self.req_list = []
        self.set_list = []

    # формирует посылку в зависимости от протокола
    def get_list(self):
        value_type = type_values[self.type]['type']
        address = int(self.address, 16)
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        value = float_to_int(self.value) if self.type == 'FLOAT' else int(self.value)
        data = [value & 0xFF,
                (value & 0xFF00) >> 8,
                (value & 0xFF0000) >> 16,
                (value & 0xFF000000) >> 24]

        if self.node.protocol == 'CANOpen':
            self.req_list = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
            self.set_list = [value_type, LSB, MSB, sub_index] + data
        if self.node.protocol == 'MODBUS':
            self.req_list = [0, 0, 0, 0, sub_index, LSB, value_type, 0x03]
            self.set_list = data + [sub_index, LSB, value_type, 0x10]

    def set_val(self, adapter: CANAdater, value):
        value += self.scaleB
        value *= self.scale
        if self.degree:
            value *= 10 ** self.degree

        self.value = (value if value < self.max_value else self.max_value) \
            if value >= self.min_value else self.min_value

        self.get_list()
        value_data = adapter.can_request(self.node.request_id, self.node.answer_id, self.set_list)
        if isinstance(value_data, str):
            return value_data
        else:
            return ''

    def get_value(self, adapter: CANAdater):
        if not self.req_list:
            self.get_list()
        while adapter.is_busy:
            sleep(0.0001)    # очень костыльный момент, ждёт миллисекунду, чтоб освободился адаптер
            # на случай когда идёт чтение с двух каналов
        value_data = adapter.can_request(self.node.request_id, self.node.answer_id, self.req_list)
        if isinstance(value_data, str):
            return value_data
        if self.node.protocol == 'CANOpen':
            #  это работает для протокола CANOpen, где значение параметра прописано в последних 4 байтах
            address_ans = '0x' \
                          + int_to_hex_str(value_data[2]) \
                          + int_to_hex_str(value_data[1]) \
                          + int_to_hex_str(value_data[3])
            value = (value_data[7] << 24) + \
                    (value_data[6] << 16) + \
                    (value_data[5] << 8) + value_data[4]
        elif self.node.protocol == 'MODBUS':
            # для реек вот так  address_ans = '0x' + int_to_hex_str(data[5]) + int_to_hex_str(data[4]) наверное
            # для реек вот так  value = (data[3] << 24) + (data[2] << 16) + (data[1] << 8) + data[0]
            address_ans = '0x' + int_to_hex_str(value_data[5]) + int_to_hex_str(value_data[4])
            value = (value_data[3] << 24) + (value_data[2] << 16) + (value_data[1] << 8) + value_data[0]
        else:  # нужно какое-то аварийное решение
            address_ans = 0
            value = 0
        # принятый адрес должен совпадать с тем же адресом, что был отправлен
        if address_ans.upper() == self.address.upper():
            if self.type not in type_values.keys():
                self.type = 'UNSIGNED32'
            self.value = type_values[self.type]['func'](value).value
            if self.type == 'FLOAT':
                self.value = bytes_to_float(value_data[-4:])

            if self.degree:
                self.value /= 10 ** self.degree
            self.value /= self.scale
            self.value -= self.scaleB
            return self.value
        else:
            return 'Адрес не совпадает'

    def to_dict(self):
        exit_dict = empty_par.copy()
        for k in exit_dict.keys():
            exit_dict[k] = self.__getattribute__(k)
        exit_dict['editable'] = 1 if exit_dict['editable'] else 0
        return exit_dict
