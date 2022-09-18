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
                            else value))
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
        self.error_request = nod['errors_req'].split(',')   # не могу придумать проверку
        self.error_erase = {'address': check_address('errors_erase'),
                            'value': check_address('v_errors_erase')}
        self.errors_dict = err_dict
        self.group_params_dict = group_par_dict

    def get_serial_number(self):
        pass

    def get_firmware_version(self):
        pass

    def get_nodetr(self, address=0, name_nodetr=''):
        pass

    def change_nodetr(self, address=0, name_nodetr=''):
        pass

    def check_errors(self):
        pass

    def erase_errors(self):
        pass

    def is_connected(self):  # возможно, это нужно сделать просто полем
        pass
