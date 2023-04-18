import os
import pathlib
import time

os.environ['KVDLLPATH'] = str(pathlib.Path(pathlib.Path.cwd(), 'Kvaser_Driver_and_dll'))

from canlib import canlib, Frame

from AdapterCAN import AdapterCAN

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
    -5: 'function or feature not implemented - скорость шины не определена',
    -3: 'Адаптер не подключен',
    65535 - 10: 'no such device or object',
    65535 - 11: 'call was interrupted by event',
    65535 - 12: 'no resources',
    65535 - 13: 'time out occured',
    -2: 'Нет CAN шины больше секунды',
    -20: 'Нет ответа от блока управления',
    -14: 'Неправильные данные для передачи. Нужен список',
}


class Kvaser(AdapterCAN):
    can_bitrate = {
        125: canlib.Bitrate.BITRATE_125K,
        250: canlib.Bitrate.BITRATE_250K,
        500: canlib.Bitrate.BITRATE_500K
    }

    def __init__(self, channel=0, bit=125):
        canlib.initializeLibrary()
        self.openFlags = canlib.Open.OVERRIDE_EXCLUSIVE & ~canlib.Open.ACCEPT_VIRTUAL
        self.outputControl = canlib.Driver.NORMAL
        self.can_canal_number = channel  # по умолчанию нулевой канал
        if bit in self.can_bitrate.keys():
            self.bitrate = self.can_bitrate[bit]
        else:
            self.bitrate = canlib.Bitrate.BITRATE_125K  # и скорость 125

        self.wait_time = 500
        self.max_iteration = 5
        self.is_busy = False
        self.ch = None  # self.canal_open()

    def clear_rx_buffer(self, chan: canlib.Channel) -> bool:
        last_time = time.perf_counter_ns()
        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_time:
            try:
                frame = chan.read()
                print(frame.id)
            except canlib.CanNoMsg as ex:
                return True
            except canlib.canError as ex:
                print(ex)
                return False

        return False

    def check_bitrate(self):
        for name_bit, bit in self.can_bitrate.items():
            print(f'Проверяю битрейт {name_bit}')

            self.bitrate = bit
            i = 0
            # # если канал уже есть, его обнуляем
            # if isinstance(self.ch, canlib.Channel):
            #     self.ch.busOff()
            #     self.ch.close()
            self.ch = None
            # пока нет канала, пытаемся его открыть, пока не кончились итерации
            while not isinstance(self.ch, canlib.Channel):
                self.ch = self.canal_open()
                i += 1
                if i == self.max_iteration:
                    return self.ch

            last_frame_time = time.perf_counter_ns()  # int(round(time.time() * 1000))
            # current_time = 0
            print(self.clear_rx_buffer(self.ch))
            while (time.perf_counter_ns() - self.wait_time * 100_000) < last_frame_time:
                # current_time < (last_frame_time + self.wait_time):
                # current_time = int(round(time.time() * 1000))
                try:
                    # self.ch.iocontrol.flush_tx_buffer()
                    # self.ch.iocontrol.flush_rx_buffer()
                    frame = self.ch.read()
                    if frame.id != 0:
                        # self.ch.busOff()
                        return name_bit
                except canlib.CanNoMsg as ex:
                    pass
                except canlib.canError as ex:
                    if ex.status in error_codes.keys():
                        return error_codes[ex.status]
                    return str(ex)

        return error_codes[canlib.canERR_NOCHANNELS]

    def canal_open(self):  # если канал если он нашёлся или строку с ошибкой
        # сначала несколько раз перезагружаем библиотеку и проверяем не появился ли канал с текущим номером
        # кажется, уже найденный канал слетит, если при поиске следующего будем перезагружать библиотеку
        is_hw_channel = canlib.ChannelData(self.can_canal_number).card_type
        if is_hw_channel == canlib.HardwareType.NONE or is_hw_channel == canlib.HardwareType.VIRTUAL:
            return 'Kvaser не обнаружен'
            # for i in range(self.max_iteration):
            #     # canlib.reinitializeLibrary()
            #     try:
            #         chdata = canlib.ChannelData(self.can_canal_number).card_serial_no
            #         if chdata:  # если серийный номер карты не ноль, то это реальный адаптер, выходим из цикла
            #             break   # надо по другому определять что есть реальный канал
            #     except canlib.canError as ex:
            #         if ex.status in error_codes.keys():
            #             return error_codes[ex.status]
            #         return str(ex)
            #     if i == self.max_iteration - 1 and not chdata:
            #         return error_codes[canlib.canERR_NOTFOUND]
        # открываю канал с заданными параметрами и возвращаю его
        try:
            ch = canlib.openChannel(channel=self.can_canal_number, flags=self.openFlags, bitrate=self.bitrate)
            ch.setBusOutputControl(self.outputControl)
            ch.busOn()
            self.is_busy = False

            return ch
        except canlib.canError as ex:
            print(f' В canal_open2  так  {ex}')
            if ex.status in error_codes.keys():
                return error_codes[ex.status]
            return str(ex)

    def close_canal_can(self):
        pass

    def can_write(self, ID: int, data: list):
        if not isinstance(data, list):
            return error_codes[canERR_WRONG_DATA]

        if not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()

        if not isinstance(self.ch, canlib.Channel):
            return self.ch

        fl = canlib.MessageFlag.EXT if ID > 0x7FF else canlib.MessageFlag.STD

        frame = Frame(
            id_=ID,
            data=data,
            flags=fl)

        try:
            self.is_busy = True
            self.ch.write(frame)
        except canlib.canError as ex:
            self.is_busy = False
            if ex.status in error_codes.keys():
                return error_codes[ex.status]
            return str(ex)
        else:
            self.is_busy = False
        return ''

    def can_read(self, ID: int):
        last_frame_time = time.perf_counter_ns()

        if not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()

        if not isinstance(self.ch, canlib.Channel):
            return self.ch

        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_frame_time:

            try:
                self.is_busy = True
                frame = self.ch.read()
            except canlib.canError as ex:
                self.is_busy = False
                if ex.status == canlib.canERR_NOMSG:
                    continue
                print(f'    В can_read  так  {ex}')
                if ex.status in error_codes.keys():
                    return error_codes[ex.status]
                return str(ex)
            else:
                self.is_busy = False

            if frame.id == ID:
                return frame.data

        return error_codes[canlib.canERR_NOMSG]

    # def can_request(self, can_id_req: int, can_id_ans: int, message: list):
    #     if not isinstance(message, list):
    #         return error_codes[canERR_WRONG_DATA]
    #     # проверяю вообще подключен ли квасер, если да, то ошибки быть не должно
    #     i = 0
    #     while not isinstance(self.ch, canlib.Channel):
    #         self.ch = self.canal_open()
    #         i += 1
    #         if i == self.max_iteration:
    #             return self.ch
    #
    #     if can_id_req > 0x0000FFF:
    #         flags = canlib.MessageFlag.EXT
    #     else:
    #         flags = canlib.MessageFlag.STD
    #
    #     frame = Frame(
    #         id_=can_id_req,
    #         data=message,
    #         flags=flags)
    #     # canlib.Channel(self.can_canal_number)
    #     try:
    #         self.is_busy = True
    #         self.ch.free_objbuf()
    #         self.ch.write(frame)
    #     except canlib.canError as ex:
    #         er = ex.status
    #         self.ch = self.canal_open()
    #         if er in error_codes.keys():
    #             return error_codes[er]
    #         else:
    #             return str(ex)
    #
    #     last_frame_time = int(round(time.time() * 1000))
    #     while True:
    #         current_time = int(round(time.time() * 1000))
    #         if current_time > (last_frame_time + self.wait_time):
    #             if frame.id == 0 or frame.id == can_id_req:
    #                 print('frame.id = ', frame.id, 'can_id_req = ', can_id_req)
    #                 return error_codes[canlib.canERR_NOMSG]
    #             else:
    #                 return error_codes[canERR_NO_ECU_ANSWER]
    #
    #         try:
    #             frame = self.ch.read()
    #             self.is_busy = False
    #         except canlib.CanNoMsg as ex:
    #             pass
    #         except canlib.canError as ex:
    #             if ex.status in error_codes.keys():
    #                 return error_codes[ex.status]
    #             return str(ex)
    #         if frame.id == can_id_ans:
    #             # проверить это
    #             self.ch.busOff()
    #             return frame.data
    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        data = 'Не могу запросить параметр'
        for _ in range(self.max_iteration):
            data = self.can_write(can_id_req, message)
            if not data:
                data = self.can_read(can_id_ans)
                if not isinstance(data, str):
                    break
            else:
                break

        return data

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):

        i = 0
        while not isinstance(self.ch, canlib.Channel):
            self.ch = self.canal_open()
            i += 1
            if i == self.max_iteration:
                return self.ch

        if can_id_req > 0x0000FFF:
            flags = canlib.MessageFlag.EXT
        else:
            flags = canlib.MessageFlag.STD

        exit_list = []

        for frame_counter in range((l_byte // 7) + 1):
            message = [0x70, 0, 0, 0, 0, 0, 0, 0] if frame_counter % 2 else [0x60, 0, 0, 0, 0, 0, 0, 0]
            frame = Frame(
                id_=can_id_req,
                data=message,
                flags=flags)

            try:
                self.is_busy = True
                self.ch.write(frame)
            except canlib.canError as ex:
                er = ex.status
                self.ch = self.canal_open()
                if er in error_codes.keys():
                    return error_codes[er]
                else:
                    return str(ex)

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
                except canlib.CanNoMsg as ex:
                    pass
                except canlib.canError as ex:
                    if ex.status in error_codes.keys():
                        return error_codes[ex.status]
                    return str(ex)

                if frame.id == can_id_ans:
                    exit_list += frame.data
                    break
        self.is_busy = False
        return exit_list
