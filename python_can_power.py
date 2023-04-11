from AdapterCAN import AdapterCAN


class PythonCan(AdapterCAN):
    can_bitrate = {
        125: 125000,
        250: 250000,
        500: 500000
    }

    def __init__(self, channel=0, bit=125):
        if bit in self.can_bitrate.keys():
            self.bitrate = self.can_bitrate[bit]
        else:
            self.bitrate = 125000  # и скорость 125
        self.wait_time = 300
        self.max_iteration = 5

    def check_bitrate(self):
        for name_bit, bit in self.can_bitrate.items():
            print(f'Проверяю битрейт {name_bit}')
        return name_bit

    def canal_open(self):  # если канал если он нашёлся или строку с ошибкой
        pass

    def close_canal_can(self):
        pass

    def can_write(self, ID: int, data: list):
        return ''

    def can_read(self, ID: int):
        data = []
        return data

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        data = []
        return data

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):
        exit_list = []
        return exit_list
