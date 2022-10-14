import time

from CANAdater import CANAdapter

can_adapter = CANAdapter()
if not can_adapter.isDefined:
    can_adapter = CANAdapter()

bku_kvu_id = int('0x18FF51A5', 16)
kvu_bku_id = int('0x18FF34A1', 16)
kvu_burr_id = int('0x314', 16)
burr_kvu_id = int('0x18f', 16)
kvu_on_mode_message = [1, 0, 0, 0, 0, 0, 0, 0]


def on_off_kvu(swich: bool):
    start_time = time.perf_counter()
    can_adapter.can_send(bku_kvu_id, [int(swich), 0, 0, 0, 0, 0, 0, 0], 250)
    while True:
        ans = can_adapter.can_read(kvu_burr_id)
        if not isinstance(ans, str):
            for i in ans:
                print(hex(i), end=' ')
            print()
            if ans[0] & int(swich):
                break
        pass
    bku_burr_time = time.perf_counter() - start_time
    while can_adapter.can_read(burr_kvu_id)[0] != int(swich):
        pass
    burr_kvu_time = time.perf_counter() - start_time

    while can_adapter.can_read(kvu_bku_id, 250)[0] != int(swich):
        pass
    kvu_bku_time = time.perf_counter() - start_time

    print(f'{bku_burr_time=}, {burr_kvu_time=}, {kvu_bku_time=}')


def read_kvu():
    j = 0
    t = 0
    for _ in range(20):
        start_time = time.perf_counter()
        ans = can_adapter.can_read(kvu_burr_id)
        if not isinstance(ans, str):
            for i in ans:
                print(hex(i), end=' ')
            print()
            tim = time.perf_counter() - start_time
            print('Time = ', tim)
            j += 1
            t += tim
    print('iter = ', j, ' avg time = ', tim / j)
