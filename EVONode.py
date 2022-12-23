import ctypes

import CANAdater
from Parametr import Parametr
from helper import int_to_hex_str

invertor_command_dict = {
    'POWER_ON': (0x200100, "ОСТОРОЖНО!!! Высокое напряжение ВКЛЮЧЕНО!",
                 'Уверен, что нужно принудительно включить ВЫСОКОЕ напряжение?'),
    'POWER_OFF': (0x200101, "Высокое напряжение выключено!", ''),
    'RESET_DEVICE': (0x200200, "Инвертор перезагружен", 'Полностью перезагрузить инвертор?'),
    'RESET_PARAMETERS': (0x200201, "Параметры инвертора сброшены на заводские настройки",
                         'Сбросить инвертор на заводские настройки?'),
    'APPLY_PARAMETERS': (0x200202, "Текущие параметры сохранены в ЕЕПРОМ Инвертора", ''),
    'BEGIN_POSITION_SENSOR_CALIBRATION': (0x200203, "Идёт калибровка Инвертора",
                                          'Перед калибровкой проверь что:\n'
                                          ' - стояночный тормоз отпущен\n'
                                          ' - приводная ось вывешена\n'
                                          ' - высокое напряжение ВЫКЛЮЧЕНО',),
    'INVERT_ROTATION': (0x200204, "Направление вращения двигателя инвертировано",
                        'Перед инверсией проверь что:\n'
                        ' - высокое напряжение ВЫКЛЮЧЕНО',),
    'RESET_FAULTS': (0x200205, "Ошибки Инвертора сброшены", '')}

'''
'''

empty_node = {
    'name': 'NoName',
    'req_id': 0x500,
    'ans_id': 0x481,
    'protocol': 'CANOpen',
    'serial_number': '',
    'firm_version': '',
    'errors_req': '0x000000',
    'errors_erase': '0x000000',
    'v_errors_erase': 0,
    'errors_list': [],
    'group_nods_list': []
}


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
            for group, params_list in group_par_dict:
                for param in params_list:
                    if hasattr(param, 'node'):
                        if param.node.name == 'NoName':
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
            print('Answer ')
            for i in value:
                print(hex(i), end=' ')
            print()
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
                num += adr.value_string
            elif not isinstance(ans, str):
                num += str(ans).rstrip('0').rstrip('.')
        print(num)
        return int(num) if num.isdigit() else num

    # Потому-то кому-то приспичило передавать серийник в чарах
    # пока никому не приспичило передавать серийник по нескольким адресам и сейчас это затычка для ТТС,
    # но вообще неплохо бы сделать эту функцию наподобие опроса ошибок по нескольким адресам,
    # другое дело как чары парусить, наверное, это должно быть либо в ответе от блока либо в типе параметра
    def get_serial_for_ttc(self, adapter: CANAdater):
        serial_ascii_address_lst = [0x218001,
                                    0x218002,
                                    0x218003,
                                    0x218004]

        ser = ''
        for adr in serial_ascii_address_lst:
            ge = self.get_val(adr, adapter)
            i = 0
            while isinstance(ge, str):
                ge = self.get_val(adr, adapter)
                i += 1
                if i > 10:
                    return ''

            ser += check_printable(ge)

        self.serial_number = ser
        return int(self.serial_number) if ser else ser

    def get_firmware_version(self, adapter: CANAdater):
        if self.firmware_version:
            return self.firmware_version
        f_list = self.get_val(self.request_firmware_version, adapter) if self.request_firmware_version else 0
        if isinstance(f_list, str):
            if self.string_from_can:
                f_list = self.string_from_can

        self.firmware_version = f_list
        print(f'{self.name} - {f_list=}')
        return self.firmware_version

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
        err_dict = {v.value: v for v in s_list}
        big_error = 0
        j = 0
        for adr in r_request:
            error = self.get_val(adr, adapter)
            # print(hex(adr), error)
            if isinstance(error, int):
                if error <= 128:
                    big_error += error << j * 8
                else:
                    big_error = error
            else:
                big_error = 0
            j += 1

        if big_error:
            if self.name == 'КВУ_ТТС':
                if big_error in err_dict.keys():  # космический костыль
                    current_list.add(err_dict[big_error])
                else:
                    current_list.add(f'Неизвестная ошибка ({big_error})')
            else:
                for e_num, e_obj in err_dict.items():
                    if big_error & e_num:
                        current_list.add(e_obj)
        return current_list

    def erase_errors(self, adapter: CANAdater):
        #  ошибки должны быть объектами
        if self.error_erase['address']:
            self.send_val(self.error_erase['address'], adapter, self.error_erase['value'])
            self.current_errors_list.clear()
            self.current_warnings_list.clear()

    def read_string_from_can(self, value):
        # value = adapter.can_request(self.request_id, self.answer_id, [0x60, 0, 0, 0, 0, 0, 0, 0])
        # это сделано только для инвертора мэи, который должен ответить
        if isinstance(value, str):
            self.string_from_can = ''
            return value
        for byte in value:
            self.string_from_can += chr(byte)
        s = self.string_from_can.strip()
        return int(s) if s.isdigit() else s


def check_printable(lst):
    a_st = ''
    lst = [(lst & 0xFF000000) >> 24,
           (lst & 0xFF0000) >> 16,
           (lst & 0xFF00) >> 8,
           lst & 0xFF]
    for s in lst:
        a_st += chr(s) if chr(s).isprintable() else ''
    return a_st
