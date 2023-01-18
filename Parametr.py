"""
тот самый объект параметра, который имеет все нужные поля, умеет запрашивать своё значение и записывать в блок нужное
"""
import ctypes
from copy import deepcopy, copy

import CANAdater
from helper import bytes_to_float, int_to_hex_str, float_to_int, empty_par

readme = dict(
    required_fields=dict(
        name='Содержит имя параметра',
        index='Определяет адрес параметра в словаре Canopen устройства, либо адресс ячейки памяти для рулевых блоков',
        sub_index='Определяет адрес параметра в словаре Canopen устройства, для рулевых блоков не используется',
        type='Определяет тип данных параметра, возможные значения "BOOLEAN", "SIGNED8", "SIGNED16", '
             '"SIGNED32", "SIGNED64", "UNSIGNED8", "UNSIGNED16", "UNSIGNED32", "FLOAT", "VISIBLE_STRING",'
             ' "OCTET_STRING", "UNICODE_STRING", "TIME_OF_DAY", "TIME_DIFFERENCE", "DOMAIN"'),
    optional_fields=dict(
        editable='Аналог access, указывает возможно ли изменение параметра или только для просмотра,'
                 'возможные значения: True, False',
        description='Содержит подробное описание параметра',
        offset='Смещение для перевода полученного integer-значения в дробное по формуле '
               'value = (raw_value * mult) - offset.Указывается только для физических величин, '
               'которые нуждаются в конвертации. Если значение 0, то может не указываться',
        multiplier='Множитель для перевода полученного integer-значения в дробное по формуле '
                   'value = (raw_value * mult) - offset. Указывается только для физических величин,'
                   ' которые нуждаются в конвертации. Если значение 1, то может не указываться',
        eeprom='Наличие поля показывает, что этот параметр сохраняется в энергонезависимую память. '
               'Запись и чтение осуществляются по запросам со стороны пользователя. '
               'При включении КВУ чтение параметров из EEPROM происходит автоматически',
        value='Предназначено для сохранения актуального значения параметра при выгрузке конфигурации из блока'
              'в файл и обратно',
        units='Единицы измерения',
        value_table="Расшифровка возможных значений в поле 'value'",
        period='Периодичность опроса параметра, от 1 до 1000, чем меньше, чем чаще опрашивается',
        min_value='Минимально возможное значение параметра, при отсутствии заданной величины принимается равному'
                  ' минимальному значению согласно типу параметра',
        max_value='Максимально возможное значение параметра, при отсутствии заданной величины принимается равному'
                  ' Максимальному значению согласно типу параметра',
        widget='Отображение величины параметра в диагностической программе, при отсутствии отображается в виде цифр, '
               'возможные значения: для нередактируемых: "BAR", для редактируемых: "BUTTON", "SLIDER", "SWITCH"'
    )
)
# список полей параметра, который будем запихивать в файл. Можно выбрать не все поля
# в следующем релизе нужно согласовать со стандартными полями Параметра
exit_list = ['name', 'address', 'description', 'offset', 'units', 'value_table',
             'value', 'type', 'period', 'min_value', 'max_value', 'multiplier', 'editable']

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
    __slots__ = ('value', 'name',
                 'type', 'sub_index', 'index',
                 'editable', 'units', 'description',
                 'multiplier', 'offset', 'period', 'editable',
                 'min_value', 'max_value', 'widget', 'node',
                 'req_list', 'set_list', 'value_compare', 'value_table', 'value_string')

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

        # в следующем релизе нужно прийти к стандартным полям Параметра,
        # но чтоб принимал все предыдущие варианты, превращая их в стандартные, примерно как сейчас в scale
        address = int(check_string('address', '0x000000'), 16)
        if address:
            self.index = ((address & 0xFFFF00) >> 8)
            self.sub_index = address & 0xFF
        else:
            self.index = check_value(0, 'index')
            self.sub_index = check_value(0, 'sub_index')
        typ = check_string('type')
        self.type = typ if typ in type_values.keys() else 'UNSIGNED32'
        self.editable = True if check_string('editable') else False
        self.units = check_string('unit', check_string('units'))  # единицы измерения
        self.description = check_string('description')  # описание параметра по русски
        self.value = check_value(0, 'value')
        self.value_compare = 0
        self.name = check_string('name', 'NoName')
        # на что умножаем число из КАНа
        degree = check_value(0, 'degree')
        scale = float(check_value(10 ** degree, 'scale'))
        self.multiplier = float(check_value(float(check_value(1 / scale, 'mult')), 'multiplier'))
        # вычитаем это из полученного выше числа
        self.offset = float(check_value(float(check_value(0, 'offset')), 'scaleB'))
        period = int(check_value(1, 'period'))  # период опроса параметра 1=каждый цикл 1000=очень редко
        self.period = 1000 if period > 1001 else period  # проверять горячие буквы, что входят в
        # статические параметры, чтоб период был = 1001
        self.min_value = check_value(type_values[self.type]['min'], 'min_value')
        self.max_value = check_value(type_values[self.type]['max'], 'max_value')
        valueS_table = check_string('values_table', check_string('value_dict'))
        v_table = valueS_table if valueS_table else check_string('value_table')
        self.value_table = {int(k): v for k, v in v_table.items()} if isinstance(v_table, dict) \
            else {int(val.split(':')[0]): val.split(':')[1]
                  for val in v_table.split(',')} if v_table else {}
        # из editable и соответствующего списка
        self.widget = 'QtWidgets'
        self.node = node
        self.req_list = []
        self.set_list = []
        self.value_string = ''

    # формирует посылку в зависимости от протокола
    def get_list(self):
        value_type = type_values[self.type]['type']
        MSB = ((self.index & 0xFF00) >> 8)
        LSB = self.index & 0xFF
        value = float_to_int(self.value) if self.type == 'FLOAT' else int(self.value)
        data = [value & 0xFF,
                (value & 0xFF00) >> 8,
                (value & 0xFF0000) >> 16,
                (value & 0xFF000000) >> 24]

        if self.node.protocol == 'CANOpen':
            self.req_list = [0x40, LSB, MSB, self.sub_index, 0, 0, 0, 0]
            self.set_list = [value_type, LSB, MSB, self.sub_index] + data
        if self.node.protocol == 'MODBUS':
            self.req_list = [0, 0, 0, 0, LSB, MSB, value_type, 0x03]
            self.set_list = data + [LSB, MSB, value_type, 0x10]

    def set_val(self, adapter: CANAdater, value):
        value += self.offset
        value /= self.multiplier

        self.value = (value if value < self.max_value else self.max_value) \
            if value >= self.min_value else self.min_value

        self.get_list()
        value_data = adapter.can_request(self.node.request_id, self.node.answer_id, self.set_list)
        # надо как-то определять, если блок не принял значение, тоже какой-то ответ будет
        if isinstance(value_data, str):
            return value_data
        else:
            return ''

    def get_value(self, adapter: CANAdater):
        if not self.req_list:
            self.get_list()
        while adapter.is_busy:
            pass
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
            index_ans = (value_data[2] << 8) + value_data[1]
            sub_index_ans = value_data[3]
            value = (value_data[7] << 24) + \
                    (value_data[6] << 16) + \
                    (value_data[5] << 8) + value_data[4]
            print(f'{hex(index_ans)=}, {hex(sub_index_ans)=}, {value=}')
        elif self.node.protocol == 'MODBUS':
            # print(self.name, end='   ')
            # for i in value_data:
            #     print(hex(i), end=' ')
            index_ans = (value_data[5] << 8) + value_data[4]
            sub_index_ans = 0
            value = (value_data[3] << 24) + (value_data[2] << 16) + (value_data[1] << 8) + value_data[0]
        else:  # нужно какое-то аварийное решение
            index_ans = 0
            sub_index_ans = 0
            value = 0

        if self.type == 'VISIBLE_STRING':
            self.string_from_can(value_data[-4:])
            self.value = None
            return self.value
        elif index_ans == self.index and sub_index_ans == self.sub_index:
            # принятый адрес должен совпадать с тем же адресом, что был отправлен
            if self.type == 'FLOAT':
                self.value = bytes_to_float(value_data[-4:])
            elif self.type == 'DATE':
                # do something
                self.value_string = '20.12.2022'
                self.value = None
                return self.value
            else:
                self.value = type_values[self.type]['func'](value).value

            self.value *= self.multiplier
            self.value -= self.offset
            return self.value
        else:
            return 'Адрес не совпадает'

    def to_dict(self):
        return {k: self.__getattribute__(k) for k in exit_list}


    def string_from_can(self, value):
        self.value_string = ''
        if isinstance(value, str):
            return value
        s = ''
        for byte in value:
            if 'Ethernet_' in self.name or '_Ip' in self.name:
                if s.count('.') < 4:
                    s += str(byte) + '.'
            elif '_Mac' in self.name:
                if s.count(':') < 4:
                    s += int_to_hex_str(byte) + ':'
            elif 'time' in self.name:
                s += str(byte)
            else:
                s += chr(byte)
        self.value_string = s.strip().rstrip('.').rstrip(':')
        self.editable = False
        self.period = 500
        return int(self.value_string) if self.value_string.isdigit() else self.value_string

    def copy(self):
        return copy(self)
