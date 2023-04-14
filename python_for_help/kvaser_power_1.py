import can
from can import CanInterfaceNotImplementedError


new_adapter = can.Bus(channel=0, interface='kvaser', bitrate=250000)
# for msg in new_adapter:
# while True:
msg = new_adapter.recv(1)
print(msg)
# quit()

device_list = can.detect_available_configs()
adapters_list = []
for b in device_list:
    try:
        can_bus = can.Bus(channel=b['channel'], interface=b['interface'])
        if 'Virtual' not in can_bus.channel_info:
            adapters_list.append(b)
            print(f'Find Hardware adapter {can_bus.channel_info}')
    except CanInterfaceNotImplementedError as ex:
        print(f'Adapter {b["interface"]} FAULT ====>>>>   {ex.__str__()}')

bit_list = [125000, 250000, 500000]
checked_adapters = []
for b in adapters_list:
    print(b['interface'], b['channel'], end=' ')
    for bit in bit_list:
        print(bit, end=' ==> ')
        # new_adapter = can.Bus(channel=b['channel'], interface=b['interface'], bitrate=bit)
        new_adapter = can.Bus(channel=0, interface='kvaser', bitrate=250000)
        msg = new_adapter.recv(1)
        if isinstance(msg, can.Message):
            print(msg, end=' ; ')
            if not msg.is_error_frame:
                checked_adapters.append(new_adapter)
                break

new_adapter = can.Bus(channel=0, interface='kvaser', bitrate=250000)
msg = new_adapter.recv(1)
if isinstance(msg, can.Message):
    print(msg, end=' ; ')
    if not msg.is_error_frame:
        checked_adapters.append(new_adapter)

if checked_adapters:
    while KeyboardInterrupt:
        for adapter in checked_adapters:
            for msg in adapter:
                print(msg)
