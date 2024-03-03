
# import random
#
# from machine import Pin
#
# button_led_1 = Pin(10, Pin.OUT)
# button_led_2 = Pin(11, Pin.OUT)
# button_led_3 = Pin(12, Pin.OUT)
# button_led_4 = Pin(13, Pin.OUT)
#
# button_1 = Pin(6, Pin.IN, Pin.PULL_UP)
# button_2 = Pin(7, Pin.IN, Pin.PULL_UP)
# button_3 = Pin(8, Pin.IN, Pin.PULL_UP)
# button_4 = Pin(9, Pin.IN, Pin.PULL_UP)
#
# status_led = Pin(14, Pin.OUT)
#
# def all_buttons_value(v):
#     button_led_1.value(v)
#     button_led_2.value(v)
#     button_led_3.value(v)
#     button_led_4.value(v)
#
# def new_number():
#     num = random.randint(1, 4)
#     print(num)
#     return num
#
#
# num = new_number()
# while True:
#     status_led.value(0)
#
#     if num == 1:
#         all_buttons_value(0)
#         button_led_1.value(1)
#     elif num == 2:
#         all_buttons_value(0)
#         button_led_2.value(1)
#     elif num == 3:
#         all_buttons_value(0)
#         button_led_3.value(1)
#     elif num == 4:
#         all_buttons_value(0)
#         button_led_4.value(1)
#
#     if button_1.value() == 0:
#         if num == 1:
#             num = new_number()
#     elif button_2.value() == 0:
#         if num == 2:
#             num = new_number()
#     elif button_3.value() == 0:
#         if num == 3:
#             num = new_number()
#     elif button_4.value() == 0:
#         if num == 4:
#             num = new_number()


# from machine import Pin
#
# button_led_1 = Pin(10, Pin.OUT)
# button_led_2 = Pin(11, Pin.OUT)
# button_led_3 = Pin(12, Pin.OUT)
# button_led_4 = Pin(13, Pin.OUT)
#
# button_1 = Pin(6, Pin.IN, Pin.PULL_UP)
# button_2 = Pin(7, Pin.IN, Pin.PULL_UP)
# button_3 = Pin(8, Pin.IN, Pin.PULL_UP)
# button_4 = Pin(9, Pin.IN, Pin.PULL_UP)
#
# status_led = Pin(14, Pin.OUT)
#
# def all_buttons_value(v):
#     button_led_1.value(v)
#     button_led_2.value(v)
#     button_led_3.value(v)
#     button_led_4.value(v)
#
# any_pushed = 0
#
# while True:
#     status_led.value(0)
#     push_val = 1
#     not_push_val = 0
#
#     if button_1.value() == 0:
#         all_buttons_value(1)
#         any_pushed = 1
#     elif any_pushed == 0:
#         button_led_1.value(not_push_val)
#
#     if button_2.value() == 0:
#         all_buttons_value(1)
#         any_pushed = 1
#     else:
#         button_led_2.value(not_push_val)
#
#     if button_3.value() == 0:
#         all_buttons_value(1)
#         any_pushed = 1
#     else:
#         button_led_3.value(not_push_val)
#
#     if button_4.value() == 0:
#         all_buttons_value(1)
#         any_pushed = 1
#     else:
#         button_led_4.value(not_push_val)
#
#     if button_1.value() == 1 and button_2.value() == 1 and button_3.value() == 1 and button_4.value() == 1:
#         any_pushed = 0


# import time
# import utime
# import network
# #import uasyncio
# #import urequests as ur
# import _thread
# from machine import Pin, Timer
#
#
# class Button:
#     def __init__(self, pin, timeout=50):
#         self.pin = pin
#         self.timeout = timeout
#         self.debounce_timer = Timer(-1)
#         self.is_timeout = False
#         self.cur_value = pin.value()
#         self.last_value = self.value
#
#     def _start_debounce_timer(self):
#         self.debounce_timer.init(period=self.timeout, mode=Timer.ONE_SHOT,
#                                  callback=self._cancel_timeout)
#
#     def _cancel_timeout(self, _):
#         self.is_timeout = not self.is_timeout
#
#     def value(self):
#         self.cur_value = self.pin.value()
#
#         if self.cur_value == 0 and self.last_value != 0 and not self.is_timeout:
#             self.is_timeout = True
#             self._start_debounce_timer()
#             self.last_value = self.cur_value
#             return 0
#         elif self.cur_value == 1 and self.last_value != 1 and not self.is_timeout:
#             self.is_timeout = True
#             self._start_debounce_timer()
#             self.last_value = self.cur_value
#             return 1
#         else:
#             self.last_value = self.cur_value
#             return 1
#
#
# ssid = 'Chillplatz'
# password = 'Schillerstr42'
#
# global button_led_1, button_led_2, button_led_3, button_led_4
# global button_1
# global myQueue
#
# def connect_wifi():
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     wlan.connect(ssid, password)
#
#     # Wait for connect or fail
#     max_wait = 10
#     while max_wait > 0:
#         if wlan.status() < 0 or wlan.status() >= 3:
#             break
#         max_wait -= 1
#         print('waiting for connection...')
#         time.sleep(1)
#
#     # Handle connection error
#     if wlan.status() != 3:
#         raise RuntimeError('network connection failed')
#     else:
#         print('connected')
#         status = wlan.ifconfig()
#         print('ip = ' + status[0])
#
#
# def button_handler(pin: Pin):
#     if pin.value() == 1:
#         button_led_1.on()
#     else:
#         button_led_1.off()
#     print(f'button {pin} pressed')
#     utime.sleep_ms(200)
#
#
# def button_handler2(pin: Pin):
#     button_led_1.off()
#
#
# def setup():
#     global button_led_1, button_led_2, button_led_3, button_led_4
#     global button_1
#
#     button_led_1 = Pin(16, Pin.OUT)
#     button_led_2 = Pin(17, Pin.OUT)
#     button_led_3 = Pin(18, Pin.OUT)
#     button_led_4 = Pin(19, Pin.OUT)
#
#     button_1 = Button(Pin(15, Pin.IN, Pin.PULL_UP))
#
#
# def send_button_press(button):
#     r = ur.post(
#         "http://192.168.0.112:9898/api/button_press/new",
#         headers={'content-type': 'application/json'},
#         json={
#             "kiosk_id": 666,
#             "button": button
#         }
#     )
#     print(r.status_code)
#     r.close()
#
#
# def print_button_press():
#     global myQueue
#     while True:
#         if button_1.value() == 0:
#             myQueue.append(1)
#             print("button 1 pressed")
#
# def main():
#     connect_wifi()
#     setup()
#
#     global myQueue
#     myQueue = []
#     #_thread.start_new_thread(print_button_press, ())
#
#     # while True:
#     #     if len(myQueue) > 0:
#     #         item = myQueue.pop(0)
#     #         r = ur.post(
#     #             "http://192.168.0.112:9898/api/button_press/new",
#     #             headers={'content-type': 'application/json'},
#     #             json={
#     #                 "kiosk_id": 666,
#     #                 "button": item
#     #             }
#     #         )
#     #         print(r.status_code)
#     #         r.close()
#
#     while True:
#         if button_1.value() == 0:
#             send_button_press(1)
#             print("button 1 pressed")
#
# main()
# #uasyncio.run(main())



# # SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
# # SPDX-License-Identifier: MIT
#
# import time
# import urtc
# from machine import I2C, Pin
#
# # I2C = busio.I2C(board.GP5, board.GP4)
# # rtc = PCF8523(I2C)
# i2c = I2C(0, scl=Pin(5), sda=Pin(4))
# rtc = urtc.PCF8523(i2c)
#
# days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
#
# set_time = False
#
# if set_time:   # change to True if you want to write the time!
#     #                     year, mon, date, hour, min, sec, wday, yday, isdst
#     t = time.struct_time((2023,  3,   6,   10,  55,  00,    1,   -1,    -1))
#     # you must set year, mon, date, hour, min, sec and weekday
#     # yearday is not supported, isdst can be set but we don't do anything with it at this time
#
#     print("Setting time to:", t)     # uncomment for debugging
#     rtc.datetime = t
#     print()
#
# while True:
#     t = rtc.datetime()
#     print(t)     # uncomment for debugging
#     #print("The date is %s %d/%d/%d" % (days[t.weekday], t.month, t.day, t.year))
#     #print("The time is %d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec))
#
#     time.sleep(1) # wait a second


# # SPDX-FileCopyrightText: 2023 Liz Clark for Adafruit Industries
# #
# # SPDX-License-Identifier: MIT
# """CircuitPython PiCowbell Adalogger Example"""
# import time
# import machine
# import sdcard
# import uos
# import urtc
# from machine import I2C, Pin
#
# i2c = I2C(0, scl=Pin(5), sda=Pin(4))
# rtc = urtc.PCF8523(i2c)
#
# #  list of days to print to the text file on boot
# days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
#
# # Assign chip select (CS) pin (and start it high)
# cs = machine.Pin(17, machine.Pin.OUT)
# # Intialize SPI peripheral (start with 1 MHz)
# spi = machine.SPI(0,
#                   baudrate=1000000,
#                   polarity=0,
#                   phase=0,
#                   bits=8,
#                   firstbit=machine.SPI.MSB,
#                   sck=machine.Pin(18, machine.Pin.OUT),
#                   mosi=machine.Pin(19, machine.Pin.OUT),
#                   miso=machine.Pin(16, machine.Pin.OUT))
#
# # Initialize SD card
# sd = sdcard.SDCard(spi, cs)
# # Mount filesystem
# vfs = uos.VfsFat(sd)
# uos.mount(vfs, "/sd")
#
#
# set_clock = False
#
# if set_clock:
#     #                     year, mon, date, hour, min, sec, wday, yday, isdst
#     t = time.struct_time((2023,  3,   6,   00,  00,  00,    0,   -1,    -1))
#
#     print("Setting time to:", t)
#     rtc.datetime = t
#     print()
#
# #  variable to hold RTC datetime
# t = rtc.datetime()
#
# time.sleep(1)
#
# #  initial write to the SD card on startup
# try:
#     with open("/sd/temp.txt", "a") as f:
#         #  writes the date
#         f.write('The date is {} {}/{}/{}\n'.format(days[t.weekday], t.month, t.day, t.year))
#         #  writes the start time
#         f.write('Start time: {}:{}:{}\n'.format(t.hour, t.minute, t.second))
#         #  headers for data, comma-delimited
#         f.write('Temp,Time\n')
#         #  debug statement for REPL
#         print("initial write to SD card complete, starting to log")
# except ValueError:
#     print("initial write to SD card failed - check card")
#
# while True:
#     try:
#         #  variable for RTC datetime
#         t = rtc.datetime()
#         #  append SD card text file
#         with open("/sd/temp.txt", "a") as f:
#             #  write temp data followed by the time, comma-delimited
#             f.write('{},{}:{}:{}\n'.format(666, t.hour, t.minute, t.second))
#             print("data written to sd card")
#         #  repeat every 30 seconds
#         time.sleep(1)
#     except ValueError:
#         print("data error - cannot write to SD card")
#         time.sleep(10)




# Big Button: 2024 Colin Luoma
#
# License: GPL
"""Big Button"""
import _thread
import time
import machine
import network
import sdcard
import uos
import urtc
import urequests as ur
from machine import I2C, Pin, Timer

"""Button - handles debouncing and button led status"""
class Button:
    def __init__(self, pin, led_pin, timeout=50):
        self.pin = pin
        self.led_pin = led_pin
        self.timeout = timeout
        self.debounce_timer = Timer(-1)
        self.is_timeout = False
        self.cur_value = pin.value()
        self.last_value = self.value

    def _start_debounce_timer(self):
        self.debounce_timer.init(period=self.timeout, mode=Timer.ONE_SHOT,
                                 callback=self._cancel_timeout)

    def _cancel_timeout(self, _):
        self.is_timeout = not self.is_timeout

    def value(self):
        self.cur_value = self.pin.value()

        if self.cur_value == 0:
            self.led_pin.value(1)
        else:
            self.led_pin.value(0)

        if self.cur_value == 0 and self.last_value != 0 and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return 0
        elif self.cur_value == 1 and self.last_value != 1 and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return 1
        else:
            self.last_value = self.cur_value
            return 1

# button queue
global bq

# GPIO pin setup
button_led_1 = Pin(10, Pin.OUT)
button_led_2 = Pin(11, Pin.OUT)
button_led_3 = Pin(12, Pin.OUT)
button_led_4 = Pin(13, Pin.OUT)

button_1 = Button(Pin(6, Pin.IN, Pin.PULL_UP), button_led_1)
button_2 = Button(Pin(7, Pin.IN, Pin.PULL_UP), button_led_2)
button_3 = Button(Pin(8, Pin.IN, Pin.PULL_UP), button_led_3)
button_4 = Button(Pin(9, Pin.IN, Pin.PULL_UP), button_led_4)

# status led on back of box
status_led = Pin(14, Pin.OUT)
status_led.value(0)

# setup I2C and RTC
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
rtc = urtc.PCF8523(i2c)

# init SPI for SD Card reading
cs = machine.Pin(17, machine.Pin.OUT)
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18, machine.Pin.OUT),
                  mosi=machine.Pin(19, machine.Pin.OUT),
                  miso=machine.Pin(16, machine.Pin.OUT))

# init SD Card and mount fs
sd = sdcard.SDCard(spi, cs)
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")

def turn_off_status_led(t):
    status_led.value(0)
    t.deinit()

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connect or fail
    max_wait = 60
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status_led.value(1)
        led_flash = Timer(-1)
        led_flash.init(mode=Timer.ONE_SHOT, period=5000, callback=turn_off_status_led)
        status = wlan.ifconfig()
        print('ip = ' + status[0])

def set_rtc_from_api():
    try:
        r = ur.get(
            "http://bigbutton.cluoma.com/time",
            # "http://192.168.0.112:9898/api/time",
            headers={'accept': 'application/json'}
        )
        if r.status_code == 200:
            data = r.json()
            print(data)
            datetime = urtc.datetime_tuple(year=data['year'], month=data['month'], day=data['day'],
                                           hour=data['hour'], minute=data['minute'], second=data['second'])
            rtc.datetime(datetime)
        r.close()
    except:
        print("Failed to get time from server")

def append_press_to_queue(button):
    global bq
    t = rtc.datetime()
    timestamp = f"{t.year}-{t.month:02d}-{t.day:02d}T{t.hour:02d}:{t.minute:02d}:{t.second:02d}Z"
    bq.append({"button": button, "timestamp": timestamp})


def print_button_press():
    """"This function runs in a separate thread to read button presses"""
    global bq

    while True:
        if button_1.value() == 0:
            append_press_to_queue(1)
            print("button 1 pressed")
        if button_2.value() == 0:
            append_press_to_queue(2)
            print("button 2 pressed")
        if button_3.value() == 0:
            append_press_to_queue(3)
            print("button 3 pressed")
        if button_4.value() == 0:
            append_press_to_queue(4)
            print("button 4 pressed")


def sd_log_press(press):
    try:
        f_log = open("/sd/log2.txt", "a")
        print(f"Logging {press['button']},{press['timestamp']}")
        f_log.write('{},{}\n'.format(press['button'], press['timestamp']))
        f_log.close()
    except FileNotFoundError:
        print("Cannot open 'log2.txt'")

def server_log_press(press):
    try:
        r = ur.post(
            "http://bigbutton.cluoma.com/api/button_press/new",
            # "http://192.168.0.112:9898/api/button_press/new",
            headers={'content-type': 'application/json'},
            json=[{'kiosk_id': 666, 'button': press['button'], 'clientdate': press['timestamp']}]
        )
        print(r.status_code)
        r.close()
    except:
        print("Failed to send press to server")

def load_wifi_connection_details():
    # load wifi connection details from a file
    try:
        f = open("/sd/wifi.txt", "r")
        lines = f.readlines()
        file_ssid = lines[0].rstrip()
        file_password = lines[1].rstrip()
        f.close()
        return file_ssid, file_password
    except FileNotFoundError:
        print("Cannot open 'wifi.txt'")


## Start program

ssid, password = load_wifi_connection_details()
connect_wifi(ssid, password)
set_rtc_from_api()

bq = []
_thread.start_new_thread(print_button_press, ())

while True:
    if len(bq) > 0:
        item = bq.pop(0)
        sd_log_press(item)
        server_log_press(item)
