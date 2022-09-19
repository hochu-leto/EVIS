import ctypes
import struct

import CANAdater
from EVONode import EVONode
from helper import bytes_to_float, zero_del, int_to_hex_str, float_to_int

empty_par = {'name': '',
             'address': '',
             'editable': '',
             'description': '',
             'scale': '',
             'scaleB': '',
             'unit': '',
             'value': '',
             'type': '',
             'group': '',
             'period': '',
             'size': '',
             'degree': ''}

example_par = {'name': 'fghjk',
               'address': '34567',
               'editable': 1,
               'description': 'ytfjll hkvlbjkkj',
               'scale': 10,
               'scaleB': -40,
               'unit': 'A',
               'value': '23',
               'type': 'SIGNED16',
               'group': '1',
               'period': '20',
               'size': 'nan',
               'degree': 3}

type_values = {
    'UNSIGNED8': {'min': 0, 'max': 255, 'type': 0x2F, 'func': ctypes.c_uint8},
    'SIGNED8': {'min': -128, 'max': 127, 'type': 0x2F, 'func': ctypes.c_int8},
    'UNSIGNED16': {'min': 0, 'max': 65535, 'type': 0x2B, 'func': ctypes.c_uint16},
    'SIGNED16': {'min': -32768, 'max': 32767, 'type': 0x2B, 'func': ctypes.c_int16},
    'UNSIGNED32': {'min': 0, 'max': 4294967295, 'type': 0x23, 'func': ctypes.c_uint32},
    'SIGNED32': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_int32},
    'FLOAT': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_uint8},

}


class Parametr:

    def __init__(self, param=None, node=None):
        if param is None:
            param = empty_par
        if node is None:
            node = EVONode

        def check_value(value, name: str):
            v = value if name not in list(param.keys()) \
                         or str(param[name]) == 'nan' \
                else (param[name] if not isinstance(param[name], str)
                      else (param[name] if param[name].isdigit()
                            else value))
            return v

        def check_string(name: str, s=''):
            st = param[name] if name in list(param.keys()) \
                                and str(param[name]) != 'nan' else s
            return st

        self.name = check_string('name', 'NoName')
        self.address = check_string('address', '0x000000')
        self.type = check_string('type')
        self.type = self.type if self.type in type_values.keys() else 'UNSIGNED32'
        self.editable = True if check_string('editable') else False
        self.unit = check_string('unit')  # единицы измерения
        self.description = check_string('description')  # описание параметра по русски
        self.group = check_string('group')  # неиспользуемое поле в подарок от Векторов
        self.size = check_string('size')  # это какой-то атавизм от блоков БУРР
        self.value = 0
        self.scale = float(check_value(1, 'scale'))  # на что домножаем число из КАНа
        self.scaleB = float(check_value(0, 'scaleB'))  # вычитаем это из полученного выше числа
        self.period = int(check_value(1, 'period'))  # период опроса параметра 1=каждый цикл 1000=очень редко
        self.period = 1000 if self.period > 1000 else self.period
        self.degree = int(check_value(0, 'degree'))  # степень 10 на которую делится параметр из КАНа

        self.min_value = type_values[self.type]['min']
        self.max_value = type_values[self.type]['max']
        # из editable и соответствующего списка
        self.widget = 'QtWidgets'
        # что ставить, если node не передали - emptyNode - который получается, если в EVONode ничего не передать
        self.node = node
        self.req_list = []
        self.set_list = []

    def get_list(self):
        value_type = type_values[self.type]['type']
        address = int(self.address, 16)
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        value = float_to_int(self.value) if self.type == 'FLOAT' else self.value
        data = [value & 0xFF,
                (value & 0xFF00) >> 8,
                (value & 0xFF0000) >> 16,
                (value & 0xFF000000) >> 24]

        if self.node.protocol == 'CANOpen':
            self.req_list = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
            self.set_list = [0x20, LSB, MSB, sub_index] + data
        if self.node.protocol == 'MODBUS':
            self.req_list = [0, 0, 0, 0, sub_index, LSB, value_type, 0x03]
            self.set_list = data + [sub_index, LSB, value_type, 0x10]

    def get_value(self, adapter: CANAdater):
        if not self.req_list:
            self.get_list()
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
            # для реек вот так  address_ans = '0x' + int_to_hex_str(data[4]) + int_to_hex_str(data[5]) наверное
            # для реек вот так  value = (data[3] << 24) + (data[2] << 16) + (data[1] << 8) + data[0]
            address_ans = hex((value_data[5] << 8) + value_data[4])
            value = (value_data[3] << 24) + (value_data[2] << 16) + (value_data[1] << 8) + value_data[0]
        else:  # нужно какое-то аварийное решение
            address_ans = 0
            value = 0
        # ищу в списке параметров како-то с тем же адресом, что в ответе
        if address_ans == self.address:
            if self.type in type_values.keys():
                self.type = 'UNSIGNED32'
            self.value = type_values[self.type]['func'](value).value
            if self.type == 'FLOAT':
                self.value = bytes_to_float(value_data[-4:])

            if self.degree:
                self.value /= 10 ** self.degree
            self.value /= self.scale
            self.value -= self.scaleB
            self.value = zero_del(round(self.value, 4))
            return self.value
        else:
            return 'Адрес не совпадает'

    def set_value(self):
        pass
