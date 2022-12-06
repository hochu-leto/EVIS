from time import sleep

from CANAdater import CANAdapter

can_adapter = CANAdapter()
t = 0

if __name__ == '__main__':
    if can_adapter.find_adapters():
        old_t = 0
        while t < 15:
            # sleep(2)
            ans = can_adapter.can_read(0x18F)
            if isinstance(ans, list):
                for a in ans:
                    print(t, buf_to_string(a), end='   ')
                    print()
            elif isinstance(ans, dict):
                for ti, a in ans.items():
                    print(str(t).zfill(2), (ti - old_t), buf_to_string(a), end='   ')
                    print()
                    old_t = ti
            t += 1
            sleep(0.02)

