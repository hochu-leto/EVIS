import ctypes
import time

from CANAdater import CANAdapter

can_adapter = CANAdapter()
if not can_adapter.isDefined:
    can_adapter = CANAdapter()

bku_kvu_id = {'id': int('0x18FF51A5', 16), 'bit': 250, 'scale': 1, 'f_byte': 1}
kvu_bku_id = {'id': int('0x18FF34A1', 16), 'bit': 250, 'scale': 300, 'f_byte': 2}
kvu_burr_id = {'id': int('0x314', 16), 'bit': 125, 'scale': 10, 'f_byte': 1}
burr_kvu_id = {'id': int('0x18f', 16), 'bit': 125, 'scale': 10, 'f_byte': 1}


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
    start_time = time.perf_counter()
    for t in range(100):
        ans = can_adapter.can_read(id['id'], bitrate=id['bit'])
        if not isinstance(ans, str):
            value = ans[id['f_byte'] - 1] << 8 + ans[id['f_byte']]
            value = ctypes.c_int16(value).value
            if value >= val * id['scale']:
                print('Время когда получил нужный ответ', time.perf_counter() - start_time)
                return time.perf_counter() - start_time
    return False


def moving(pos: int):
    print(pos)
    can_adapter.can_send(bku_kvu_id['id'], [1, 0, 0, 0, 100 + pos, 0, 100, 0], bku_kvu_id['bit'])

    bku_burr_time = time_mov_resp(kvu_burr_id, pos)

    burr_kvu_time = time_mov_resp(burr_kvu_id, pos)

    kvu_bku_time = time_mov_resp(kvu_bku_id, pos)

    print(f'{bku_burr_time=}, {burr_kvu_time=}, {kvu_bku_time=}')
    return bku_burr_time, burr_kvu_time, kvu_bku_time


if __name__ == '__main__':
    loop_kvu()
    # read_ecu(burr_kvu_id)
