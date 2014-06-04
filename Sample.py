__author__ = 'JLyon'

import PyLCDIP
import sys  # to check to see if we have any arguments for automatic running of the script
import socket  # to automatically detect the IP Address
import serial.tools.list_ports  # to list the serial ports for easier user selection and auto selection with the script
import threading  # to run the serial read input without blocking

lcd = PyLCDIP.CrystalLCD()


def send_custom():
    print "IMPORTANT: Make sure your message is less than 20 characters."
    ctext = raw_input("What message would you like to send?")
    lcd.write_text(ctext[:20]) # trim to 20 chars


def write_ip():
    #ip = socket.gethostbyname(socket.gethostname())
    ip = ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
    lcd.write_text(ip)


def is_int(value):
    try:
        val = int(value)
        return True
    except ValueError:
        return False


def calc_crc():
    rin = "X"
    inbytes = []
    while rin != "":
        rin = raw_input("Enter hex byte: ")
        if rin != "":
            b = int(rin, 16)  # base 16 is hex
            print "%#x added to array" % b
            inbytes.append(b)
        else:
            print "Completed input: ", rin
    crc = PyLCDIP.crc16(inbytes)


def read_serial():
    toread = lcd.ser.inWaiting()
    # print "Bytes waiting: ", toread
    if toread > 0:
        read = lcd.ser.read(toread)
        read = map(ord, read)
        print "Bytes read: ", map(hex,read)  # convert the ASCII byte (int) to a HEX string for display (0xFF)
        lcd.rxbuffer += read  # TODO should rxbuffer adjustments be thread locked?
        lcd.check_input(lcd.rxbuffer)


def listen_serial():
    while True:
        read_serial()

# if called with ANY parameter, just hit the first COM port, clear the screen, and write the IP
if len(sys.argv) > 1:
    lcd.port = serial.tools.list_ports.comports()[0][0]  # the first listed COM port's name
    lcd.open()
    lcd.clear_screen()
    write_ip()
else:
    print "The following COM ports are available: "
    ports = list(serial.tools.list_ports.comports())
    for i, port in enumerate(ports):
        print "%s. Port: %s" % (i + 1, port[0])
        print " > Description: ", port[1]
    res = raw_input("Which COM port would you like to open? ")
    if is_int(res[0]):
        port = ports[int(res[0]) - 1][0]
        lcd.port = port
        lcd.open()
    selection = "0"
    while selection != "x":
        print "======================"
        print "1. Clear Screen"
        print "2. Send Hello World!"
        print "3. Send custom text"
        print "4. Send Local IP"
        print "5. Read Serial"
        print "6. Listen to Serial"
        print ""
        print "0. CRC16 Calc"
        print "X. Exit"
        print ""
        selection = raw_input("Select an option: ")
        print "Selected %s" % selection
        if len(selection) > 0:
            selection == selection[0].lower()
        else:
            selection == "0"
        if selection == "1":
            lcd.clear_screen()
        elif selection == "2":
            lcd.write_text("Hello World!")
        elif selection == "3":
            send_custom()
        elif selection == "4":
            write_ip()
        elif selection == "5":
            read_serial()
        elif selection == "6":
            thread = threading.Thread(target=listen_serial())
            thread.start()  # run the listen serial on a background thread
        elif selection == "0":
            calc_crc()
    else:
        print "Exiting"
        #manually close the port?