import time

from CANAdater import CANAdapter

can_adapter = CANAdapter()
if not can_adapter.isDefined:
    can_adapter = CANAdapter()

bku_kvu_id = {'id': int('0x18FF51A5', 16), 'bit': 250}
kvu_bku_id = {'id': int('0x18FF34A1', 16), 'bit': 250}
kvu_burr_id = {'id': int('0x314', 16), 'bit': 125}
burr_kvu_id = {'id': int('0x18f', 16), 'bit': 125}


def on_off_kvu(swich: bool):
    print(swich)
    can_adapter.can_send(bku_kvu_id['id'], [int(swich), 0, 0, 0, 0, 0, 0, 0], bku_kvu_id['bit'])

    bku_burr_time = time_resp(bku_kvu_id, swich)

    burr_kvu_time = time_resp(burr_kvu_id, swich)

    kvu_bku_time = time_resp(kvu_bku_id, swich)

    print(f'{bku_burr_time=}, {burr_kvu_time=}, {kvu_bku_time=}')
    return bku_burr_time, burr_kvu_time, kvu_bku_time


def time_resp(id: dict, sw: bool):
    start_time = time.perf_counter()
    t = 0
    while t < 10:
        ans = can_adapter.can_read(id['id'], bitrate=id['bit'])
        if not isinstance(ans, str):
            print(hex(id['id']), end='   ')
            for i in ans:
                print(hex(i), end=' ')
            print()
            if ans[0] & 0x01 == int(sw):
                break
        t += 1
    return time.perf_counter() - start_time


def read_kvu():
    j = 0
    t = 0
    for _ in range(20):
        start_time = time.perf_counter()
        ans = can_adapter.can_read(kvu_burr_id[0])
        if not isinstance(ans, str):
            for i in ans:
                print(hex(i), end=' ')
            print()
            tim = time.perf_counter() - start_time
            print('Time = ', tim)
            j += 1
            t += tim
    print('iter = ', j, ' avg time = ', tim / j)


def loop_kvu(ite=10):
    at1 = 0
    at2 = 0
    at3 = 0
    on_off_kvu(False)
    for i in range(ite):
        t1, t2, t3 = on_off_kvu(True)
        time.sleep(1)
        on_off_kvu(False)
        time.sleep(2)
        at1 += t1
        at2 += t2
        at3 += t3

    a = at1 / ite
    print('Среднее время от бку до рейки = ', a)
    b = at2 / ite
    print('Среднее время реакции рейки = ', b)
    c = at3 / ite
    print('Среднее время от кву до бку = ', c)


if __name__ == '__main__':
    loop_kvu()
