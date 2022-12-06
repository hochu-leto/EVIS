
from CANAdater import CANAdapter

can_adapter = CANAdapter()
t = 0


def buf_to_string(buf):
    if isinstance(buf, str):
        return buf
    s = ''
    for i in buf:
        s += hex(i) + ' '
    return s


if can_adapter.find_adapters():
    while t < 15:
        ans = can_adapter.can_read(0x381)
        print(t, buf_to_string(ans))
        t += 1

