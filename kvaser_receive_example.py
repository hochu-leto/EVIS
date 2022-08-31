from time import sleep

from canlib import canlib, Frame
from canlib.canlib import ChannelData

def setUpChannel(channel=0,
                 openFlags=canlib.Open.ACCEPT_VIRTUAL,
                 # openFlags=canlib.Open.NOFLAG,
                 # openFlags=canlib.Open.EXCLUSIVE,
                 outputControl=canlib.Driver.NORMAL):
    for i in range(10):
        chdata = 0
        while chdata == 0:
            canlib.reinitializeLibrary()
            try:
                chdata = canlib.ChannelData(channel).card_serial_no
            except canlib.canError as ex:
                   print(ex)
            print(canlib.getNumberOfChannels(), chdata)

        try:
            ch = canlib.openChannel(channel, openFlags, bitrate=canlib.Bitrate.BITRATE_125K)
            print("Using channel: %s, EAN: %s" % (ChannelData(channel).channel_name,
                                                  ChannelData(channel).card_upc_no))
            ch.setBusOutputControl(outputControl)
            ch.busOn()
            return ch
        except canlib.canError as ex:
            print(f'Ошибка при открытии канала = {ex}')
            try:
                canlib.Channel(channel).busOff()
                canlib.Channel(channel).close()
            except canlib.canError as ex:
                print(f'Ошибка при закрытии канала = {ex}')

def tearDownChannel(ch):
    ch.busOff()
    ch.close()


print("canlib version:", canlib.dllversion())
num_channels = canlib.getNumberOfChannels()
print("Found %d channels" % num_channels)
for channel in range(0, num_channels):
    chdata = canlib.ChannelData(channel)
    print("%d. %s (%s / %s)" % (
        channel,
        chdata.channel_name,
        chdata.card_upc_no,
        chdata.card_serial_no)
    )

ch0 = setUpChannel(channel=0)

while True:
    # chdata = canlib.ChannelData(0)
    # print(f'Channel s/n = {chdata.card_serial_no}')
    while not isinstance(ch0, canlib.Channel):
        ch0 = setUpChannel(channel=0)

    try:
        frame = ch0.read()
        print(frame)
        # break
    except (canlib.canNoMsg) as ex:
        # print('canNoMsg')
        pass
    except (canlib.canError) as ex:
        print(ex)
        ch0 = setUpChannel(channel=0)
    except (canlib.CanNotFound) as ex:
        print('CanNotFound')
    except KeyboardInterrupt:
        print("Stop.")
        break

tearDownChannel(ch0)
