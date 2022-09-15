class EVONode:
    def __init__(self, nod: dict):
        self.request_id = 0x500
        self.answer_id = 0x481
        self.protocol = 'CANOpen'
        self.serial_number = '---'
        self.firmware_version = '---'
        self.error_request = ['0x000000']
        self.error_erase = '0x000000'
        self.errors_list = []

    def get_serial_number(self):
        pass

    def get_firmware_version(self):
        pass

    def get_parametr(self, address=0, name_parametr=''):
        pass

    def change_parametr(self, address=0, name_parametr=''):
        pass

    def check_errors(self):
        pass

    def erase_errors(self):
        pass

    def is_connected(self):  # возможно, это нужно сделать просто полем
        pass
