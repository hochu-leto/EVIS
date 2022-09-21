import ctypes

import CANAdater
from helper import int_to_hex_str

empty_node = {
    'name': 'NoName',
    'req_id': 0x500,
    'ans_id': 0x481,
    'protocol': 'CANOpen',
    'serial_number': 0,
    'firm_version': 0,
    'errors_req': ['0x000000'],
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
                 'errors_dict', 'current_errors_list', 'group_params_dict')

    def __init__(self, nod=None, err_dict=None, group_par_dict=None):
        if group_par_dict is None:
            group_par_dict = {}
        if err_dict is None:
            err_dict = {}
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
        self.error_request = nod['errors_req'].split(',')  # не могу придумать проверку
        self.error_erase = {'address': check_address('errors_erase'),
                            'value': check_address('v_errors_erase')}
        self.errors_dict = err_dict
        self.current_errors_list = []
        self.group_params_dict = group_par_dict

    def get_val(self, address: int, adapter: CANAdater):
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        r_list = []

        if self.protocol == 'CANOpen':
            r_list = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
        if self.protocol == 'MODBUS':
            r_list = [0, 0, 0, 0, sub_index, LSB, 0x2B, 0x03]

        value = adapter.can_request(self.request_id, self.answer_id, r_list)

        if isinstance(value, str):
            return value
        if self.protocol == 'CANOpen':
            value = (value[7] << 24) + \
                    (value[6] << 16) + \
                    (value[5] << 8) + value[4]
        elif self.protocol == 'MODBUS':
            value = value[0]
        else:
            value = ctypes.c_int32(value)
        return value

    def get_serial_number(self, adapter: CANAdater):
        if not isinstance(self.serial_number, str):
            return self.serial_number
        serial = self.get_val(self.request_serial_number, adapter)
        if isinstance(serial, str):
            serial = '---'
        self.serial_number = serial
        return self.serial_number

    def get_firmware_version(self, adapter: CANAdater):
        if not isinstance(self.firmware_version, str):
            return self.firmware_version
        f_list = self.get_val(self.request_firmware_version, adapter)
        if isinstance(f_list, str):
            f_list = '---'
        self.firmware_version = f_list
        return self.firmware_version

    def cut_firmware(self):
        if isinstance(self.firmware_version, int):
            fm = self.firmware_version
            if fm > 0xFFFF:
                text = int_to_hex_str((fm & 0xFF00) >> 8) + \
                       '.' + int_to_hex_str(fm & 0xFF)
                text = text.upper()
            else:
                text = str(fm)
            return text
        return self.firmware_version

    def get_nodetr(self, address=0, name_nodetr=''):
        pass

    def change_nodetr(self, address=0, name_nodetr=''):
        pass

    def check_errors(self, adapter: CANAdater):
        #  на выходе - список текущих ошибок
        error_list = []
        e_str = ''
        for adr in self.error_request:
            adr_int = int(adr, 16)
            error = self.get_val(adr_int, adapter)
            if error < 128:
                for e_num, e_name in self.errors_dict.items():

                    pass
            else:
                if error in self.errors_dict.keys():
                    e_str = self.errors_dict[error]
            if e_str:
                error_list.append(e_str)
        self.current_errors_list = error_list
        return error_list

    def erase_errors(self, adapter: CANAdater):
        #  на выходе - список оставшихся ошибок или пустой список, если ОК
        pass

    def is_connected(self):  # возможно, это нужно сделать просто полем
        pass
