class AdapterCAN:
    def check_bitrate(self):
        pass

    def canal_open(self):
        pass

    def close_canal_can(self):
        pass

    def can_write(self, ID: int, data: list):
        pass

    def can_read(self, ID: int):
        pass

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        pass
