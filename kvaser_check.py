from canlib import canlib

ch = canlib.openChannel(channel=0, flags=canlib.Open.OVERRIDE_EXCLUSIVE, bitrate=canlib.Bitrate.BITRATE_250K)
ch.setBusOutputControl(canlib.Driver.NORMAL)
ch.busOn()
while True:
    try:
        frame = ch.read()
        print(frame.id, end='   ')
        for bit in frame.data:
            print(hex(bit), end=' ')
        print()
    except canlib.CanNoMsg as ex:
        pass
    except canlib.canError as ex:
        print(ex)