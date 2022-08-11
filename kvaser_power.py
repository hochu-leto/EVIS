import time

from canlib import canlib, Frame

'''
    canStatus = {
    canOK = 0,
    canERR_PARAM = -1,
    canERR_NOMSG = -2,
    canERR_NOTFOUND = -3,
    canERR_NOMEM = -4,
    canERR_NOCHANNELS = -5,
    canERR_INTERRUPTED = -6,
    canERR_TIMEOUT = -7,
    canERR_NOTINITIALIZED = -8,
    canERR_NOHANDLES = -9,
    canERR_INVHANDLE = -10,
    canERR_INIFILE = -11,
    canERR_DRIVER = -12,
    canERR_TXBUFOFL = -13,
    canERR_RESERVED_1 = -14,
    canERR_HARDWARE = -15,
    canERR_DYNALOAD = -16,
    canERR_DYNALIB = -17,
    canERR_DYNAINIT = -18,
    canERR_NOT_SUPPORTED = -19,
    canERR_RESERVED_5 = -20,
    canERR_RESERVED_6 = -21,
    canERR_RESERVED_2 = -22,
    canERR_DRIVERLOAD = -23,
    canERR_DRIVERFAILED = -24,
    canERR_NOCONFIGMGR = -25,
    canERR_NOCARD = -26,
    canERR_RESERVED_7 = -27,
    canERR_REGISTRY = -28,
    canERR_LICENSE = -29,
    canERR_INTERNAL = -30,
    canERR_NO_ACCESS = -31,
    canERR_NOT_IMPLEMENTED = -32,
    canERR_DEVICE_FILE = -33,
    canERR_HOST_FILE = -34,
    canERR_DISK = -35,
    canERR_CRC = -36,
    canERR_CONFIG = -37,
    canERR_MEMO_FAIL = -38,
    canERR_SCRIPT_FAIL = -39,
    canERR_SCRIPT_WRONG_VERSION = -40,
    canERR_SCRIPT_TXE_CONTAINER_VERSION = -41,
    canERR_SCRIPT_TXE_CONTAINER_FORMAT = -42,
    canERR_BUFFER_TOO_SMALL = -43,
    canERR_IO_WRONG_PIN_TYPE = -44,
    canERR_IO_NOT_CONFIRMED = -45,
    canERR_IO_CONFIG_CHANGED = -46,
    canERR_IO_PENDING = -47,
    canERR_IO_NO_VALID_CONFIG = -48,
    canERR__RESERVED = -49
    }
'''
canERR_WRONG_DATA = -14
canERR_NO_ECU_ANSWER = -20
error_codes = {
    - 15: 'Проблемы с адаптером',
    65535 - 1: 'generic (not specified) error',
    65535 - 2: 'device or recourse busy',
    65535 - 3: 'memory fault',
    65535 - 4: "function can't be called for chip in current state",
    65535 - 5: "invalid call, function can't be called for this object",
    65535 - 6: 'invalid parameter - номер канала, переданный в качестве параметра, выходит за '
               'пределы поддерживаемого числа каналов, либо канал не был открыт;',
    65535 - 7: 'can not access resource',
    65535 - 8: 'function or feature not implemented',
    -3: 'Адаптер не подключен',
    65535 - 10: 'no such device or object',
    65535 - 11: 'call was interrupted by event',
    65535 - 12: 'no resources',
    65535 - 13: 'time out occured',
    -2: 'Нет CAN шины больше секунды',
    -20: 'Нет ответа от блока управления',
    -14: 'Неправильные данные для передачи. Нужен список',
}


class Kvaser:
    can_bitrate = {
        125: canlib.Bitrate.BITRATE_125K,
        250: canlib.Bitrate.BITRATE_250K,
        500: canlib.Bitrate.BITRATE_500K
    }

    def __init__(self, channel=0, bit=125):
        self.openFlags = canlib.Open.ACCEPT_VIRTUAL
        self.outputControl = canlib.Driver.NORMAL
        self.can_canal_number = channel  # по умолчанию нулевой канал
        if bit in self.can_bitrate.keys():
            self.bitrate = self.can_bitrate[bit]
        else:
            self.bitrate = canlib.Bitrate.BITRATE_125K  # и скорость 125

        self.wait_time = 300
        self.max_iteration = 5
        # может, это не совсем верный подход, но я пытаюсь стандартизировать под марафон
        # self.ch = self.canal_open()
        self.ch = self.canal_open()

    def canal_open(self):
        for i in range(self.max_iteration):
            canlib.reinitializeLibrary()
            try:
                chdata = canlib.ChannelData(self.can_canal_number).card_serial_no
                if chdata:
                    break
            except canlib.canError as ex:
                # print(f' В canal_open_card_serial_no  так  {ex}')
                if ex.status in error_codes.keys():
                    return error_codes[ex.status]
                return str(ex)
            if i == self.max_iteration - 1 and not chdata:
                return error_codes[canlib.canERR_NOTFOUND]
        try:
            ch = canlib.openChannel(channel=self.can_canal_number, flags=self.openFlags, bitrate=self.bitrate)
            ch.setBusOutputControl(self.outputControl)
            ch.busOn()
            # print(f' В canal_open2  так  {ch}')
            return ch
        except canlib.canError as ex:
            print(f' В canal_open2  так  {ex}')
            if ex.status in error_codes.keys():
                return error_codes[ex.status]
            return str(ex)

    def close_canal_can(self):
        # if not isinstance(self.ch, canlib.Channel):
        #     return
        # try:
        #     self.ch.busOff()
        #     self.ch.close()
        #     return ''
        # except canlib.canError as ex:
        #     if ex.status in error_codes.keys():
        #         return error_codes[ex.status]
        #     return str(ex)
        pass

    def can_write(self, ID: int, data: list):
        if not isinstance(data, list):
            return error_codes[canERR_WRONG_DATA]

        if not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()

        if not isinstance(self.ch, canlib.Channel):
            return self.ch

        frame = Frame(
            id_=ID,
            data=data,
            flags=canlib.MessageFlag.EXT)

        try:
            self.ch.write(frame)
            return ''
        except canlib.canError == canlib.canERR_INVHANDLE:
            self.ch = self.canal_open()
            self.ch.write(frame)
            return ''
        except canlib.canError as ex:
            if ex.status in error_codes.keys():
                return error_codes[ex.status]
            return str(ex)

    def can_read(self, ID: int):
        last_frame_time = int(round(time.time() * 1000))

        if not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()

        if not isinstance(self.ch, canlib.Channel):
            return self.ch

        while True:
            current_time = int(round(time.time() * 1000))
            if current_time > (last_frame_time + self.wait_time):
                return error_codes[canlib.canERR_NOMSG]

            try:
                frame = self.ch.read()
            except canlib.canError as ex:
                print(f' В canal_open  так  {ex}')
                if ex.status in error_codes.keys():
                    return error_codes[ex.status]
                return str(ex)

            if frame.id == ID:
                return frame.data

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        if not isinstance(message, list):
            return error_codes[canERR_WRONG_DATA]
        # print('реквест')
        # проверяю вообще подключен ли квасер, если да, то ошибки быть не должно
        i = 0
        while not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()
            i += 1
            if i == self.max_iteration:
                return self.ch

        frame = Frame(
            id_=can_id_req,
            data=message,
            flags=canlib.MessageFlag.EXT)

        try:
            self.ch.write(frame)
        except canlib.canError as ex:
            er = ex.status
            self.ch = self.canal_open()
            if er in error_codes.keys():
                return error_codes[er]
            else:
                return str(ex)

        no_msg = False
        last_frame_time = int(round(time.time() * 1000))
        while True:
            current_time = int(round(time.time() * 1000))

            if current_time > (last_frame_time + self.wait_time):
                if frame.id == 0 or frame.id == can_id_req:
                    return error_codes[canlib.canERR_NOMSG]
                else:
                    return error_codes[canERR_NO_ECU_ANSWER]

            try:
                frame = self.ch.read()
                no_msg = False
            except (canlib.canNoMsg) as ex:
                no_msg = True
            except canlib.canError as ex:
                if ex.status in error_codes.keys():
                    return error_codes[ex.status]
                return str(ex)
            print(f'frane id = {frame.id}  no_msg = {no_msg}')
            if frame.id == can_id_ans:
                return frame.data
