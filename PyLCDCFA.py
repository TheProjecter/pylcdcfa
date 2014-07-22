__author__ = 'Josh'

import serial  # to access the serial port
import threading  # to run the serial read input without blocking


class CrystalLCD(object):
    port = 0
    ser = serial.Serial()
    command = []
    rxbuffer = []
    debug = False

    def __init__(self, desired_port=None):
        if desired_port is not None:
            # set the desired port and open it
            self.port = desired_port
            self.open()
        else:
            # try to find a port with Crystalfontz in the name
            ports = list(serial.tools.list_ports.comports())
            selected = ""
            for i, port in enumerate(ports):
                if "Crystalfontz" in port[1]:
                    selected = port[0]
            if selected:
                self.port = selected
                self.open()


    def open(self):
        self.ser.close()
        self.ser.port = self.port
        self.ser.baudrate = 115200
        self.ser.open()

    def clear_screen(self):
        cmd = self.build_command(0x06)
        self.ser.write(cmd)

    def write_text(self, data, col=0, row=0):
        #command = 0x1F, length (3-22), col (0-19), row (0-3), data (1-22 char)
        command = [0x1F]
        if 22 > len(data) > 0:
            command.append(len(data) + 2)  # add in the col + row bytes
        else:
            raise Exception("Too much text!")

        # make sure the row and col parameters are in range
        if 19 >= row >= 0 and 3 >= col >= 0:
            command.append(col)
            command.append(row)
        else:
            raise Exception("Row and Col outside of range!")

        # append each of the characters
        for c in data:
            command.append(c)

        # calculate the CRC
        crc = crc16(command)
        #append the CRC in reverse order
        for c in crc[::-1]:
            command.append(c)

        # write the command to the serial port
        self.ser.write(command)

    def build_command(self, code, data=None):
        command = [code]
        if data is not None:
            command.append(len(data))
            command.append(data)
        else:
            command.append(0)
        crc = crc16(command)
        for c in crc[::-1]:
            command.append(c)
        return command


    def check_input(self, data):
        """Check the list of bytes for input"""
        # Format: Command, Size, Data[], CRC16[2]
        # if we don't have any remaining data or we don't have enough data for a full packet, let's stop
        if len(data) == 0 or len(data) < 5:
            return
        # if the data is in string format, convert it to int/byte
        if type(data[0]) is str:
            data = map(ord, data)
        # if the first byte is the Key Activity response command, let's parse it
        if data[0] == 0x80:
            size = data[1]  # should always be one with key presses
            keyin = data[2]
            print "Key In: ", keyin
            crc = data[3:5]  # this should really combine the two bytes
            if keyin == 1:
                print "KEY_UP_PRESS"
            elif keyin == 2:
                print "KEY_DOWN_PRESS"
            elif keyin == 3:
                print "KEY_LEFT_PRESS"
            elif keyin == 4:
                print "KEY_RIGHT_PRESS"
            elif keyin == 5:
                print "KEY_ENTER_PRESS"
            elif keyin == 6:
                print "KEY_EXIT_PRESS"
            elif keyin == 7:
                print "KEY_UP_RELEASE"
            elif keyin == 8:
                print "KEY_DOWN_RELEASE"
            elif keyin == 9:
                print "KEY_LEFT_RELEASE"
            elif keyin == 10:
                print "KEY_RIGHT_RELEASE"
            elif keyin == 11:
                print "KEY_ENTER_RELEASE"
            elif keyin == 12:
                print "KEY_EXIT_RELEASE"
            # remove the items we just worked on
            del data[0:5]
            self.check_input(data)

    def read_serial(self):
        toread = self.ser.inWaiting()
        # print "Bytes waiting: ", toread
        if toread > 0:
            read = self.ser.read(toread)
            read = map(ord, read)
            if self.debug:
                print "Bytes read: ", map(hex,read)  # convert the ASCII byte (int) to a HEX string for display (0xFF)
            self.rxbuffer += read  # TODO should rxbuffer adjustments be thread locked?
            self.check_input(self.rxbuffer)

# the following CRC table is from 635_packet.c, by crystalfontz
CRC_LOOKUP_TABLE = [0x00000, 0x01189, 0x02312, 0x0329B, 0x04624, 0x057AD, 0x06536, 0x074BF,
                    0x08C48, 0x09DC1, 0x0AF5A, 0x0BED3, 0x0CA6C, 0x0DBE5, 0x0E97E, 0x0F8F7,
                    0x01081, 0x00108, 0x03393, 0x0221A, 0x056A5, 0x0472C, 0x075B7, 0x0643E,
                    0x09CC9, 0x08D40, 0x0BFDB, 0x0AE52, 0x0DAED, 0x0CB64, 0x0F9FF, 0x0E876,
                    0x02102, 0x0308B, 0x00210, 0x01399, 0x06726, 0x076AF, 0x04434, 0x055BD,
                    0x0AD4A, 0x0BCC3, 0x08E58, 0x09FD1, 0x0EB6E, 0x0FAE7, 0x0C87C, 0x0D9F5,
                    0x03183, 0x0200A, 0x01291, 0x00318, 0x077A7, 0x0662E, 0x054B5, 0x0453C,
                    0x0BDCB, 0x0AC42, 0x09ED9, 0x08F50, 0x0FBEF, 0x0EA66, 0x0D8FD, 0x0C974,
                    0x04204, 0x0538D, 0x06116, 0x0709F, 0x00420, 0x015A9, 0x02732, 0x036BB,
                    0x0CE4C, 0x0DFC5, 0x0ED5E, 0x0FCD7, 0x08868, 0x099E1, 0x0AB7A, 0x0BAF3,
                    0x05285, 0x0430C, 0x07197, 0x0601E, 0x014A1, 0x00528, 0x037B3, 0x0263A,
                    0x0DECD, 0x0CF44, 0x0FDDF, 0x0EC56, 0x098E9, 0x08960, 0x0BBFB, 0x0AA72,
                    0x06306, 0x0728F, 0x04014, 0x0519D, 0x02522, 0x034AB, 0x00630, 0x017B9,
                    0x0EF4E, 0x0FEC7, 0x0CC5C, 0x0DDD5, 0x0A96A, 0x0B8E3, 0x08A78, 0x09BF1,
                    0x07387, 0x0620E, 0x05095, 0x0411C, 0x035A3, 0x0242A, 0x016B1, 0x00738,
                    0x0FFCF, 0x0EE46, 0x0DCDD, 0x0CD54, 0x0B9EB, 0x0A862, 0x09AF9, 0x08B70,
                    0x08408, 0x09581, 0x0A71A, 0x0B693, 0x0C22C, 0x0D3A5, 0x0E13E, 0x0F0B7,
                    0x00840, 0x019C9, 0x02B52, 0x03ADB, 0x04E64, 0x05FED, 0x06D76, 0x07CFF,
                    0x09489, 0x08500, 0x0B79B, 0x0A612, 0x0D2AD, 0x0C324, 0x0F1BF, 0x0E036,
                    0x018C1, 0x00948, 0x03BD3, 0x02A5A, 0x05EE5, 0x04F6C, 0x07DF7, 0x06C7E,
                    0x0A50A, 0x0B483, 0x08618, 0x09791, 0x0E32E, 0x0F2A7, 0x0C03C, 0x0D1B5,
                    0x02942, 0x038CB, 0x00A50, 0x01BD9, 0x06F66, 0x07EEF, 0x04C74, 0x05DFD,
                    0x0B58B, 0x0A402, 0x09699, 0x08710, 0x0F3AF, 0x0E226, 0x0D0BD, 0x0C134,
                    0x039C3, 0x0284A, 0x01AD1, 0x00B58, 0x07FE7, 0x06E6E, 0x05CF5, 0x04D7C,
                    0x0C60C, 0x0D785, 0x0E51E, 0x0F497, 0x08028, 0x091A1, 0x0A33A, 0x0B2B3,
                    0x04A44, 0x05BCD, 0x06956, 0x078DF, 0x00C60, 0x01DE9, 0x02F72, 0x03EFB,
                    0x0D68D, 0x0C704, 0x0F59F, 0x0E416, 0x090A9, 0x08120, 0x0B3BB, 0x0A232,
                    0x05AC5, 0x04B4C, 0x079D7, 0x0685E, 0x01CE1, 0x00D68, 0x03FF3, 0x02E7A,
                    0x0E70E, 0x0F687, 0x0C41C, 0x0D595, 0x0A12A, 0x0B0A3, 0x08238, 0x093B1,
                    0x06B46, 0x07ACF, 0x04854, 0x059DD, 0x02D62, 0x03CEB, 0x00E70, 0x01FF9,
                    0x0F78F, 0x0E606, 0x0D49D, 0x0C514, 0x0B1AB, 0x0A022, 0x092B9, 0x08330,
                    0x07BC7, 0x06A4E, 0x058D5, 0x0495C, 0x03DE3, 0x02C6A, 0x01EF1, 0x00F78]


def dump(n):
    s = '%x' % n
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')
    #print repr(Dump(1245427))  #: '\x13\x00\xf3'


def crc16(data, seed=0xFFFF):  # 0x0FFFF
    for item in data:
        # print "Type: %s | Data: %s" % (type(item), item)
        if type(item) != int:
            for c in item:
                c = ord(c)
                seed = (seed >> 8) ^ CRC_LOOKUP_TABLE[(seed ^ c) & 0xff]
        else:
            seed = (seed >> 8) ^ CRC_LOOKUP_TABLE[(seed ^ item) & 0xff]
    # print "Pre-CRC: %#x" % seed
    mask = 0xFFFF  # (1 << seed.bit_length()) - 1  #Shifts exactly the number of bits, not full bytes
    # print "Mask: ", bin(mask), hex(mask)
    seed = seed ^ mask
    # print "CRC: %#x" % seed
    return dump(seed)










""" Linux Only Code - dependent on LCDUI
from lcdui.devices import CrystalFontz
device = CrystalFontz.CFA635Display(2)
device.ClearScreen()
device.WriteData("Hello World!", row=0, col=0)
"""
