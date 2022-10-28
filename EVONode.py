import ctypes

import CANAdater
from helper import int_to_hex_str, empty_par

empty_node = {
    'name': 'NoName',
    'req_id': 0x500,
    'ans_id': 0x481,
    'protocol': 'CANOpen',
    'serial_number': 0,
    'firm_version': 0,
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
                 'string_from_can', 'load_from_eeprom', 'save_to_eeprom', 'has_compare_params')

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
            v = value if name not in list(nod.keys()) \
                         or str(nod[name]) == 'nan' \
                else (nod[name] if not isinstance(nod[name], str)
                      else (int(nod[name], 16) if '0x' in nod[name]
                            else value))  # надо включать регулярку
            return v

        def check_string(name: str, s=''):
            st = nod[name] if name in list(nod.keys()) \
                              and str(nod[name]) != 'nan' else s
            return st

        self.name = check_string('name', 'NoName')
        self.request_id = check_address('req_id', 0x500)
        self.answer_id = check_address('ans_id', 0x481)
        self.protocol = check_string('protocol', 'CANOpen')
        self.request_serial_number = check_address('serial_number')
        self.serial_number = '---'
        self.request_firmware_version = check_address('firm_version')
        self.firmware_version = '---'

        self.error_request = [int(i, 16) if i else 0 for i in check_string('errors_req').split(',')]
        self.errors_list = err_list
        self.current_errors_list = set()

        self.warning_request = [int(i, 16) if i else 0 for i in check_string('warnings_req').split(',')]
        self.warnings_list = war_list
        self.current_warnings_list = set()

        self.error_erase = {'address': check_address('errors_erase'),
                            'value': int(check_address('v_errors_erase'))}

        self.group_params_dict = group_par_dict
        self.string_from_can = ''
        self.save_to_eeprom = check_address('to_eeprom')
        self.load_from_eeprom = check_address('from_eeprom')
        self.has_compare_params = False

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

        if isinstance(value, str):
            return value

        if self.protocol == 'CANOpen':
            if value[0] == 0x41:
                value = self.read_string_from_can(adapter)
                if isinstance(value, str):
                    return value
            else:
                value = (value[7] << 24) + \
                        (value[6] << 16) + \
                        (value[5] << 8) + value[4]
        elif self.protocol == 'MODBUS':
            value = value[0]
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
        # for i in r_list:
        #     print(hex(i), end=' ')
        # print()
        # while adapter.is_busy:
        #     pass
        value = adapter.can_request(self.request_id, self.answer_id, r_list)

        if isinstance(value, str):
            return value  # если вернул строку, значит, проблема
        else:
            # for i in value:
            #     print(hex(i), end=' ')
            # print()
            return ''  # если пусто, значит, норм ушла

    def get_serial_number(self, adapter: CANAdater):
        if not isinstance(self.serial_number, str):
            return self.serial_number

        serial = self.get_val(self.request_serial_number, adapter) if self.request_serial_number else 777

        if isinstance(serial, str):
            if self.string_from_can:
                self.string_from_can = ''
            else:
                serial = '---'

        self.serial_number = serial
        # print(f'{self.name} - {serial=}')
        return self.serial_number

    def get_firmware_version(self, adapter: CANAdater):
        if not isinstance(self.firmware_version, str):
            return self.firmware_version
        f_list = self.get_val(self.request_firmware_version, adapter) if self.request_firmware_version else 0
        if isinstance(f_list, str):
            if self.string_from_can:
                self.string_from_can = ''
            else:
                f_list = '---'
        self.firmware_version = f_list
        # print(f'{self.name} - {f_list=}')
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

    def check_errors(self, adapter: CANAdater, er_or_war=None):
        if er_or_war is None:
            er_or_war = 'errors'
        #  на выходе - список текущих ошибок
        if 'er' in er_or_war:
            r_request = self.error_request.copy()
            s_list = self.errors_list.copy()
            current_list = self.current_errors_list.copy()
        else:
            r_request = self.warning_request.copy()
            s_list = self.warnings_list.copy()
            current_list = self.current_warnings_list.copy()
        if not r_request or not s_list:
            return current_list
        err_dict = {int(v['value_error'], 16) if '0x' in str(v['value_error']) else int(v['value_error']):
                        v['description_error'] for v in s_list}
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
                    current_list.add('Неизвестная ошибка')
            else:
                for e_num, e_name in err_dict.items():
                    if big_error & e_num:
                        current_list.add(e_name)
        return current_list

    def erase_errors(self, adapter: CANAdater):
        #  на выходе - список оставшихся ошибок или пустой список, если ОК
        if self.error_erase['address']:
            at = self.send_val(self.error_erase['address'], adapter, self.error_erase['value'])
            self.current_errors_list.clear()
            self.current_warnings_list.clear()
            if not at:
                self.check_errors(adapter)
            else:
                self.current_errors_list.add(f'{self.name}: Удалить ошибки не удалось потому что {at} \n')
        return self.current_errors_list

    def read_string_from_can(self, adapter: CANAdater):
        value = adapter.can_request(self.request_id, self.answer_id, [0x60, 0, 0, 0, 0, 0, 0, 0])
        if isinstance(value, str):
            self.string_from_can = ''
            return value

        for byte in value:
            self.string_from_can += chr(byte)

        return int(self.string_from_can.strip()) if self.string_from_can.strip().isdigit() \
            else self.string_from_can.strip()
