"""
тот самый объект параметра, который имеет все нужные поля, умеет запрашивать своё значение и записывать в блок нужное
"""
import ctypes
from copy import deepcopy

import CANAdater
from helper import bytes_to_float, int_to_hex_str, float_to_int, empty_par

type_values = {
    'UNSIGNED8': {'min': 0, 'max': 255, 'type': 0x2F, 'func': ctypes.c_uint8},
    'SIGNED8': {'min': -128, 'max': 127, 'type': 0x2F, 'func': ctypes.c_int8},
    'UNSIGNED16': {'min': 0, 'max': 65535, 'type': 0x2B, 'func': ctypes.c_uint16},
    'SIGNED16': {'min': -32768, 'max': 32767, 'type': 0x2B, 'func': ctypes.c_int16},
    'UNSIGNED32': {'min': 0, 'max': 4294967295, 'type': 0x23, 'func': ctypes.c_uint32},
    'SIGNED32': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_int32},
    'FLOAT': {'min': -2147483648, 'max': 2147483647, 'type': 0x23, 'func': ctypes.c_uint8},
    'VISIBLE_STRING': {'min': 0, 'max': 255, 'type': 0x21, 'func': ctypes.c_int32},  # can_to_char}
    'DATE': {'min': 0, 'max': 4294967295, 'type': 0x23, 'func': ctypes.c_uint32}  # can_to_char}
}


# слоты для ускорения работы
class Parametr:
    __slots__ = ('address', 'type',
                 'editable', 'unit', 'description',
                 'group', 'size', 'value', 'name',
                 'scale', 'offset', 'period', 'degree',
                 'min_value', 'max_value', 'widget', 'node',
                 'req_list', 'set_list', 'value_compare', 'value_dict', 'value_string')

    def __init__(self, param=None, node=None):
        if param is None:
            param = empty_par

        def check_value(value, name: str):
            v = value if name not in list(param.keys()) \
                         or not param[name] \
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
        self.value = check_value(0, 'value')
        self.value_compare = 0
        self.name = check_string('name', 'NoName')
        self.scale = float(check_value(1, 'scale'))  # на что домножаем число из КАНа
        self.offset = float(check_value(0, 'scaleB'))  # вычитаем это из полученного выше числа
        self.period = int(check_value(1, 'period'))  # период опроса параметра 1=каждый цикл 1000=очень редко
        self.period = 1000 if self.period > 1001 else self.period  # проверять горячие буквы, что входят в
        # статические параметры, чтоб период был = 1001
        self.degree = int(check_value(0, 'degree'))  # степень 10 на которую делится параметр из КАНа

        self.min_value = check_value(type_values[self.type]['min'], 'min_value')
        self.max_value = check_value(type_values[self.type]['max'], 'max_value')
        v_table = check_string('values_table')
        self.value_dict = {int(k): v for k, v in v_table.items()} if isinstance(v_table, dict) \
            else {int(val.split(':')[0]): val.split(':')[1]
                  for val in v_table.split(',')} if v_table else {}
        # из editable и соответствующего списка
        self.widget = 'QtWidgets'
        # что ставить, если node не передали - emptyNode - который получается, если в EVONode ничего не передать
        self.node = node
        self.req_list = []
        self.set_list = []
        self.value_string = ''

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
        value += self.offset
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
            pass  # очень костыльный момент, ждёт миллисекунду, чтоб освободился адаптер
            # на случай когда идёт чтение с двух каналов
        # print('Запррашиваю')
        # for i in self.req_list:
        #     print(hex(i), end=' ')
        # print()
        value_data = adapter.can_request(self.node.request_id, self.node.answer_id, self.req_list)
        if isinstance(value_data, str):
            return value_data

        if self.node.protocol == 'CANOpen':
            # print(self.name, end='   ')
            # for i in value_data:
            #     print(hex(i), end=' ')
            # print()
            if value_data[0] == 0x41:  # это запрос на длинный параметр строчный
                # print(self.name, end='   ')
                # for i in value_data:
                #     print(hex(i), end=' ')
                data = adapter.can_request_long(self.node.request_id, self.node.answer_id, value_data[4])
                value = self.string_from_can(data)
                if not self.value_string:  # ошибка, если свой стринг пустой
                    return value
                self.value = None
                return self.value
            #  это работает для протокола CANOpen, где значение параметра прописано в последних 4 байтах
            address_ans = '0x' \
                          + int_to_hex_str(value_data[2]) \
                          + int_to_hex_str(value_data[1]) \
                          + int_to_hex_str(value_data[3])
            value = (value_data[7] << 24) + \
                    (value_data[6] << 16) + \
                    (value_data[5] << 8) + value_data[4]
            # print(f'{address_ans=}, {value=}')
        elif self.node.protocol == 'MODBUS':
            # print(self.name, end='   ')
            # for i in value_data:
            #     print(hex(i), end=' ')
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
                self.type = 'SIGNED32'
            self.value = type_values[self.type]['func'](value).value
            if self.type == 'FLOAT':
                self.value = bytes_to_float(value_data[-4:])
            elif self.type == 'VISIBLE_STRING':
                self.string_from_can(value_data[-4:])
                self.value = None
                return self.value
            elif self.type == 'DATE':
                # self.string_from_can(value_data)
                # do something
                self.value_string = '20.12.2022'
                self.value = None
                return self.value

            if self.degree:
                self.value /= 10 ** self.degree
            self.value /= self.scale
            self.value -= self.offset
            return self.value
        elif self.type == 'VISIBLE_STRING':
            self.string_from_can(value_data[-4:])
            self.value = None
            return self.value
        else:
            return 'Адрес не совпадает'

    def to_dict(self):
        exit_dict = empty_par.copy()
        # for k in exit_dict.keys():
        print(self.__dir__)
        for k in self.__dir__():
            exit_dict[k] = self.__getattribute__(k)
        exit_dict['editable'] = 1 if exit_dict['editable'] else 0
        return exit_dict

    def check_node(self, node_dict: dict):
        if '#' in self.name:
            node_name = self.name.split('#')[1]
            if node_name in node_dict.keys():
                self.node = node_dict[node_name]
                return True
            else:
                print('Этого блока нет в словаре')
                return False
        else:
            print('В имени параметра нет разделителя')
            return False

    def string_from_can(self, value):
        self.value_string = ''
        if isinstance(value, str):
            return value
        s = ''
        for byte in value:
            if 'Ethernet_' in self.name or '_Ip' in self.name:
                self.editable = False
                s += str(byte) + '.'
            elif '_Mac' in self.name:
                self.editable = False
                s += int_to_hex_str(byte) + ':'
            elif '_time' in self.name:
                s += str(byte)
            else:
                s += chr(byte)
        self.value_string = s.strip().rstrip('.').rstrip(':')
        return int(self.value_string) if self.value_string.isdigit() else self.value_string

    def copy(self):
        return deepcopy(self)


class Copyable:
    __slots__ = 'a', '__dict__'

    def __init__(self, a, b):
        self.a, self.b = a, b

    def __copy__(self):
        return type(self)(self.a, self.b)

    def __deepcopy__(self, memo):  # memo is a dict of id's to copies
        id_self = id(self)  # memoization avoids unnecesary recursion
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)(
                deepcopy(self.a, memo),
                deepcopy(self.b, memo))
            memo[id_self] = _copy
        return _copy

    def copye(self):
        return deepcopy(self)
