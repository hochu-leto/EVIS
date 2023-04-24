import os
import pathlib
import time

os.environ['KVDLLPATH'] = str(pathlib.Path(pathlib.Path.cwd(), 'Kvaser_Driver_and_dll'))

from canlib import canlib, Frame

can_bitrate = {
    125: canlib.Bitrate.BITRATE_125K,
    250: canlib.Bitrate.BITRATE_250K,
    500: canlib.Bitrate.BITRATE_500K
}


class KvaserChannel1:
    def __init__(self):
        self.wait_time = 500
        self.max_iteration = 5
        self.is_busy = False
        self.ch = None
        self.text = ''
        self.defined_channels_count = 0

    def close_canal_can(self):
        pass
        # охренительная логика -  если использовать .busOff()
        # то возникает ошибка по переполнению буфера отправки Transmit buffer overflow (-13)
        # self.ch.busOff()

    def canal_open(self):  # если канал если он нашёлся или строку с ошибкой
        # открываю канал с заданными параметрами и возвращаю его
        try:
            self.ch = canlib.openChannel(channel=1,
                                         flags=canlib.Open.OVERRIDE_EXCLUSIVE,
                                         bitrate=canlib.Bitrate.BITRATE_250K)
            self.ch.setBusOutputControl(canlib.Driver.NORMAL)
            self.ch.busOn()
            self.is_busy = False
            self.text += f' успешно открыт канал 0'
            return ''
        except canlib.canError as ex:
            print(f' В canal_open2  так  {ex}')
            t = f' при открытии канала 0 возникла проблема {ex}'
            self.text += t
            return t

    def can_write(self, ID: int, data: list):
        if not isinstance(data, list):
            return 'Неправильные данные пытаемся отправить в канал 0'

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()

        fl = canlib.MessageFlag.EXT if ID > 0x7FF else canlib.MessageFlag.STD

        frame = Frame(
            id_=ID,
            data=data,
            flags=fl)

        try:
            self.is_busy = True
            self.ch.write(frame)
            self.is_busy = False
        except canlib.canError as ex:
            self.is_busy = False
            self.text += f' ошибка при отправке в канал 0 -> {ex}'
            return self.text

        return ''

    def can_read(self, ID: int):
        last_frame_time = time.perf_counter_ns()

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()

        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_frame_time:

            try:
                self.is_busy = True
                frame = self.ch.read()
            except canlib.canError as ex:
                self.is_busy = False
                if ex.status == canlib.canERR_NOMSG:
                    continue
                print(f'    В can_read  так  {ex}')
                self.text += f' ошибка при чтении с канала 0 -> {ex}'
                return self.text
            else:
                self.is_busy = False

            if frame.id == ID:
                return frame.data
        self.text += f' нет ответа в канале 0'
        return self.text

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
        exit_list = []
        for frame_counter in range((l_byte // 7) + 1):
            message = [0x70, 0, 0, 0, 0, 0, 0, 0] if frame_counter % 2 else [0x60, 0, 0, 0, 0, 0, 0, 0]
            if not self.can_write(can_id_req, message):
                data = self.can_read(can_id_ans)
                if not isinstance(data, str):
                    exit_list += data
        self.is_busy = False
        return exit_list


class KvaserChannel2:
    def __init__(self):
        self.wait_time = 500
        self.max_iteration = 5
        self.is_busy = False
        self.ch = None  # self.canal_open()
        self.text = ''

    def close_canal_can(self):
        pass

    def canal_open(self):  # если канал если он нашёлся или строку с ошибкой
        # открываю канал с заданными параметрами и возвращаю его
        try:
            self.ch = canlib.openChannel(channel=0,
                                         flags=canlib.Open.OVERRIDE_EXCLUSIVE,
                                         bitrate=canlib.Bitrate.BITRATE_125K)
            self.ch.setBusOutputControl(canlib.Driver.NORMAL)
            self.ch.busOn()
            self.is_busy = False
            self.text += f' успешно открыт канал 1'
            return ''
        except canlib.canError as ex:
            print(f' В canal_open2  так  {ex}')
            t = f' при открытии канала 1 возникла проблема {ex}'
            self.text += t
            return t

    def can_write(self, ID: int, data: list):
        if not isinstance(data, list):
            return 'Неправильные данные пытаемся отправить в канал 1'

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()

        fl = canlib.MessageFlag.EXT if ID > 0x7FF else canlib.MessageFlag.STD

        frame = Frame(
            id_=ID,
            data=data,
            flags=fl)

        try:
            self.is_busy = True
            self.ch.write(frame)
            self.is_busy = False
        except canlib.canError as ex:
            self.is_busy = False
            self.text += f' ошибка при отправке в канал 1 -> {ex}'
            return self.text

        return ''

    def can_read(self, ID: int):
        last_frame_time = time.perf_counter_ns()

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()

        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_frame_time:

            try:
                self.is_busy = True
                frame = self.ch.read()
            except canlib.canError as ex:
                self.is_busy = False
                if ex.status == canlib.canERR_NOMSG:
                    continue
                print(f'    В can_read  так  {ex}')
                self.text += f' ошибка при чтении с канала 1 -> {ex}'
                return self.text
            else:
                self.is_busy = False

            if frame.id == ID:
                return frame.data
        self.text += f' нет ответа в канале 1'
        return self.text

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
        exit_list = []
        for frame_counter in range((l_byte // 7) + 1):
            message = [0x70, 0, 0, 0, 0, 0, 0, 0] if frame_counter % 2 else [0x60, 0, 0, 0, 0, 0, 0, 0]
            if not self.can_write(can_id_req, message):
                data = self.can_read(can_id_ans)
                if not isinstance(data, str):
                    exit_list += data
        self.is_busy = False
        return exit_list


class KvaserChannel:
    def __init__(self, channel=0, bitrate=125):
        self.wait_time = 500
        self.max_iteration = 5
        self.is_busy = False
        self.ch = None
        self.text = ''
        self.channel_number = channel
        self.bitrate = bitrate

    def close_canal_can(self):
        pass

    def canal_open(self):  # если канал если он нашёлся или строку с ошибкой
        # открываю канал с заданными параметрами и возвращаю его
        try:
            self.ch = canlib.openChannel(channel=self.channel_number,
                                         flags=canlib.Open.OVERRIDE_EXCLUSIVE,
                                         bitrate=can_bitrate[self.bitrate])
            self.ch.setBusOutputControl(canlib.Driver.NORMAL)
            self.ch.busOn()
            self.is_busy = False
            self.text += f' успешно открыт канал 1'
            return ''
        except canlib.canError as ex:
            print(f' В canal_open2  так  {ex}')
            t = f' при открытии канала 1 возникла проблема {ex}'
            self.text += t
            return t

    def can_write(self, ID: int, data: list):
        if not isinstance(data, list):
            return 'Неправильные данные пытаемся отправить в канал 1'

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()

        fl = canlib.MessageFlag.EXT if ID > 0x7FF else canlib.MessageFlag.STD

        frame = Frame(
            id_=ID,
            data=data,
            flags=fl)

        try:
            self.is_busy = True
            self.ch.write(frame)
            self.is_busy = False
        except canlib.canError as ex:
            self.is_busy = False
            self.text += f' ошибка при отправке в канал 1 -> {ex}'
            return ex

        return ''

    def clear_rx_buffer(self) -> bool:
        last_time = time.perf_counter_ns()
        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_time:
            try:
                frame = self.ch.read()
                print(frame.id)
            except canlib.CanNoMsg as ex:
                return True
            except canlib.canError as ex:
                print(ex)
                return False
        return False

    def can_read(self, ID: int):
        last_frame_time = time.perf_counter_ns()

        if not isinstance(self.ch, canlib.Channel):
            self.canal_open()
        self.clear_rx_buffer()
        while (time.perf_counter_ns() - self.wait_time * 100_000) < last_frame_time:

            try:
                self.is_busy = True
                frame = self.ch.read(200)
            except canlib.canError as ex:
                if ex.status == canlib.canERR_NOMSG:
                    continue
                self.is_busy = False
                print(f'    В can_read  так  {ex}')
                self.text += f' ошибка при чтении с канала 1 -> {ex}'
                return ex
            else:
                self.is_busy = False

            if frame.id == ID:
                return frame.data
        self.text += f' нет ответа'
        return canlib.canERR_NOMSG

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        data = 'Не могу запросить параметр'
        for _ in range(self.max_iteration):
            data = self.can_write(can_id_req, message)
            if not data:
                data = self.can_read(can_id_ans)
                if not isinstance(data, canlib.Error):
                    break
            else:
                break

        return data

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):
        exit_list = []
        for frame_counter in range((l_byte // 7) + 1):
            message = [0x70, 0, 0, 0, 0, 0, 0, 0] if frame_counter % 2 else [0x60, 0, 0, 0, 0, 0, 0, 0]
            if not self.can_write(can_id_req, message):
                data = self.can_read(can_id_ans)
                if not isinstance(data, str):
                    exit_list += data
        self.is_busy = False
        return exit_list


def hardware_kvaser_channels() -> dict[int:int]:
    exit_dict = {}
    for ch in range(canlib.enumerate_hardware()):
        if canlib.ChannelData(ch).card_type > canlib.HardwareType.VIRTUAL:
            for name_bit, bit in can_bitrate.items():
                try:
                    channel = canlib.openChannel(channel=ch,
                                                 flags=canlib.Open.OVERRIDE_EXCLUSIVE,
                                                 bitrate=bit)
                    channel.setBusOutputControl(canlib.Driver.NORMAL)
                    channel.busOn()
                except canlib.canError as ex:
                    print(f' при открытии канала 1 возникла проблема {ex}')
                    break

                try:
                    frame = channel.read(200)
                    if frame.id != 0:
                        print(' успешно определён')
                        exit_dict[ch] = name_bit
                except canlib.CanNoMsg as ex:
                    print(f', но не подключен к шине CAN')
                except canlib.canError as ex:
                    print(f' при определении скорости канала возникла проблема {ex}')

                channel.busOff()
                channel.close()

    return exit_dict
