import ctypes
import time
НЕ ПРОКАТИЛО
from PyQt5.QtCore import QTimer

from CANAdater import CANAdapter

can_adapter = CANAdapter()
if not can_adapter.isDefined:
    can_adapter = CANAdapter()
#
# bku_kvu_id = {'id': int('0x18FF51A5', 16), 'bit': 250, 'scale': 1, 'f_byte': 1}
# kvu_bku_id = {'id': int('0x18FF34A1', 16), 'bit': 250, 'scale': 300, 'f_byte': 3}
# kvu_burr_id = {'id': int('0x314', 16), 'bit': 125, 'scale': 10, 'f_byte': 2}
# burr_kvu_id = {'id': int('0x18f', 16), 'bit': 125, 'scale': 10, 'f_byte': 2}


bku_kvu_id = {'id': int('0x04FF81A5', 16), 'bit': 250, 'scale': 100, 'LSB': 3, 'MSB': 4, 'offset': 10000}
kvu_bku_id = {'id': int('0x18FF55A1', 16), 'bit': 250, 'scale': 300, 'LSB': 1, 'MSB': 2, 'offset': 30000}
kvu_burr_id = {'id': int('0x314', 16), 'bit': 125, 'scale': 10, 'LSB': 1, 'MSB': 2, 'offset': 0}
burr_kvu_id = {'id': int('0x18f', 16), 'bit': 125, 'scale': 10, 'LSB': 2, 'MSB': 1, 'offset': 0}


def on_off_kvu(swich: bool):
    print(swich)
    can_adapter.can_send(bku_kvu_id['id'], [int(swich), 0, 0, 0, 100, 0, 100, 0], bku_kvu_id['bit'])

    bku_burr_time = time_resp(kvu_burr_id, swich)

    burr_kvu_time = time_resp(burr_kvu_id, swich)

    kvu_bku_time = time_resp(kvu_bku_id, swich)

    print(f'{bku_burr_time=}, {burr_kvu_time=}, {kvu_bku_time=}')
    return bku_burr_time, burr_kvu_time, kvu_bku_time


def time_resp(id: dict, sw: bool):
    start_time = time.perf_counter()
    t = 0
    while t < 15:
        ans = can_adapter.can_read(id['id'], bitrate=id['bit'])
        if not isinstance(ans, str):
            if ans[0] & 0x01 == int(sw):
                print('Время когда получил нужный ответ', time.perf_counter() - start_time)
                return time.perf_counter() - start_time
        t += 1
    return False


def read_ecu(id: dict):
    j = 0
    t = 0
    can_adapter.can_read(id['id'])
    for _ in range(5):
        start_time = time.perf_counter()
        ans = can_adapter.can_read(id['id'])
        if not isinstance(ans, str):
            # for i in ans:
            #     print(hex(i), end=' ')
            # print()
            tim = time.perf_counter() - start_time
            # print('Time = ', tim)
            j += 1
            t += tim
    print('iter = ', j, ' avg time = ', t / j)


def loop_kvu(ite=10):
    at1 = 0
    at2 = 0
    at3 = 0
    it = 0
    on_off_kvu(False)
    time.sleep(1)

    for i in range(ite):
        t1, t2, t3 = on_off_kvu(bool(ite % 2))
        time.sleep(0.3)
        if t1 and t2 and t3:
            at1 += t1
            at2 += t2
            at3 += t3
            it += 1

    a = at1 / it
    print('Среднее время от бку до рейки = ', a)
    b = at2 / it
    print('Среднее время реакции рейки = ', b)
    c = at3 / it
    print('Среднее время от кву до бку = ', c)
    print('Суммарное среднее время от кву до кву = ', a + b + c)


def time_mov_resp(id: dict, val: int):

    data = [1,  bku_kvu_id['offset'] & 0xFF, (bku_kvu_id['offset'] & 0xFF00) >> 8,
            (bku_kvu_id['offset'] + val * bku_kvu_id['scale']) & 0xFF,
            ((bku_kvu_id['offset'] + val * bku_kvu_id['scale']) & 0xFF00) >> 8, 0, 0, 0]
    can_adapter.can_send(bku_kvu_id['id'], data, bku_kvu_id['bit'])
    start_time = time.perf_counter()
    p_time = time.perf_counter()
    send_delay = 0.1
    for t in range(10):
        ans = can_adapter.can_read(id['id'], bitrate=id['bit'])
        if time.perf_counter() > p_time + send_delay:
            p_time += send_delay
            can_adapter.can_send(bku_kvu_id['id'], data, bku_kvu_id['bit'])
        if not isinstance(ans, str):
            value = (ans[id['MSB']] << 8) + ans[id['LSB']]
            value = ctypes.c_int16(value).value
            print(hex(id['id']), hex(ans[id['MSB']]), hex(ans[id['LSB']]), value, (value - id['offset']) / id['scale'], val)
            for i in ans:
                print(hex(i), end=' ')
            print()
            # if value >= val * id['scale'] + id['offset']:
            #     print('Время когда получил нужный ответ', time.perf_counter() - start_time)
            #     return time.perf_counter() - start_time
    return False


def moving(pos=1):
    print(pos)
    time_mov_resp(kvu_burr_id, 0)
    bku_burr_time = time_mov_resp(kvu_burr_id, pos)

    burr_kvu_time = time_mov_resp(burr_kvu_id, pos)

    kvu_bku_time = time_mov_resp(kvu_bku_id, pos)

    print(f'{bku_burr_time=}, {burr_kvu_time=}, {kvu_bku_time=}')
    return bku_burr_time, burr_kvu_time, kvu_bku_time


if __name__ == '__main__':
    moving(10)
