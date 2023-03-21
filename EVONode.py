import ctypes

import CANAdater
from EVOErrors import EvoError
from EVOParametr import Parametr
from helper import int_to_hex_str

invertor_command_dict = {
    'POWER_ON': (0x200100, "ОСТОРОЖНО!!! Высокое напряжение ВКЛЮЧЕНО!",
                 'Уверен, что нужно принудительно включить ВЫСОКОЕ напряжение?'),
    'POWER_ON_SILENT': (0x200100, "", ''),
    'POWER_OFF': (0x200101, "Высокое напряжение выключено!", ''),
    'RESET_DEVICE': (0x200200, "Инвертор перезагружен", 'Полностью перезагрузить инвертор?'),
    'RESET_PARAMETERS': (0x200201, "Параметры инвертора сброшены на заводские настройки",
                         'Сбросить инвертор на заводские настройки?'),
    'APPLY_PARAMETERS': (0x200202, "Текущие параметры сохранены в ЕЕПРОМ Инвертора", ''),
    'BEGIN_POSITION_SENSOR_CALIBRATION': (0x200203, "Идёт калибровка Инвертора",
                                          'Перед калибровкой проверь что:'
                                          ' - стояночный тормоз отпущен'
                                          ' - приводная ось вывешена'
                                          ' - высокое напряжение ВЫКЛЮЧЕНО',),
    'INVERT_ROTATION': (0x200204, "Направление вращения двигателя инвертировано",
                        'Перед инверсией проверь что:'
                        ' - высокое напряжение ВЫКЛЮЧЕНО',),
    'RESET_FAULTS': (0x200205, "Ошибки Инвертора сброшены", ''),
    'ISOLATION_MONITORING_OFF': (0x200211, "Контроль изоляции ОТКЛЮЧЕН", ''),
    'ISOLATION_MONITORING_ON': (0x200210, "Контроль изоляции ВКЛЮЧЕН", '')}

'''
'''

empty_node = {
    'name': 'NoName',
    'req_id': 0x0,
    'ans_id': 0x1,
    'protocol': 'CANOpen',
    'serial_number': '',
    'firm_version': '',
    'errors_req': '0x000000',
    'errors_erase': '0x000000',
    'v_errors_erase': 0,
    'errors_list': [],
    'group_nods_list': []
}

exit_list = ['name', 'serial_number', 'firmware_version', 'request_id', 'answer_id', 'protocol']


class EVONode:
    __slots__ = ('name', 'request_id', 'answer_id',
                 'protocol', 'request_serial_number',
                 'serial_number', 'request_firmware_version',
                 'firmware_version', 'error_request', 'error_erase',
                 'errors_list', 'current_errors_list', 'warning_request',
                 'warnings_list', 'current_warnings_list', 'group_params_dict',
                 'string_from_can', 'load_from_eeprom', 'save_to_eeprom', 'has_compare_params',
                 'param_was_changed')

    def __init__(self, nod=None, err_list=None, war_list=None, group_par_dict=None):
        if group_par_dict is None:
            group_par_dict = {}
        if err_list is None:
            err_list = []
        if war_list is None:
            war_list = []
        if nod is None or not isinstance(nod, dict):
            nod = empty_node

        def check_address(name: str, value=0):
            v = value if name not in list(nod.keys()) or str(nod[name]) == 'nan' \
                else (nod[name] if not isinstance(nod[name], str)
                      else (int(nod[name], 16) if '0x' in nod[name]
                            else value))  # надо включать регулярку
            return v

        def check_string(name: str, s=''):
            st = nod[name] if name in list(nod.keys()) \
                              and nod[name] \
                              and str(nod[name]) != 'nan' else s
            return st

        self.name = check_string('name', 'NoName')
        self.request_id = check_address('req_id', 0x500)
        self.answer_id = check_address('ans_id', 0x481)
        self.protocol = check_string('protocol', 'CANOpen')
        # теперь в серийнике, версии ПО и ошибках будут списки параметров, по которым всё это опрашивается
        self.request_serial_number = [Parametr(p, node=self) for p in nod['serial_number']]
        self.serial_number = ''
        self.request_firmware_version = [Parametr(p, node=self) for p in nod['firm_version']]
        self.firmware_version = ''

        self.error_request = [int(i, 16) if i else 0 for i in check_string('errors_req').split(',')]
        if err_list:
            for er in err_list:
                if hasattr(er, 'node'):
                    if er.node.name == 'Неизвестная ошибка':
                        er.node = self
        self.errors_list = err_list
        self.current_errors_list = set()

        self.warning_request = [int(i, 16) if i else 0 for i in check_string('warnings_req').split(',')]
        if war_list:
            for war in war_list:
                if hasattr(war, 'node'):
                    if war.node.name == 'Неизвестная ошибка':
                        war.node = self
        self.warnings_list = war_list
        self.current_warnings_list = set()

        self.error_erase = {'address': check_address('errors_erase'),
                            'value': int(check_address('v_errors_erase'))}

        if group_par_dict:
            for group, params_list in group_par_dict.items():
                for param in params_list:
                    if hasattr(param, 'node'):
                        if not param.node or param.node.name == 'NoName':
                            param.node = self

        self.group_params_dict = group_par_dict
        self.string_from_can = ''
        self.save_to_eeprom = check_address('to_eeprom')
        self.load_from_eeprom = check_address('from_eeprom')
        self.has_compare_params = False
        self.param_was_changed = False

    def get_val(self, address: int, adapter: CANAdater):
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        r_list = []

        if self.protocol == 'CANOpen':
            r_list = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
        if self.protocol == 'MODBUS':
            r_list = [0, 0, 0, 0, sub_index, LSB, 0x2B, 0x03]
        while adapter.is_busy:
            pass
        value = adapter.can_request(self.request_id, self.answer_id, r_list)
        # надо переделать на пустоту. величина может быть текстом
        if isinstance(value, str):
            return value

        if self.protocol == 'CANOpen':
            if value[0] == 0x41:  # это запрос на длинный параметр строчный
                data = adapter.can_request_long(self.request_id, self.answer_id, value[4])
                value = self.read_string_from_can(data)
                if not self.string_from_can:  # ошибка, если свой стринг пустой
                    return value
                # если есть стринг - значит всё хорошо и отправляем None
                return None

            else:
                value = (value[7] << 24) + \
                        (value[6] << 16) + \
                        (value[5] << 8) + value[4]
        elif self.protocol == 'MODBUS':
            # value = value[0]
            value = (value[3] << 24) + (value[2] << 16) + (value[1] << 8) + value[0]
        else:
            value = ctypes.c_int32(value)
        return value

    def send_val(self, address: int, adapter: CANAdater, value=0):
        try:
            value = int(value)
        except ValueError:
            return 'Передаваемое значение должно быть INTEGER'

        data = [value & 0xFF,
                (value & 0xFF00) >> 8,
                (value & 0xFF0000) >> 16,
                (value & 0xFF000000) >> 24]

        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        r_list = []
        if self.protocol == 'CANOpen':
            r_list = [0x23, LSB, MSB, sub_index] + data  # вообще - это колхоз - нужно определять тип переменной
        if self.protocol == 'MODBUS':  # , которой я хочу отправить
            r_list = data + [sub_index, LSB, 0x2B, 0x10]
        for i in r_list:
            print(hex(i), end=' ')
        print()
        while adapter.is_busy:
            pass
        value = adapter.can_request(self.request_id, self.answer_id, r_list)

        if isinstance(value, str):
            return value  # если вернул строку, значит, проблема
        else:
            # print('Answer ')
            # for i in value:
            #     print(hex(i), end=' ')
            # print()
            return ''  # если пусто, значит, норм ушла

    def get_data(self, adapter: CANAdater, address_list=None):
        if address_list is None:
            address_list = self.request_serial_number
        elif not isinstance(address_list, list):
            return address_list
        num = ''
        for adr in address_list:
            ans = adr.get_value(adapter)
            print(ans, adr.value_string, end=' ')
            if adr.value_string:
                if adr.value_string != num:
                    num += adr.value_string
            elif not isinstance(ans, str):
                num += str(ans).rstrip('0').rstrip('.')
        print(num)
        return int(num) if num.isdigit() else ''.join([s for s in num if s.isprintable()])

    def cut_firmware(self):
        if isinstance(self.firmware_version, int):
            fm = self.firmware_version
            if not fm:
                text = 'EVOCARGO'
            elif fm > 0xFFFF:
                text = '0x' + int_to_hex_str((fm & 0xFF000000) >> 24) + \
                       int_to_hex_str((fm & 0xFF0000) >> 16) + \
                       int_to_hex_str((fm & 0xFF00) >> 8) + \
                       int_to_hex_str(fm & 0xFF)
            else:
                text = str(fm)
            return text
        return self.firmware_version

    def check_errors(self, adapter: CANAdater, false_if_war=True):
        #  на выходе - список текущих ошибок
        # тоже херня надо переходить на параметры, которые при опросе выдают свои ошибки
        if false_if_war:
            r_request = self.error_request.copy()
            s_list = self.errors_list.copy()
            current_list = self.current_errors_list.copy()
        else:
            r_request = self.warning_request.copy()
            s_list = self.warnings_list.copy()
            current_list = self.current_warnings_list.copy()

        if not r_request or not s_list:
            return current_list

        big_error = 0
        j = 0
        for adr in r_request:
            error = self.get_val(adr, adapter)
            if isinstance(error, int):
                if error <= 128:
                    big_error += error << j * 8
                else:
                    big_error = error
            else:
                big_error = 0
            j += 1

        if big_error:
            err_dict = {v.value: v for v in s_list}

            if self.name == 'КВУ_ТТС':
                if big_error in err_dict.keys():  # космический костыль
                    current_list.add(err_dict[big_error])
                else:
                    err_name = f'Неизвестная ошибка ({big_error})'
                    if err_name not in [er.name for er in current_list]:
                        e = EvoError()
                        e.name = err_name
                        current_list.add(e)
            else:
                for e_num, e_obj in err_dict.items():
                    if big_error & e_num:
                        current_list.add(e_obj)
        return current_list

    def erase_errors(self, adapter: CANAdater):
        # полная хрень. удаление ошибок - это должен быть параметр, который умеет отсылаться
        if self.error_erase['address']:
            self.send_val(self.error_erase['address'], adapter, self.error_erase['value'])
            self.current_errors_list.clear()
            self.current_warnings_list.clear()

    def read_string_from_can(self, value):
        if isinstance(value, str):
            self.string_from_can = ''
            return value
        for byte in value:
            self.string_from_can += chr(byte)
        s = self.string_from_can.strip().rstrip('0')
        return int(s) if s.isdigit() else s

    def to_dict(self):
        exit_dict = {ke: self.__getattribute__(ke) for ke in exit_list}
        if self.current_errors_list:
            exit_dict['current_errors_list'] = [er.name for er in self.current_errors_list]
        if self.current_warnings_list:
            exit_dict['current_warnings_list'] = [wr.name for wr in self.current_warnings_list]
        exit_dict['parameters'] = self.groups_to_dict()
        return exit_dict

    def groups_to_dict(self):
        return {group: [par.to_dict() for par in params]
                for group, params in self.group_params_dict.items()}


def check_printable(lst):
    a_st = ''
    lst = [(lst & 0xFF000000) >> 24,
           (lst & 0xFF0000) >> 16,
           (lst & 0xFF00) >> 8,
           lst & 0xFF]
    for s in lst:
        a_st += chr(s) if chr(s).isprintable() else ''
    return a_st
